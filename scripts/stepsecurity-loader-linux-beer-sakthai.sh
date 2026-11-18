#!/bin/bash
#
# StepSecurity Device Agent Loader for Linux
#
# This is a lightweight loader that fetches the latest dev-machine-guard binary
# version info from the StepSecurity API, downloads the binary from GitHub
# releases, verifies its integrity using both SHA256 checksum and an SSH-style
# Ed25519 signature (verified via `ssh-keygen -Y verify`), writes configuration,
# and delegates execution to the binary.
#
# Deploy this once via MDM — binary updates are delivered automatically.
#
# Template placeholders (replaced server-side when served from dashboard):
#   beer-sakthai, https://agent.api.stepsecurity.io, step_a62d578a-eea3-448f-bff7-d27dd6da39a8, ,
#   15, ,
#
# The install directory is hardcoded at the top of this script as
# INSTALL_DIR_CONFIG (defaults to $HOME/.stepsecurity). Customers who
# need a different location edit that assignment before running. The
# value is persisted to config.json so the agent picks it up on every
# subsequent run.
#
# ===== Compatibility =====
#
# This loader targets standard Linux distributions. It requires:
#   * bash 4+               (script will not start otherwise)
#   * systemd               (systemctl --user is used to schedule scans)
#   * getent                (glibc or musl)
#   * sha256sum, curl
#   * ssh-keygen 8.1+       (for `ssh-keygen -Y verify` — Ed25519 release
#                            signature verification; ships with OpenSSH 8.1,
#                            present on Fedora 32+, Ubuntu 20.04+, RHEL 9+,
#                            Debian 11+. The script aborts before touching
#                            any binary if this is missing.)
#
# If any of these are missing, the script exits early with a pointer to
# support. Distributions without systemd (e.g. Alpine, Void, NixOS, Gentoo
# with OpenRC) are not currently supported.
#
# If installation fails, please contact support@stepsecurity.io with the
# output of this script.
#

set -euo pipefail

# MDM and cron runs often get PATH=/usr/bin:/bin, without the sbin dirs that
# hold runuser.
PATH="${PATH:+$PATH:}/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export PATH

# Proxy settings for the agent the loader runs as the user: sudo resets the
# environment, and on a proxy-only network the agent can't reach the backend
# without them.
PROXY_ENV=()
for _proxy_var in http_proxy https_proxy no_proxy all_proxy HTTP_PROXY HTTPS_PROXY NO_PROXY ALL_PROXY; do
    if [ -n "${!_proxy_var:-}" ]; then PROXY_ENV+=("$_proxy_var=${!_proxy_var}"); fi
done

# The scheduled runs start with only what the scheduler definition sets, so
# it carries these proxy settings too (one line per set variable, none when
# unset). A proxy URL can hold credentials (user:pass@host): then the
# definition is written owner-only.
proxy_has_credentials() {
    local e
    for e in ${PROXY_ENV[@]+"${PROXY_ENV[@]}"}; do
        case "${e#*=}" in *@*) return 0 ;; esac
    done
    return 1
}

# Environment= lines for the systemd unit (quoted; \, " and % escaped).
systemd_proxy_env() {
    local e
    for e in ${PROXY_ENV[@]+"${PROXY_ENV[@]}"}; do
        case "$e" in *[[:cntrl:]]*) continue ;; esac
        printf 'Environment="%s"\n' "$(printf '%s' "$e" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/%/%%/g')"
    done
}

# ===== Embedded Configuration (replaced server-side) =====
CUSTOMER_ID="${STEP_SECURITY_CUSTOMER_ID:-beer-sakthai}"
API_ENDPOINT="${STEP_SECURITY_API_ENDPOINT:-https://agent.api.stepsecurity.io}"
API_KEY="${STEP_SECURITY_API_KEY:-step_a62d578a-eea3-448f-bff7-d27dd6da39a8}"
SCAN_FREQUENCY_HOURS=""
SCAN_FREQUENCY_MINUTES="15"
# Install directory — leave empty to default to $USER_HOME/.stepsecurity,
# resolved below right after the logged-in user is detected. Set an absolute
# path here to install somewhere other than the user's home. We deliberately
# don't reference $HOME at this point: MDM audit/install runs (Kandji, Jamf,
# Intune) execute scripts with a sanitized environment that doesn't set HOME,
# and under `set -u` "$HOME" would abort the script before our user
# resolution can run. The agent reads this back from the `install_dir` field
# that write_config persists into config.json.
INSTALL_DIR_CONFIG=""

# ===== Scan configuration (replaced server-side from the install wizard) =====
# Persisted verbatim into config.json by write_config and consumed by the
# binary. Each is left empty unless a value was chosen in the dashboard install
# wizard; empty means "omit the field and let the binary's built-in default
# apply". Customers deploying the raw loader can also set these by hand.
#
#   SEARCH_DIRS_JSON      JSON array of absolute dirs to scan, e.g.
#                         ["/home/me/code","/opt/work"]. Empty scans $HOME.
#   INCLUDE_TCC_PROTECTED "true"/"false"/"" — macOS-only knob; inert on Linux.
#   ENABLE_*_SCAN         "true"/"false"/"" — toggle npm / Homebrew / Python
#                         package-manager scans.
SEARCH_DIRS_JSON=''
INCLUDE_TCC_PROTECTED=""
ENABLE_NPM_SCAN="true"
ENABLE_BREW_SCAN="true"
ENABLE_PYTHON_SCAN="true"
# Optional device_id template, persisted into config.json by write_config and
# resolved by the binary on every run. Empty = the hardware serial (default).
# A literal value, or the tokens {serial} {hostname}; e.g. "{hostname}" keeps
# a rebuilt pooled desktop's history. The device is the machine: every user
# of a shared machine reports under the same id. A STEPSEC_DEVICE_ID
# environment variable wins over the template.
DEVICE_ID_TEMPLATE="-"
# "true"/"false"/"": have the binary's `uninstall` retire the device in the
# dashboard (persisted as retire_on_uninstall in config.json).
RETIRE_ON_UNINSTALL="false"
# DEVICE_TAG: dashboard label (host pool, team); the dashboard's retirement
# scope can select devices by it. Written to config.json as device_tag.
DEVICE_TAG=""

# ===== Update policy override (replaced server-side from the install wizard) =====
# Optional per-script OVERRIDE of the agent auto-update policy:
#   UPDATE_LAG_BEHIND      install N versions behind the newest release (1-5)
#   UPDATE_COOLDOWN_HOURS  skip versions published less than N hours ago (1-720)
# When set, the loader sends these to the API on every update check and the
# API resolves the version with them in place of the organization-wide policy
# (the script override wins). Empty or unreplaced = no override; the
# organization policy configured in the dashboard Settings page applies.
UPDATE_LAG_BEHIND=""
UPDATE_COOLDOWN_HOURS=""

# ===== Version pin (replaced server-side for version-pinned scripts) =====
# A pinned script installs exactly this version, verified against the
# checksum baked in when the script was generated, and never asks the API
# for the latest release. Empty = track the latest release.
PINNED_VERSION=""
PINNED_CHECKSUM_AMD64=""
PINNED_CHECKSUM_ARM64=""
case "$PINNED_VERSION" in *"{{"*) PINNED_VERSION="" ;; esac

# Maximum elapsed runtime, in whole hours, for a prior
# stepsecurity-dev-machine-guard process before the loader SIGKILLs it
# on the next tick. Defends against the alive-but-hung case that the
# binary's lock.Acquire (which only handles dead PIDs) cannot recover
# from on its own. Customers who want a stricter or looser threshold
# edit this value before deploy. 0 disables the sweeper entirely.
MAX_PROCESS_AGE_HOURS=5

# Hard wall on a single send-telemetry invocation, in whole hours.
# Written into config.json by write_config (max_execution_duration); the
# binary arms an internal watchdog that SIGTERMs (then hard-kills) itself if
# the run lasts longer. Delivered via config.json (not an env var) so it also
# reaches systemd-timer-fired runs that invoke the binary directly. Sits ABOVE
# STEPSEC_MAX_SCAN_DURATION (60min default inside the binary) so the scan trips
# first and partial telemetry can still upload. 0 disables the watchdog.
MAX_EXECUTION_DURATION_HOURS=4

# ===== SSH Public Key for Signature Verification =====
# Verifies authenticity of the binary checksum via `ssh-keygen -Y verify`.
# Must be the public-key half of the keypair used by the release operator
# (paste the contents of mdm-signing-key.pub here, including the type prefix
# and trailing comment, e.g. "ssh-ed25519 AAAA... releases@stepsecurity.io").
PUBLIC_KEY_SSH="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILN+WG4lOH/x6MysYOf1oY0PKXLLu9d3ZvQDcvq5Cboi releases@stepsecurity.io"

# ===== Constants =====
BINARY_NAME="stepsecurity-dev-machine-guard"
GITHUB_RELEASE_BASE="https://github.com/step-security/dev-machine-guard/releases/download"

# Public S3 mirror, used as a fallback when the github.com download fails
# (network block, corporate proxy, EDR rule, outage). The agent-api
# server-templates this value when serving the script. To pin the install to
# this mirror exclusively, delete the GITHUB_RELEASE_BASE branch in
# download_binary() below.
PACKAGES_BASE_URL="https://packages.stepsecurity.io/dev-machine-guard"

# Signature scope. Bound into the SSH signature at sign time; verification
# refuses signatures generated for any other namespace, which prevents reuse
# of a signature produced for a different StepSecurity artifact.
SIGNATURE_NAMESPACE="stepsecurity-mdm-checksum"
SIGNATURE_IDENTITY="releases@stepsecurity.io"

# Network bounds. Every curl is time-limited so a stalled proxy or half-open
# connection can't hold an MDM run open indefinitely.
CURL_CONNECT_TIMEOUT_SECONDS=20
API_MAX_TIME_SECONDS=60
DOWNLOAD_MAX_TIME_SECONDS=600
API_FETCH_ATTEMPTS=3

# Runtime variables (set by fetch_latest_version)
BINARY_VERSION=""
BINARY_CHECKSUM=""

# Execution ID for run-status reporting. Lazily populated on first failure
# via uuidgen — happy-path runs never generate one (the binary owns its own
# lifecycle once handed off).
EXECUTION_ID=""

#==============================================================================
# UTILITY FUNCTIONS
#==============================================================================

# _emit_log writes a formatted log line to stderr and, when LOADER_LOG_FILE is
# set (just before the command dispatch below), also appends it to that file.
# The dev-machine-guard binary folds this run's loader output from .loader_log
# into its run-status logs and then deletes it (see seedLoaderLog), so it works
# even on an admin/MDM install where stderr isn't scheduler-redirected.
# Under root the lines go to a private buffer instead (see flush_loader_log).
_emit_log() {
    echo "$1" >&2
    if [ -n "${LOADER_LOG_FILE:-}" ]; then
        printf '%s\n' "$1" 2>/dev/null >> "${LOADER_LOG_BUFFER:-$LOADER_LOG_FILE}" || true
    fi
}

print_info() {
    _emit_log "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

print_error() {
    _emit_log "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*"
}

print_success() {
    _emit_log "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

#==============================================================================
# ARCHITECTURE DETECTION
#==============================================================================

# Resolve goreleaser arch suffix. The Linux release artifacts are named
# "stepsecurity-dev-machine-guard-<version>-linux_<arch>" (see .goreleaser.yml
# in dev-machine-guard) — one file per arch, no universal binary.
case "$(uname -m)" in
    x86_64)         ARCH="amd64" ;;
    aarch64|arm64)  ARCH="arm64" ;;
    *)
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Unsupported architecture: $(uname -m)" >&2
        exit 1
        ;;
esac

#==============================================================================
# DISTRO COMPATIBILITY CHECK
#==============================================================================

# Hard requirements: systemd (for periodic scheduling) and getent (for home
# directory resolution). Bail out early with a pointer to support rather than
# letting the user discover the problem mid-install. See the "Compatibility"
# section in the file header for the full list of supported distros.
_unsupported() {
    local missing="$1"
    local ts
    ts=$(date '+%Y-%m-%d %H:%M:%S')
    {
        echo "[${ts}] ERROR: required tool '${missing}' was not found on this system."
        echo "[${ts}] ERROR: The StepSecurity Device Agent for Linux requires bash, systemd,"
        echo "[${ts}] ERROR: getent, sha256sum, and curl. Distributions without systemd are"
        echo "[${ts}] ERROR: not currently supported."
        echo "[${ts}] ERROR: For help, please contact support@stepsecurity.io with this output."
    } >&2
    exit 1
}

command -v systemctl &>/dev/null || _unsupported "systemctl"
command -v getent     &>/dev/null || _unsupported "getent"
command -v sha256sum  &>/dev/null || _unsupported "sha256sum"

#==============================================================================
# TOOL AVAILABILITY CHECKS
#==============================================================================

CURL_AVAILABLE=false
command -v curl &>/dev/null && CURL_AVAILABLE=true

# `ssh-keygen -Y verify` was added in OpenSSH 8.1 (2019). Modern Linux distros
# (Fedora 32+, Ubuntu 20.04+, RHEL 9+, Debian 11+) all ship 8.1 or newer.
# Probe by invoking `ssh-keygen -Y verify` with no args and looking for its
# specific argument-validation error, which is only emitted when the
# subcommand is recognized.
SSH_KEYGEN_AVAILABLE=false
if command -v ssh-keygen &>/dev/null; then
    _ssh_keygen_probe=$(ssh-keygen -Y verify 2>&1 || true)
    if [[ "$_ssh_keygen_probe" == *"Too few arguments for verify"* ]] \
        || [[ "$_ssh_keygen_probe" == *"missing namespace"* ]]; then
        SSH_KEYGEN_AVAILABLE=true
    fi
    unset _ssh_keygen_probe
fi

#==============================================================================
# JSON / EXECUTION HELPERS
#==============================================================================

json_escape() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    s="$(echo "$s" | tr -d '\000-\037')"
    echo "$s"
}

# Map common curl exit codes to a human-readable reason so download failures
# carry a useful signal in telemetry instead of a generic "download_failed".
curl_exit_reason() {
    case "$1" in
        5)  echo "failed to resolve proxy" ;;
        6)  echo "DNS resolution failed" ;;
        7)  echo "failed to connect to host" ;;
        22) echo "HTTP error response (4xx/5xx)" ;;
        28) echo "operation timed out" ;;
        35) echo "SSL/TLS connect error" ;;
        52) echo "empty reply from server" ;;
        56) echo "failure receiving network data" ;;
        60) echo "SSL certificate problem" ;;
        *)  echo "curl error" ;;
    esac
}

# net_error_code maps a curl exit code (plus curl's message, for exit 22) to a
# stable cause code. The Windows loader and the agent (dev-machine-guard
# internal/telemetry/neterr.go) emit the same set, so failures group by cause
# on every platform: net_dns, net_proxy, net_connect, net_timeout, net_tls,
# net_cert, net_conn_dropped, http_4xx, http_5xx, net_other.
net_error_code() {
    # A proxy refusing CONNECT surfaces as exit 22 (curl 8) or 56 (older curl);
    # without this it reads as the API rejecting the request.
    case "${2:-}" in
        *"error: 407"*|*"from proxy after CONNECT"*|*"CONNECT tunnel failed"*)
            echo "net_proxy"
            return 0
            ;;
    esac
    case "$1" in
        5)        echo "net_proxy" ;;
        6)        echo "net_dns" ;;
        7)        echo "net_connect" ;;
        28)       echo "net_timeout" ;;
        35)       echo "net_tls" ;;
        51|60|77) echo "net_cert" ;;
        52|55|56) echo "net_conn_dropped" ;;
        22)
            case "${2:-}" in
                *"error: 4"*) echo "http_4xx" ;;
                *"error: 5"*) echo "http_5xx" ;;
                *)            echo "net_other" ;;
            esac
            ;;
        *)        echo "net_other" ;;
    esac
}

# curl reads the Authorization header from this config on stdin (-K -) so the
# API key never appears on argv, where ps and EDR process telemetry see it.
curl_auth_config() {
    printf 'header = "Authorization: Bearer %s"\n' "$(printf '%s' "$API_KEY" | sed 's/[\\"]/\\&/g')"
}

# api_get_with_retry runs a curl GET against the API (request args in "$@"),
# retrying transport errors and 5xx. Sets API_RESPONSE on success, or
# API_FETCH_ERROR with the curl reason on failure. Uses globals rather than
# stdout so the retry notices can still print_info.
api_get_with_retry() {
    API_RESPONSE=""
    API_FETCH_ERROR=""
    local attempt=1 output curl_exit code
    while [ "$attempt" -le "$API_FETCH_ATTEMPTS" ]; do
        curl_exit=0
        # With -sS, $output is the body on success and curl's error on failure.
        output=$(curl_auth_config | curl -sS -f -K - \
            --connect-timeout "$CURL_CONNECT_TIMEOUT_SECONDS" \
            --max-time "$API_MAX_TIME_SECONDS" \
            "$@" 2>&1) || curl_exit=$?
        if [ "$curl_exit" -eq 0 ]; then
            API_RESPONSE="$output"
            return 0
        fi
        code=$(net_error_code "$curl_exit" "$output")
        API_FETCH_ERROR="[${code}] $(curl_exit_reason "$curl_exit") (curl exit ${curl_exit}, attempt ${attempt}/${API_FETCH_ATTEMPTS}): ${output}"
        # A 4xx (bad key, unknown tenant) won't change on retry.
        if [ "$code" = "http_4xx" ]; then
            return 1
        fi
        if [ "$attempt" -lt "$API_FETCH_ATTEMPTS" ]; then
            print_info "Latest-binary request failed: ${API_FETCH_ERROR}; retrying in $((attempt * 5))s..."
            sleep $((attempt * 5))
        fi
        attempt=$((attempt + 1))
    done
    return 1
}

get_execution_id() {
    if [ -z "$EXECUTION_ID" ]; then
        if command -v uuidgen &>/dev/null; then
            # Don't let pipefail in this helper kill the parent script.
            EXECUTION_ID=$(uuidgen 2>/dev/null | tr 'A-Z' 'a-z' 2>/dev/null) || EXECUTION_ID=""
        fi
        # Minimal images ship no uuidgen (uuid-runtime); the kernel has one.
        if [ -z "$EXECUTION_ID" ] && [ -r /proc/sys/kernel/random/uuid ]; then
            EXECUTION_ID=$(cat /proc/sys/kernel/random/uuid 2>/dev/null) || EXECUTION_ID=""
        fi
        if [ -z "$EXECUTION_ID" ]; then
            EXECUTION_ID=$(printf 'fallback-%s-%s-%s' "$(date +%s)" "$$" "$RANDOM" 2>/dev/null) || EXECUTION_ID="fallback-unknown"
        fi
    fi
    echo "$EXECUTION_ID"
}

# device_id an admin configured (configure / hand edit). write_config carries
# it across rewrites and failure reports use it, matching the agent, where a
# configured ID wins over the hardware serial. Only plain values are kept.
configured_device_id() {
    local f id
    for f in "${CONFIG_FILE:-}" "${LEGACY_CONFIG_FILE:-}"; do
        [ -n "$f" ] && [ -r "$f" ] && [ ! -L "$f" ] || continue
        id=$(sed -n 's/.*"device_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$f" 2>/dev/null | head -n 1)
        id=$(printf '%s' "$id" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
        [ -n "$id" ] || continue
        case "$id" in *\\*|*[![:print:]]*) continue ;; esac
        [ ${#id} -le 200 ] || continue
        echo "$id"
        return 0
    done
    return 0
}

# ===== Device identity resolution (mirrors dev-machine-guard internal/device) =====
# The binary reports under the machine identity unless a configured identity
# (the STEPSEC_DEVICE_ID environment variable, else the device_id template the
# wizard baked in or an admin wrote to config.json) says otherwise. The loader
# resolves the SAME id, so the run-status rows it posts on its own land on the
# device the binary reports as and never on a literal "{hostname}".
# Self-contained (no script-level state) so the functions also work when
# lifted out of the script on their own, as the loader tests do.

# sanitize_device_id ID: the binary's SanitizeDeviceID. Bytes outside
# [A-Za-z0-9._~-] become '-', runs of '-' collapse, leading and trailing '-'
# and '.' are trimmed, and an id over 128 bytes keeps its first 115 bytes plus
# 12 hex digits of its sha256 so it stays unique and readable.
sanitize_device_id() {
    local s hex
    s=$(printf '%s' "${1:-}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' \
        | LC_ALL=C sed -e 's/[^A-Za-z0-9._~-]/-/g' -e 's/--*/-/g' -e 's/^[-.]*//' -e 's/[-.]*$//')
    if [ ${#s} -gt 128 ]; then
        hex=$(printf '%s' "$s" | { sha256sum 2>/dev/null || shasum -a 256 2>/dev/null || openssl dgst -sha256 2>/dev/null; } \
            | sed -e 's/^.*= //' | awk '{print $1}' | cut -c1-12)
        s=$(printf '%s' "${s:0:115}" | sed -e 's/[-.]*$//')"-${hex}"
    fi
    printf '%s\n' "$s"
}

# resolve_device_id TEMPLATE SERIAL HOSTNAME: the binary's identity
# resolution. An empty template is the machine identity, bytes untouched. A
# literal without tokens is used exactly as given. Tokens ({serial} {hostname},
# case-insensitive) are expanded and the result sanitized; any other token,
# the {user} of an older template included, falls back to the machine
# identity: the device is the machine, whoever is signed in.
resolve_device_id() {
    local t serial="${2:-}" host rest tok out=""
    t=$(printf '%s' "${1:-}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
    if [ -z "$t" ]; then printf '%s\n' "$serial"; return 0; fi
    case "$t" in *\{*) ;; *) printf '%s\n' "$t"; return 0 ;; esac
    host=$(printf '%s' "${3:-}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' | tr '[:upper:]' '[:lower:]')
    rest="$t"
    while :; do
        case "$rest" in *\{*\}*) ;; *) break ;; esac
        rest="${rest#*\{}"
        tok=$(printf '%s' "${rest%%\}*}" | tr '[:upper:]' '[:lower:]')
        rest="${rest#*\}}"
        case "$tok" in
            serial) if [ -z "$serial" ] || [ "$serial" = "unknown" ]; then echo ""; return 0; fi ;;
            hostname)
                # No usable host name: fall back to the machine identity, as the binary does.
                case "$host" in ""|unknown|localhost|localhost.localdomain) host="$serial" ;; esac
                if [ -z "$host" ] || [ "$host" = "unknown" ]; then echo ""; return 0; fi ;;
            *) printf '%s\n' "$serial"; return 0 ;;
        esac
    done
    rest="$t"
    while :; do
        case "$rest" in *\{*\}*) ;; *) out="${out}${rest}"; break ;; esac
        out="${out}${rest%%\{*}"
        rest="${rest#*\{}"
        tok=$(printf '%s' "${rest%%\}*}" | tr '[:upper:]' '[:lower:]')
        rest="${rest#*\}}"
        case "$tok" in
            serial) out="${out}${serial}" ;;
            hostname) out="${out}${host}" ;;
        esac
    done
    out=$(sanitize_device_id "$out")
    if [ -z "$out" ]; then printf '%s\n' "$serial"; return 0; fi
    printf '%s\n' "$out"
}

# loader_hostname: what os.Hostname gives the binary.
loader_hostname() {
    local h
    h=$(hostname 2>/dev/null || cat /proc/sys/kernel/hostname 2>/dev/null || true)
    printf '%s\n' "$h"
}

# Mirror the binary's device identifier resolution
# (dev-machine-guard internal/device/device.go getSerialNumberLinux):
#   1. /sys/class/dmi/id/product_serial — readable without root on most distros
#   2. dmidecode -s system-serial-number — needs root
#   3. /etc/machine-id — always available, unique per install
# Keeping loader and binary on the same partition key means failure rows
# correlate with the binary's own run-status rows for the same device.
# Leading/trailing whitespace only, like the binary's strings.TrimSpace;
# serials with inner spaces must match it byte for byte.
_trim() {
    sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' | head -n 1
}

# get_device_id: the id the binary will report under. Precedence as in the
# binary: STEPSEC_DEVICE_ID, the wizard template, a device_id already in
# config.json, then the machine identity. A {user} token (an older template)
# names no identity any more: it resolves to the machine identity, with a
# warning in the loader log.
# agent_device_id: the id the installed binary resolves for the target user
# (identity --json), the authority on the id. Prints the id; prints nothing,
# still succeeding, when an older binary says its template cannot be
# completed in this context (a {user} template with nobody to name), which
# the caller takes as "no beacon". Fails when the binary is absent or does
# not answer, and the loader computes its own answer instead.
agent_device_id() {
    [ -n "${BINARY_PATH:-}" ] && [ -x "$BINARY_PATH" ] || return 1
    local out
    out=$(_run_as_user "$BINARY_PATH" identity --json 2>/dev/null) || return 1
    if printf '%s' "$out" | grep -Eq '"incomplete"[[:space:]]*:[[:space:]]*true'; then
        return 0
    fi
    local id
    id=$(printf '%s' "$out" | sed -n 's/.*"device_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)
    [ -n "$id" ] || return 1
    printf '%s\n' "$id"
}

get_device_id() {
    local agent
    if agent=$(agent_device_id); then
        printf '%s\n' "$agent"
        return 0
    fi
    local template="${STEPSEC_DEVICE_ID:-${DEVICE_ID_TEMPLATE:-}}"
    if [ "$template" = "-" ]; then
        template=""   # explicit reset: the machine identity, no fallback
    else
        [ -n "$template" ] || template=$(configured_device_id)
    fi
    case "$(printf '%s' "$template" | tr '[:upper:]' '[:lower:]')" in
        *"{user}"*)
            # Self-contained like its neighbours: the logger is absent when the
            # functions are lifted out of the script.
            if command -v print_info >/dev/null 2>&1; then
                print_info "WARNING: device_id template '${template}' uses {user}, which is no longer an identity token; reporting under the machine identity"
            fi ;;
    esac
    local serial
    serial=$(loader_machine_identity)
    resolve_device_id "$template" "$serial" "$(loader_hostname)"
}

# loader_machine_identity: the machine identity the binary falls back to when
# nothing is configured: the machine-wide id a privileged run saved, else the
# hardware serial the agent's user can read, else machine-id.
loader_machine_identity() {
    local id

    # The agent prefers the machine-wide ID a privileged run saved.
    if [ -f /etc/stepsecurity/device-id ] && [ ! -L /etc/stepsecurity/device-id ]; then
        id=$(_trim </etc/stepsecurity/device-id 2>/dev/null || true)
        if [ -n "$id" ] && [ "$id" != "unknown" ]; then
            echo "$id"; return
        fi
    fi

    # Otherwise resolve it as the agent will. When it runs as the logged-in
    # user, product_serial (root-only) and dmidecode are out of reach, so it
    # reports machine-id unless the serial is readable to that user.
    if [ "$(id -u)" -eq 0 ]; then
        if [ -n "${USER_UID:-}" ]; then
            id=$(_run_as_user cat /sys/class/dmi/id/product_serial 2>/dev/null | _trim || true)
        elif [ -n "$(find /sys/class/dmi/id/product_serial -perm -0004 2>/dev/null)" ]; then
            # No target user: the unprivileged agent reads the serial only
            # when it is world-readable.
            id=$(_trim </sys/class/dmi/id/product_serial 2>/dev/null || true)
        else
            id=""
        fi
        if [ -n "$id" ] && [ "$id" != "None" ] && [ "$id" != "To Be Filled By O.E.M." ]; then
            echo "$id"; return
        fi
        if [ -r /etc/machine-id ]; then
            id=$(tr -d '[:space:]' </etc/machine-id 2>/dev/null || true)
            if [ -n "$id" ]; then
                echo "$id"; return
            fi
        fi
        echo "unknown"; return
    fi

    if [ -r /sys/class/dmi/id/product_serial ]; then
        id=$(_trim </sys/class/dmi/id/product_serial 2>/dev/null || true)
        if [ -n "$id" ] && [ "$id" != "None" ] && [ "$id" != "To Be Filled By O.E.M." ]; then
            echo "$id"; return
        fi
    fi

    if command -v dmidecode &>/dev/null; then
        id=$(dmidecode -s system-serial-number 2>/dev/null | _trim || true)
        if [ -n "$id" ] && [ "$id" != "None" ] && [ "$id" != "To Be Filled By O.E.M." ]; then
            echo "$id"; return
        fi
    fi

    if [ -r /etc/machine-id ]; then
        id=$(tr -d '[:space:]' </etc/machine-id 2>/dev/null || true)
        if [ -n "$id" ]; then
            echo "$id"; return
        fi
    fi

    echo "unknown"
}

# Posts a "failed" run-status row to /developer-mdm-agent/telemetry/run-status.
# Mirrors the binary's run-status reporter on the macOS loader: 2 attempts,
# 500ms backoff, 3s per request, 2xx and 4xx terminal, 5xx and transport
# errors retry. Always best-effort — never blocks or fails the calling code.
report_run_status_failed() {
    local error_type="$1"
    local message="$2"
    local error_message="${error_type}: ${message}"

    # Match runStatusMaxErrorChars on the binary side.
    if [ ${#error_message} -gt 2000 ]; then
        error_message="${error_message:0:2000}"
    fi

    local exec_id
    exec_id=$(get_execution_id)
    local device_id
    device_id=$(get_device_id)
    # An older binary with a {user} template and no developer to name skips
    # such runs, so the loader posts nothing rather than inventing a device.
    [ -n "$device_id" ] || return 0
    local agent_version="loader-${BINARY_VERSION:-unknown}"

    local payload
    payload=$(printf '{"execution_id":"%s","device_id":"%s","status":"failed","agent_version":"%s","platform":"linux","error_message":"%s"}' \
        "$exec_id" "$device_id" "$agent_version" "$(json_escape "$error_message")")

    local endpoint="${API_ENDPOINT}/v1/${CUSTOMER_ID}/developer-mdm-agent/telemetry/run-status"

    local attempt http_code
    for attempt in 1 2; do
        if [ "$attempt" -gt 1 ]; then sleep 0.5; fi
        http_code=$(curl_auth_config | curl -s -o /dev/null -w '%{http_code}' -X POST -K - \
            --max-time 3 \
            -H "Content-Type: application/json" \
            -H "X-Agent-Version: ${agent_version}" \
            -d "$payload" \
            "$endpoint" 2>/dev/null) || http_code="000"
        case "$http_code" in
            2*|4*) return 0 ;;
        esac
    done
    return 0
}

cleanup() {
    if [ -n "${TEMP_DIR:-}" ] && [ -d "${TEMP_DIR:-}" ]; then
        rm -rf "$TEMP_DIR"
    fi
    if [ -n "${DOWNLOAD_TEMP:-}" ]; then
        rm -f "$DOWNLOAD_TEMP"
    fi
    if [ -n "${LOADER_LOG_BUFFER:-}" ]; then
        flush_loader_log
        rm -f "$LOADER_LOG_BUFFER"
    fi
}

trap cleanup EXIT

#==============================================================================
# RESOLVE TARGET USER AND HOME DIRECTORY
#==============================================================================

# Accounts an agent can belong to: UID_MIN (login.defs) and up, not nobody.
# Display-manager greeters (gdm, Debian-gdm, sddm, lightdm) are system accounts.
is_regular_user() {
    local uid min
    uid=$(id -u "$1" 2>/dev/null) || return 1
    min=$(awk '$1 == "UID_MIN" {print $2; exit}' /etc/login.defs 2>/dev/null || true)
    case "$min" in ''|*[!0-9]*) min=1000 ;; esac
    case "$uid" in ''|*[!0-9]*) return 1 ;; esac
    [ "$uid" -ge "$min" ] && [ "$uid" -ne 65534 ]
}

# The account to install for. A non-root run (a periodic tick) serves only
# itself. As root: the user at the machine's seat, else the account that ran
# sudo (an Ansible become account only when no one sits at the seat), else
# the first regular user with a session, $USER, or who.
get_target_user() {
    local user s
    if [ "$(id -u)" -ne 0 ]; then
        id -un; return 0
    fi

    if command -v loginctl &>/dev/null; then
        s=$(loginctl show-seat seat0 -p ActiveSession 2>/dev/null | sed 's/^[^=]*=//' || true)
        if [ -n "$s" ]; then
            user=$(loginctl show-session "$s" -p Name 2>/dev/null | sed 's/^[^=]*=//' || true)
            if [ -n "$user" ] && is_regular_user "$user"; then echo "$user"; return 0; fi
        fi
    fi

    if [ -n "${SUDO_USER:-}" ] && is_regular_user "$SUDO_USER"; then
        echo "$SUDO_USER"; return 0
    fi

    if command -v loginctl &>/dev/null; then
        # `loginctl list-sessions --no-legend` columns: SESSION UID USER SEAT TTY
        while read -r _ _ user _; do
            if [ -n "$user" ] && is_regular_user "$user"; then echo "$user"; return 0; fi
        done < <(loginctl list-sessions --no-legend 2>/dev/null || true)
    fi

    if [ -n "${USER:-}" ] && is_regular_user "$USER"; then
        echo "$USER"; return 0
    fi

    if command -v who &>/dev/null; then
        for user in $(who 2>/dev/null | awk '{print $1}' || true); do
            if is_regular_user "$user"; then echo "$user"; return 0; fi
        done
    fi

    return 1
}

# MDMs pass arguments their own way — Jamf, for example, passes the mount point
# as "$1" and custom script parameters starting at "$4" — so we never assume
# "$1" is our command. Scan every argument for a recognized verb and otherwise
# fall back to the default action baked in at generation time. Unknown/extra
# arguments are ignored rather than fatal, so the script runs cleanly under any
# MDM (this is what made Jamf's "$1=/" abort with "Unknown command: /").
COMMAND="send-telemetry"
for _arg in "$@"; do
    case "$_arg" in
        install | --install | uninstall | --uninstall | send-telemetry | --send-telemetry | run | help | --help | -h)
            COMMAND="$_arg"
            break
            ;;
    esac
done

TEMP_DIR=""
INSTALL_DIR_TEMPLATE="$INSTALL_DIR_CONFIG"
# Match dev-machine-guard internal/systemd/systemd.go: same unit name so a
# previous binary-installed pair gets cleanly replaced.
SYSTEMD_UNIT_NAME="stepsecurity-dev-machine-guard"

# Point the per-user globals and paths at user $1 with home $2.
set_user_context() {
    LOGGED_IN_USER="$1"
    USER_HOME="$2"
    USER_UID=$(id -u "$LOGGED_IN_USER" 2>/dev/null || echo "")

    # Export HOME so the Go binary's os.UserHomeDir() finds the correct config
    export HOME="$USER_HOME"

    # Default INSTALL_DIR_CONFIG once we have a resolved user home. Skipped when
    # the operator pinned an absolute path at the top of the file.
    INSTALL_DIR_CONFIG="${INSTALL_DIR_TEMPLATE:-$USER_HOME/.stepsecurity}"

    # ===== Paths =====
    INSTALL_DIR="$INSTALL_DIR_CONFIG/bin"
    BINARY_PATH="$INSTALL_DIR/$BINARY_NAME"
    # CONFIG_DIR stays at the legacy bootstrap location ($USER_HOME/.stepsecurity)
    # regardless of INSTALL_DIR_CONFIG — the agent reads config.json from a
    # fixed path at startup, before it can know about a custom install_dir
    # (which it then loads from inside the file).
    CONFIG_DIR="$USER_HOME/.stepsecurity"
    CONFIG_FILE="$CONFIG_DIR/config.json"
    VERSION_FILE="$INSTALL_DIR_CONFIG/.current_version"

    # Loader script + systemd units live next to the binary so periodic timer
    # fires can re-invoke this script (auto-update on every tick) instead of
    # bypassing it by running the binary directly.
    LOADER_SCRIPT_NAME="stepsecurity-loader.sh"
    LOADER_SCRIPT_PATH="$INSTALL_DIR/$LOADER_SCRIPT_NAME"

    SYSTEMD_UNIT_DIR="$USER_HOME/.config/systemd/user"
    SYSTEMD_SERVICE_PATH="$SYSTEMD_UNIT_DIR/${SYSTEMD_UNIT_NAME}.service"
    SYSTEMD_TIMER_PATH="$SYSTEMD_UNIT_DIR/${SYSTEMD_UNIT_NAME}.timer"
    LOG_DIR="$INSTALL_DIR_CONFIG"
}

# no_user_exit <message>: report and stop, except for uninstall, which then
# tears down every account with an install (headless hosts, cron).
no_user_exit() {
    case "$COMMAND" in
        uninstall|--uninstall) LOGGED_IN_USER=""; return 0 ;;
    esac
    print_error "$1"
    report_run_status_failed "no_user" "$1"
    exit 1
}

LOGGED_IN_USER=$(get_target_user || true)
USER_HOME=""

if [ -z "$LOGGED_IN_USER" ]; then
    no_user_exit "No non-root user found for installation"
else
    USER_HOME=$(getent passwd "$LOGGED_IN_USER" 2>/dev/null | cut -d: -f6)
    if [ -z "$USER_HOME" ] || [ ! -d "$USER_HOME" ]; then
        no_user_exit "Home directory not found for user: $LOGGED_IN_USER"
    fi
fi
if [ -n "$LOGGED_IN_USER" ]; then
    set_user_context "$LOGGED_IN_USER" "$USER_HOME"
fi

#==============================================================================
# PRIVILEGE-AWARE FILE OWNERSHIP / SYSTEMCTL HELPERS
#==============================================================================

# Run a command as $LOGGED_IN_USER with the user-bus env vars set. Used both
# for `systemctl --user` calls from the loader itself and for invoking the
# binary so its internal `systemctl --user` (internal/systemd/systemd.go) can
# reach the user's systemd manager. Without XDG_RUNTIME_DIR, daemon-reload
# fails with "Failed to connect to user scope bus via local transport".
_run_as_user() {
    if [ "$(id -u)" -eq 0 ] && [ -n "${USER_UID:-}" ]; then
        if command -v runuser &>/dev/null; then
            runuser -u "$LOGGED_IN_USER" -- env \
                HOME="$USER_HOME" \
                XDG_RUNTIME_DIR="/run/user/${USER_UID}" \
                DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${USER_UID}/bus" \
                ${PROXY_ENV[@]+"${PROXY_ENV[@]}"} \
                "$@"
        else
            # Fallback: sudo. Some minimal Linux distros lack runuser.
            sudo -u "$LOGGED_IN_USER" \
                HOME="$USER_HOME" \
                XDG_RUNTIME_DIR="/run/user/${USER_UID}" \
                DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${USER_UID}/bus" \
                ${PROXY_ENV[@]+"${PROXY_ENV[@]}"} \
                "$@"
        fi
    else
        "$@"
    fi
}

run_systemctl_user() {
    _run_as_user systemctl --user "$@"
}

# Write stdin to a file in the user's tree. A root run must never write
# through a path the user controls (a symlink planted at config.json would
# turn the write into a root file clobber), so the write runs as the user,
# into a temp file renamed over the target: rename replaces a planted
# symlink instead of following it, and the result is user-owned.
write_user_file() {
    _run_as_user /bin/sh -c 'umask 077; t=$(mktemp "$1.XXXXXX") || exit 1
if cat > "$t" && chmod "$2" "$t" && mv -f "$t" "$1"; then exit 0; fi
rm -f "$t"; exit 1' sh "$1" "$2"
}

# Copy the root run's buffered loader log into place (as the user).
flush_loader_log() {
    [ -n "${LOADER_LOG_BUFFER:-}" ] && [ -n "${LOADER_LOG_FILE:-}" ] || return 0
    write_user_file "$LOADER_LOG_FILE" 644 < "$LOADER_LOG_BUFFER" >/dev/null 2>&1 || true
}

# The binary consumes .loader_log when it starts: flush it, then stop logging
# to it so a later flush can't resurrect this run's lines.
handoff_loader_log() {
    flush_loader_log
    LOADER_LOG_FILE=""
}

# The execution-watchdog limit is delivered via config.json (see write_config),
# not an env var, so it reaches systemd-timer-fired runs that bypass the loader.
run_binary_as_user() {
    _run_as_user "$BINARY_PATH" "$@"
}

# argv[0] of PID with its whitespace intact (`ps args` joins argv with spaces,
# so an agent under "/opt/Device Guard/bin" can't be split back out of it;
# `ps comm` is truncated to 15 chars). /proc/PID/cmdline is readable for any
# account's processes; empty for kernel threads. Fails when PID isn't running.
proc_exe() {
    local exe=""
    [ -r "/proc/$1/cmdline" ] || return 1
    IFS= read -r -d '' exe < "/proc/$1/cmdline" || true
    printf '%s\n' "$exe"
}

# PIDs of running agents (any account, not this loader): argv[0]'s basename
# is exactly $BINARY_NAME, so a sibling such as the -task launcher, or a
# process merely naming the agent in its arguments, is not one.
is_agent_pid() {
    local exe
    exe=$(proc_exe "$1") || return 1
    [ "${exe##*/}" = "$BINARY_NAME" ]
}

agent_pids() {
    local pid rest
    ps -eo pid=,args= 2>/dev/null | while read -r pid rest; do
        [ "$pid" != "$$" ] || continue
        case "$rest" in *"$BINARY_NAME"*) ;; *) continue ;; esac
        if is_agent_pid "$pid"; then echo "$pid"; fi
    done || true
}

# Kill prior stepsecurity-dev-machine-guard processes whose elapsed
# runtime exceeds MAX_PROCESS_AGE_HOURS. See the macOS sibling loader
# for the rationale; the awk parser is identical (etime is portable
# across macOS and Linux ps).
kill_stale_dmg_processes() {
    local hours="${MAX_PROCESS_AGE_HOURS:-2}"
    if ! [[ "$hours" =~ ^[0-9]+$ ]] || [ "$hours" -le 0 ]; then
        return 0
    fi
    local max_seconds=$((hours * 3600))
    local self="$$"
    ps -eo pid,etime,command 2>/dev/null \
      | awk -v self="$self" -v max="$max_seconds" -v name="$BINARY_NAME" '
        NR == 1 { next }
        {
            pid = $1; etime = $2
            if (pid == self) next
            # Candidates only; is_agent_pid below checks argv[0] exactly.
            if (!index($0, name)) next
            d = 0; h = 0; m = 0; s = 0
            n = split(etime, a, "-")
            if (n == 2) { d = a[1]; rest = a[2] } else { rest = a[1] }
            n2 = split(rest, b, ":")
            if (n2 == 3) { h = b[1]; m = b[2]; s = b[3] }
            else         { m = b[1]; s = b[2] }
            secs = d*86400 + h*3600 + m*60 + s
            if (secs > max) print pid" "secs
        }' \
      | while read -r pid age; do
            is_agent_pid "$pid" || continue
            # SIGKILL cannot reap a process wedged in uninterruptible wait
            # (macOS "U", Linux "D"): the kernel holds it until its blocking
            # syscall returns. Attempting the kill is futile and re-logging it
            # on every tick is noise, so skip such processes — let the OS reap
            # them when the wait clears (or on reboot). A transiently-U process
            # (brief I/O) is simply swept on a later tick once it is back in a
            # killable state.
            # Gone since the listing: nothing to kill.
            st=$(ps -o stat= -p "$pid" 2>/dev/null | awk 'NR==1{print substr($1,1,1)}') || continue
            case "$st" in
                U|D) continue ;;
            esac
            print_info "kill_stale_dmg: SIGKILL PID ${pid} (age=${age}s, threshold=${max_seconds}s)"
            kill -KILL "$pid" 2>/dev/null || true
        done || true
    return 0
}

# Remove the binary's instance lock when its PID isn't a running agent.
# lock.Acquire treats any live PID as the holder, so a recycled (or planted)
# PID blocks every run. A lock this run can't read (left by a root run) is
# left alone; only root can clear that one. Agents >= 1.18.0 use an OS lock at
# a different path, so binary-scheduled runs (which skip this) don't need it.
remove_stale_instance_lock() {
    local lock="/tmp/stepsecurity-dev-machine-guard.lock" pid holder
    [ -f "$lock" ] && [ ! -L "$lock" ] && [ -r "$lock" ] || return 0
    pid=$(head -c 32 "$lock" 2>/dev/null | tr -cd '0-9' || true)
    [ -n "$pid" ] || return 0
    if holder=$(proc_exe "$pid"); then
        [ "${holder##*/}" != "$BINARY_NAME" ] || return 0
    elif ps -p "$pid" >/dev/null 2>&1; then
        # Running, but its identity can't be read: keep the lock.
        return 0
    fi
    print_info "Removing stale instance lock (PID ${pid}: ${holder:-not running})"
    rm -f "$lock" 2>/dev/null || true
    return 0
}

# SIGKILL (an MDM timeout) skips the EXIT trap: remove the temp files such
# runs left, the download buffer and log buffer in TMPDIR and the staging
# files write_user_file creates in the install tree. TMPDIR files carry the
# PID of the run that made them and go as soon as it is gone; anything else
# once older than an hour, so a concurrent run's files are never touched.
sweep_stale_temp_files() {
    local f p
    for f in "${TMPDIR:-/tmp}/${BINARY_NAME}".*.?????? "${TMPDIR:-/tmp}"/stepsecurity-loader-log.*.??????; do
        [ -f "$f" ] && [ -O "$f" ] || continue
        p=${f%.??????}; p=${p##*.}
        case "$p" in ''|*[!0-9]*) continue ;; esac
        [ "$p" = "$$" ] || kill -0 "$p" 2>/dev/null || rm -f "$f" 2>/dev/null || true
    done
    find "${TMPDIR:-/tmp}/" -maxdepth 1 -type f -user "$(id -un)" -mmin +60 \
        \( -name "${BINARY_NAME}.??????" -o -name 'stepsecurity-loader-log.??????' \
        -o -name "${BINARY_NAME}.*.??????" -o -name 'stepsecurity-loader-log.*.??????' \) \
        -exec rm -f {} + 2>/dev/null || true
    [ -n "${LOGGED_IN_USER:-}" ] && [ -d "${INSTALL_DIR_CONFIG:-}" ] || return 0
    _run_as_user find "$INSTALL_DIR_CONFIG" "${LEGACY_CONFIG_DIR:-$INSTALL_DIR_CONFIG}" -maxdepth 2 -type f -mmin +60 \
        \( -name "${BINARY_NAME}.??????" -o -name 'config.json.??????' -o -name '.loader_log.??????' \
        -o -name '.current_version.??????' -o -name 'stepsecurity-loader.sh.??????' \) \
        -exec rm -f {} + 2>/dev/null || true
}

# A scan in progress (an overlapping MDM run, a scheduler fire) holds the
# agent's instance lock, and an agent that loses the lock exits 1. The device
# is being scanned, so that is not a failure of this run.
agent_scan_running() {
    local pid args
    for pid in $(agent_pids); do
        args=$(ps -o args= -p "$pid" 2>/dev/null) || continue
        case "$args" in *" send-telemetry"*) return 0 ;; esac
    done
    return 1
}

# Run the scan and exit with its status, mapping "another scan holds the
# lock" to 0.
run_scan() {
    if agent_scan_running; then
        print_info "A scan is already in progress; skipping this run"
        exit 0
    fi
    local rc=0
    run_binary_as_user send-telemetry || rc=$?
    if [ "$rc" -ne 0 ] && agent_scan_running; then
        print_info "Agent exited ${rc} while another scan holds the instance lock; that scan covers this run"
        exit 0
    fi
    # 126/127: the agent never started, so it reported nothing itself.
    if [ "$rc" -eq 126 ] || [ "$rc" -eq 127 ]; then
        print_error "Agent failed to start (exit ${rc})"
        report_run_status_failed "agent_start_failed" "${BINARY_PATH} failed to start (exit ${rc}); $(ls -ln "$BINARY_PATH" 2>&1)"
    fi
    exit "$rc"
}

# A matching checksum proves the bytes, not that the scan can start them: a
# lost exec bit, a copy the user can't run (wrong owner), a noexec mount or
# quarantine fail every run while the checksum keeps matching. Run it the way
# the scan does.
binary_runnable() {
    local out rc=0
    out=$(run_binary_as_user --version 2>&1 </dev/null) || rc=$?
    [ "$rc" -eq 0 ] && return 0
    BINARY_RUN_ERROR="exit ${rc}: $(printf '%s\n' "$out" | head -1); $(ls -ln "$BINARY_PATH" 2>&1)"
    return 1
}

# Scheduled-run variant of ensure_binary. When the update fails (API or
# download outage, blocked GitHub; each is already reported) but a
# previously verified binary is installed, scan with that one instead of
# skipping the run.
ensure_binary_or_installed() {
    ensure_binary && return 0
    binary_runnable || return 1
    print_info "Update failed; running the installed binary"
    return 0
}

#==============================================================================
# SIGNATURE VERIFICATION
#==============================================================================

# Verify the SSH-style Ed25519 signature of the checksum via `ssh-keygen -Y
# verify`, ensuring the checksum was produced by the release operator and has
# not been tampered with.
# Why releases can't be verified here, for the log and the console: -Y verify
# needs OpenSSH 8.1+ (RHEL/Rocky/Alma 8 ship 8.0, Amazon Linux 2 7.4, Debian
# 10 7.9). Nothing unverified is ever installed; an installed agent keeps
# running (ensure_binary_or_installed).
ssh_keygen_diag() {
    local found="no OpenSSH client"
    if command -v ssh &>/dev/null; then
        found=$(ssh -V 2>&1 | head -1 || true)
    fi
    echo "ssh-keygen -Y verify (OpenSSH 8.1 or newer) is required to verify agent releases; found: ${found}. Install OpenSSH 8.1+, or use a version-pinned install script (checked against checksums in the script, no ssh-keygen needed)."
}

verify_checksum_signature() {
    local checksum_content="$1"
    local signature_base64="$2"

    if [ "$SSH_KEYGEN_AVAILABLE" != "true" ]; then
        local diag
        diag=$(ssh_keygen_diag)
        print_error "$diag"
        report_run_status_failed "ssh_keygen_unavailable" "$diag"
        return 1
    fi

    if [ "$PUBLIC_KEY_SSH" = "REPLACE_WITH_ACTUAL_PUBLIC_KEY" ] || [ -z "$PUBLIC_KEY_SSH" ]; then
        print_error "SSH public key is not configured"
        report_run_status_failed "public_key_not_configured" "SSH public key not configured for signature verification"
        return 1
    fi

    TEMP_DIR=$(mktemp -d)

    # allowed_signers file format expected by `ssh-keygen -Y verify`:
    #   <identity> [namespaces="<csv>"] <pubkey-line>
    # The value of `namespaces` MUST be double-quoted; ssh-keygen's option
    # parser rejects unquoted values. Pinning namespaces here means a
    # signature produced for a different namespace by the same key won't
    # validate.
    printf '%s namespaces="%s" %s\n' \
        "$SIGNATURE_IDENTITY" "$SIGNATURE_NAMESPACE" "$PUBLIC_KEY_SSH" \
        > "$TEMP_DIR/allowed_signers"

    # Decode the base64 envelope back to the multi-line SSH signature blob.
    # Linux `base64 -d` is the standard form (no `-D` like macOS).
    echo "$signature_base64" | base64 -d > "$TEMP_DIR/checksum.sig" 2>/dev/null || true

    if [ ! -s "$TEMP_DIR/checksum.sig" ]; then
        print_error "Failed to base64-decode signed_checksum"
        report_run_status_failed "signature_decode_failed" "Failed to base64-decode signed_checksum for v${BINARY_VERSION}"
        return 1
    fi

    # `ssh-keygen -Y verify` reads the verified message from stdin and exits 0
    # only if the signature, namespace, and identity all match.
    if printf '%s' "$checksum_content" | ssh-keygen -Y verify \
        -f "$TEMP_DIR/allowed_signers" \
        -I "$SIGNATURE_IDENTITY" \
        -n "$SIGNATURE_NAMESPACE" \
        -s "$TEMP_DIR/checksum.sig" >/dev/null 2>&1; then
        return 0
    fi

    report_run_status_failed "signature_verification_failed" "Checksum signature verification failed for v${BINARY_VERSION}"
    return 1
}

#==============================================================================
# SCRIPT-BAKED UPDATE POLICY (lag-behind / cooldown override)
#==============================================================================

# sanitize_policy_int: echo $1 if it is a plain non-negative integer, else 0.
# Covers empty values, unreplaced "{{...}}" template literals, and hand-edit
# garbage. MUST run before any numeric test on these knobs — under `set -e`
# an arithmetic [ -gt ] on a non-numeric value would kill the whole tick.
sanitize_policy_int() {
    if [[ "${1:-}" =~ ^[0-9]+$ ]]; then
        printf '%s' "$1"
    else
        printf '0'
    fi
}

# policy_query_string: echo the latest-binary query-string suffix carrying the
# script's baked update-policy override, or nothing when no override is set.
# The API applies these values in place of the organization policy (the script
# override wins); loaders without an override send no params. Values are
# sanitized digits, so no URL-encoding is needed. Pure function: stdout is the
# return channel, so nothing in here may print_info.
policy_query_string() {
    local lag cooldown
    lag=$(sanitize_policy_int "$UPDATE_LAG_BEHIND")
    cooldown=$(sanitize_policy_int "$UPDATE_COOLDOWN_HOURS")
    if [ "$lag" -gt 0 ] || [ "$cooldown" -gt 0 ]; then
        printf '?lag_behind=%s&cooldown_hours=%s' "$lag" "$cooldown"
    fi
    return 0
}

#==============================================================================
# FETCH LATEST VERSION FROM API
#==============================================================================

# Pinned scripts: the baked version and checksum stand in for the API's latest
# release. A checksum that isn't a SHA-256 digest verifies nothing; it is
# reported and the update skipped (a scheduled run then keeps the installed
# binary), so a working binary is never replaced or deleted.
use_pinned_version() {
    BINARY_VERSION="$PINNED_VERSION"
    BINARY_CHECKSUM=""
    case "$ARCH" in
        amd64) BINARY_CHECKSUM="$PINNED_CHECKSUM_AMD64" ;;
        arm64) BINARY_CHECKSUM="$PINNED_CHECKSUM_ARM64" ;;
    esac
    if ! [[ "$BINARY_CHECKSUM" =~ ^[0-9a-fA-F]{64}$ ]]; then
        print_error "No valid checksum in this script for v${BINARY_VERSION}"
        report_run_status_failed "checksum_invalid" "Pinned script has no valid checksum for v${BINARY_VERSION}"
        return 1
    fi
    BINARY_CHECKSUM=$(printf '%s' "$BINARY_CHECKSUM" | tr 'A-F' 'a-f')
    print_info "Pinned version: ${BINARY_VERSION}"
}

fetch_latest_version() {
    if [ -n "$PINNED_VERSION" ]; then
        use_pinned_version
        return
    fi
    if [ "$CURL_AVAILABLE" != "true" ]; then
        print_error "curl is required but not found"
        return 1
    fi

    print_info "Checking for latest binary version..."

    # Script-baked update-policy override rides the request as query params;
    # the API resolves the version with them in place of the organization
    # policy. No override = no params = today's behavior. curl -G appends the
    # os/arch data below to a URL that already has a query with "&".
    local policy_query
    policy_query=$(policy_query_string)
    if [ -n "$policy_query" ]; then
        print_info "Update policy override (script): ${policy_query#?}"
    fi

    # Pass os=linux + arch so the API returns the linux_${ARCH} checksum and
    # signature, not the macOS universal-binary checksum the endpoint
    # otherwise defaults to. Comparing the downloaded linux artifact against
    # the macOS checksum would reject every release.
    if ! api_get_with_retry -G \
        -H "Content-Type: application/json" \
        --data-urlencode "os=linux" \
        --data-urlencode "arch=${ARCH}" \
        "${API_ENDPOINT}/v1/${CUSTOMER_ID}/developer-mdm-agent/latest-binary${policy_query}"; then
        print_error "Failed to fetch latest binary info from API: ${API_FETCH_ERROR}"
        report_run_status_failed "api_failed" "Failed to fetch latest binary info from API: ${API_FETCH_ERROR}"
        return 1
    fi
    local response="$API_RESPONSE"

    BINARY_VERSION=$(echo "$response" | grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"version"[[:space:]]*:[[:space:]]*"//;s/"//')

    if [ -z "$BINARY_VERSION" ]; then
        print_error "Failed to parse version from API response"
        report_run_status_failed "version_parse_failed" "Could not extract version from latest-binary API"
        return 1
    fi

    print_info "Latest version: ${BINARY_VERSION}"

    BINARY_CHECKSUM=$(echo "$response" | grep -o '"checksum"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"checksum"[[:space:]]*:[[:space:]]*"//;s/"//')

    if [ -z "$BINARY_CHECKSUM" ]; then
        print_error "Checksum is empty for v${BINARY_VERSION}"
        report_run_status_failed "checksum_empty" "Checksum is empty for v${BINARY_VERSION}"
        return 1
    fi

    # signed_checksum is mandatory — releases must clear Ed25519 verification.
    local signed_checksum
    signed_checksum=$(echo "$response" | grep -o '"signed_checksum"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"signed_checksum"[[:space:]]*:[[:space:]]*"//;s/"//')

    if [ -z "$signed_checksum" ]; then
        print_error "API response is missing signed_checksum for v${BINARY_VERSION}"
        report_run_status_failed "signed_checksum_missing" "API response missing signed_checksum for v${BINARY_VERSION}"
        return 1
    fi

    print_info "Verifying checksum signature..."
    if ! verify_checksum_signature "$BINARY_CHECKSUM" "$signed_checksum"; then
        print_error "CHECKSUM SIGNATURE VERIFICATION FAILED — release rejected"
        print_error "The checksum did not pass Ed25519 signature verification."
        print_error "This could indicate tampering. Aborting."
        return 1
    fi
    print_success "Checksum signature verification passed"

    print_info "Expected checksum: ${BINARY_CHECKSUM}"
}

#==============================================================================
# CHECKSUM VERIFICATION
#==============================================================================

get_installed_checksum() {
    local f="${1:-$BINARY_PATH}"
    if [ -f "$f" ]; then
        sha256sum "$f" 2>/dev/null | awk '{print $1}' || echo ""
    else
        echo ""
    fi
}

get_installed_version() {
    if [ -f "$VERSION_FILE" ]; then
        cat "$VERSION_FILE" 2>/dev/null || echo ""
    else
        echo ""
    fi
}

#==============================================================================
# BINARY DOWNLOAD
#==============================================================================

# Create the install directory tree as the target user (under root, an MDM
# install, see _run_as_user) so the user owns it. This is the
# complement to the root-owned-files fix: that hands root-created *files* down
# to the user; this guarantees the *directory* the user writes into on every
# unprivileged systemd-timer tick exists and is user-owned — so a periodic run
# never has to create a directory under a root-owned parent (e.g. a custom
# INSTALL_DIR under /usr/local), which a non-root user cannot do.
#
# Check the mkdir explicitly: callers invoke this as `ensure_install_dir ||
# return 1` under the `ensure_binary || exit 1` chain, so `set -e` is suppressed
# here. A bare `mkdir -p` failure would otherwise be silently ignored and
# resurface one step later as a misleading "mktemp: No such file or directory".
ensure_install_dir() {
    local mkdir_output
    if mkdir_output=$(_run_as_user mkdir -p "$INSTALL_DIR" 2>&1); then
        return 0
    fi
    # A custom install dir under a root-owned parent: create the install root
    # as root and hand just that directory to the user. The user can't swap
    # entries in a parent it can't write, so the chown can't be redirected.
    if [ "$(id -u)" -eq 0 ] && ! _run_as_user test -w "$(dirname "$INSTALL_DIR_CONFIG")" \
        && mkdir_output=$(mkdir -p "$INSTALL_DIR_CONFIG" 2>&1) \
        && mkdir_output=$(chown -h "${LOGGED_IN_USER}:$(id -gn "$LOGGED_IN_USER")" "$INSTALL_DIR_CONFIG" 2>&1) \
        && mkdir_output=$(_run_as_user mkdir -p "$INSTALL_DIR" 2>&1); then
        return 0
    fi
    print_error "Failed to create install directory $INSTALL_DIR (uid $(id -u)): $mkdir_output"
    print_error "Hint: a parent of $INSTALL_DIR may be root-owned — installing into a system path must run as root (sudo / MDM)."
    report_run_status_failed "mkdir_failed" "mkdir -p failed for $INSTALL_DIR (uid $(id -u)): $mkdir_output"
    return 1
}

download_binary() {
    if [ "$CURL_AVAILABLE" != "true" ]; then
        print_error "curl is required but not found"
        return 1
    fi

    # Per-arch binary (linux_amd64 / linux_arm64) — see .goreleaser.yml in
    # dev-machine-guard. Unlike darwin, there is no universal Linux binary.
    local asset_name="${BINARY_NAME}-${BINARY_VERSION}-linux_${ARCH}"
    local github_url="${GITHUB_RELEASE_BASE}/v${BINARY_VERSION}/${asset_name}"

    print_info "Downloading binary v${BINARY_VERSION} (linux_${ARCH})..."

    # Ensure install directory exists (and, under root, is owned by the user).
    ensure_install_dir || return 1

    # Download to temp file for atomic replacement. Check mktemp explicitly:
    # `set -e` is suppressed inside this function (it runs under the
    # `download_binary || return 1` / `ensure_binary || exit 1` chain), so a
    # failed mktemp would otherwise leave $temp_file empty and the subsequent
    # `curl -o ""` would fail with a misleading "blank argument" error instead
    # of the real cause.
    # The download lands in a private temp file; only the verified bytes are
    # written into the user's tree (write_user_file).
    local temp_file mktemp_output
    if ! mktemp_output=$(mktemp "${TMPDIR:-/tmp}/${BINARY_NAME}.$$.XXXXXX" 2>&1); then
        print_error "Failed to create temp file (uid $(id -u)): $mktemp_output"
        report_run_status_failed "mktemp_failed" "mktemp failed (uid $(id -u)): $mktemp_output"
        return 1
    fi
    temp_file="$mktemp_output"
    DOWNLOAD_TEMP="$temp_file"

    # Try GitHub first; on any curl failure (network, DNS, TLS, 4xx, 5xx), fall
    # back to the public packages mirror. Checksum + ssh-keygen signature
    # verification still runs on whichever source succeeded — the URL is just
    # transport, the signature is the source of trust.
    local curl_stderr
    local curl_exit=0
    curl_stderr=$(curl -sSL -f --connect-timeout "$CURL_CONNECT_TIMEOUT_SECONDS" --max-time "$DOWNLOAD_MAX_TIME_SECONDS" -o "$temp_file" "$github_url" 2>&1) || curl_exit=$?
    local source_url="$github_url"
    if [ "$curl_exit" -ne 0 ]; then
        local github_reason
        github_reason=$(curl_exit_reason "$curl_exit")
        local github_failure="[$(net_error_code "$curl_exit" "$curl_stderr")] ${github_reason} (curl exit ${curl_exit}): ${curl_stderr}"

        # PACKAGES_BASE_URL is server-templated; an unreplaced literal means the
        # API didn't supply one, so skip the fallback rather than hitting a
        # bogus host.
        if [ -n "$PACKAGES_BASE_URL" ] && [[ "$PACKAGES_BASE_URL" != *"{{"* ]]; then
            local packages_url="${PACKAGES_BASE_URL}/${BINARY_VERSION}/${asset_name}"
            print_info "GitHub download failed (${github_reason}); trying packages mirror..."
            curl_exit=0
            curl_stderr=$(curl -sSL -f --connect-timeout "$CURL_CONNECT_TIMEOUT_SECONDS" --max-time "$DOWNLOAD_MAX_TIME_SECONDS" -o "$temp_file" "$packages_url" 2>&1) || curl_exit=$?
            if [ "$curl_exit" -eq 0 ]; then
                source_url="$packages_url"
            else
                rm -f "$temp_file"
                local pkg_reason
                pkg_reason=$(curl_exit_reason "$curl_exit")
                print_error "Failed to download binary v${BINARY_VERSION} from both GitHub and packages mirror"
                report_run_status_failed "download_failed" "Failed to download binary v${BINARY_VERSION}: github (${github_url}) -> ${github_failure}; packages (${packages_url}) -> [$(net_error_code "$curl_exit" "$curl_stderr")] ${pkg_reason} (curl exit ${curl_exit}): ${curl_stderr}"
                return 1
            fi
        else
            rm -f "$temp_file"
            print_error "Failed to download binary v${BINARY_VERSION}: ${github_failure}"
            report_run_status_failed "download_failed" "Failed to download binary v${BINARY_VERSION} from ${github_url}: ${github_failure}"
            return 1
        fi
    fi

    if [ ! -s "$temp_file" ]; then
        rm -f "$temp_file"
        print_error "Downloaded binary is empty"
        report_run_status_failed "download_failed" "Downloaded binary is empty"
        return 1
    fi

    # Verify before the swap so a bad download never replaces a working binary.
    local got
    got=$(get_installed_checksum "$temp_file")
    if [ "$got" != "$BINARY_CHECKSUM" ]; then
        rm -f "$temp_file"
        print_error "Downloaded binary checksum mismatch (expected: ${BINARY_CHECKSUM}, got: ${got})"
        report_run_status_failed "checksum_mismatch" "Downloaded binary checksum mismatch for v${BINARY_VERSION}"
        return 1
    fi

    # 755 so user-mode ticks can read (sha256sum) the installed binary.
    if ! write_user_file "$BINARY_PATH" 755 < "$temp_file"; then
        rm -f "$temp_file"
        print_error "Failed to install binary to ${BINARY_PATH} (uid $(id -u))"
        report_run_status_failed "install_failed" "Failed to write ${BINARY_PATH} (uid $(id -u))"
        return 1
    fi
    rm -f "$temp_file"

    print_success "Binary v${BINARY_VERSION} installed to ${BINARY_PATH} (source: ${source_url})"
}

#==============================================================================
# CONFIGURATION
#==============================================================================

write_config() {
    # install_dir is persisted only when the operator picked a non-default
    # location. This mirrors the agent's `install_dir,omitempty` JSON tag
    # (dev-machine-guard internal/config/config.go) so vanilla installs
    # keep config.json minimal and customised installs are picked up by
    # the agent's paths.Home() chain on the next run. Escape backslashes
    # and double-quotes for JSON safety in case the operator typed an
    # unusual path.
    local default_dir="$USER_HOME/.stepsecurity"
    local install_dir_line=""
    if [ "$INSTALL_DIR_CONFIG" != "$default_dir" ]; then
        local escaped
        escaped=$(printf '%s' "$INSTALL_DIR_CONFIG" | sed 's/\\/\\\\/g; s/"/\\"/g')
        install_dir_line=",
  \"install_dir\": \"${escaped}\""
    fi

    # Persist the execution-watchdog limit into config.json so the binary's
    # watchdog reads it on EVERY invocation — including systemd-timer-fired runs
    # that invoke the binary directly and never inherit a loader-exported env
    # var. Config-file channel replaces the old STEPSEC_MAX_EXECUTION_DURATION
    # export. Positive integer N → "Nh"; 0 → "0" (explicitly disables); anything
    # else omitted so the binary's built-in default applies.
    local max_exec_line=""
    local exec_h="${MAX_EXECUTION_DURATION_HOURS:-4}"
    if [[ "$exec_h" =~ ^[0-9]+$ ]]; then
        if [ "$exec_h" -gt 0 ]; then
            max_exec_line=",
  \"max_execution_duration\": \"${exec_h}h\""
        else
            max_exec_line=",
  \"max_execution_duration\": \"0\""
        fi
    fi

    # Optional scan-config fields from the install wizard. Each is emitted only
    # when set; empty means "let the binary's default apply". search_dirs is a
    # ready-made JSON array (built server-side); the rest are JSON booleans.
    local search_dirs_line=""
    if [ -n "$SEARCH_DIRS_JSON" ]; then
        search_dirs_line=",
  \"search_dirs\": ${SEARCH_DIRS_JSON}"
    fi
    local tcc_line=""
    if [ -n "$INCLUDE_TCC_PROTECTED" ]; then
        tcc_line=",
  \"include_tcc_protected\": ${INCLUDE_TCC_PROTECTED}"
    fi
    # Device identity template (a STEPSEC_DEVICE_ID environment variable wins)
    # and retire-on-uninstall, persisted so scheduler-fired binary runs, which
    # bypass the loader, resolve the same identity. ${VAR:-} keeps set -u happy.
    local device_id_line=""
    local _device_id="${STEPSEC_DEVICE_ID:-${DEVICE_ID_TEMPLATE:-}}"
    if [ "$_device_id" = "-" ]; then
        # Explicit reset to the hardware serial: no device_id is written and
        # an id a previous install left in config.json is not carried over.
        _device_id=""
    else
        # Fallback: a device_id an admin set by hand in the existing config.
        [ -n "$_device_id" ] || _device_id=$(configured_device_id)
    fi
    if [ -n "$_device_id" ]; then
        local escaped_device_id
        escaped_device_id=$(printf '%s' "$_device_id" | sed 's/\\/\\\\/g; s/"/\\"/g')
        device_id_line=",
  \"device_id\": \"${escaped_device_id}\""
    fi
    local retire_line=""
    if [ -n "${RETIRE_ON_UNINSTALL:-}" ]; then
        retire_line=",
  \"retire_on_uninstall\": ${RETIRE_ON_UNINSTALL}"
    fi
    local device_tag_line=""
    if [ -n "${DEVICE_TAG:-}" ]; then
        device_tag_line=",
  \"device_tag\": \"${DEVICE_TAG}\""
    fi
    local npm_line=""
    if [ -n "$ENABLE_NPM_SCAN" ]; then
        npm_line=",
  \"enable_npm_scan\": ${ENABLE_NPM_SCAN}"
    fi
    local brew_line=""
    if [ -n "$ENABLE_BREW_SCAN" ]; then
        brew_line=",
  \"enable_brew_scan\": ${ENABLE_BREW_SCAN}"
    fi
    local python_line=""
    if [ -n "$ENABLE_PYTHON_SCAN" ]; then
        python_line=",
  \"enable_python_scan\": ${ENABLE_PYTHON_SCAN}"
    fi

    local cfg
    cfg=$(cat <<EOF
{
  "customer_id": "${CUSTOMER_ID}",
  "api_endpoint": "${API_ENDPOINT}",
  "api_key": "${API_KEY}",
  "scan_frequency_hours": "${SCAN_FREQUENCY_HOURS}"${install_dir_line}${max_exec_line}${search_dirs_line}${tcc_line}${npm_line}${brew_line}${python_line}${device_id_line}${retire_line}${device_tag_line}
}
EOF
)

    if ! { _run_as_user mkdir -p "$CONFIG_DIR" && printf '%s\n' "$cfg" | write_user_file "$CONFIG_FILE" 600; }; then
        print_error "Failed to write ${CONFIG_FILE} (uid $(id -u))"
        report_run_status_failed "config_write_failed" "Failed to write ${CONFIG_FILE} (uid $(id -u))"
        return 1
    fi
    print_info "Configuration written to ${CONFIG_FILE}"
}

save_version() {
    printf '%s\n' "$BINARY_VERSION" | write_user_file "$VERSION_FILE" 644
}

#==============================================================================
# ENSURE BINARY IS UP-TO-DATE
#==============================================================================

ensure_binary() {
    fetch_latest_version || return 1

    local installed_checksum
    installed_checksum=$(get_installed_checksum)

    if [ "$installed_checksum" = "$BINARY_CHECKSUM" ]; then
        if binary_runnable; then
            print_info "Binary v${BINARY_VERSION} is up-to-date (checksum verified)"
            _run_as_user rm -f "${BINARY_PATH}.prev" 2>/dev/null || true
            save_version
            return 0
        fi
        print_info "Binary v${BINARY_VERSION} does not run (${BINARY_RUN_ERROR}), reinstalling..."
    elif [ -f "$BINARY_PATH" ]; then
        print_info "Binary checksum mismatch, downloading v${BINARY_VERSION}..."
    else
        print_info "Binary not found, downloading v${BINARY_VERSION}..."
    fi

    # Keep the installed binary until its replacement runs: a checksum-valid
    # release can still fail to start on this machine (e.g. it needs a newer
    # OS), and ensure_binary_or_installed falls back to the installed one.
    # Only a binary that runs replaces the kept copy: after a run killed
    # between the swap and the restore, the installed binary is the broken one
    # and the copy from that run is still the working fallback.
    local prev="${BINARY_PATH}.prev"
    if [ -f "$BINARY_PATH" ] && binary_runnable; then
        _run_as_user rm -f "$prev" 2>/dev/null || true
        _run_as_user ln -f "$BINARY_PATH" "$prev" 2>/dev/null \
            || _run_as_user cp -p "$BINARY_PATH" "$prev" 2>/dev/null || true
    fi
    if ! download_binary; then
        _run_as_user rm -f "$prev" 2>/dev/null || true
        return 1
    fi
    if ! binary_runnable; then
        print_error "Binary v${BINARY_VERSION} does not run: ${BINARY_RUN_ERROR}"
        report_run_status_failed "binary_not_runnable" "v${BINARY_VERSION} at ${BINARY_PATH}: ${BINARY_RUN_ERROR}"
        if [ -f "$prev" ] && _run_as_user mv -f "$prev" "$BINARY_PATH" 2>/dev/null; then
            print_info "Restored the previously installed binary"
        fi
        return 1
    fi
    _run_as_user rm -f "$prev" 2>/dev/null || true

    print_info "Binary v${BINARY_VERSION} checksum verified"
    save_version
}

#==============================================================================
# SYSTEMD CONFIGURATION
#==============================================================================

# Copy this script to a stable location next to the binary so the systemd
# timer can re-invoke it across reboots even if the user deletes the original
# download. Skip the copy when already running from $LOADER_SCRIPT_PATH.
install_loader_script() {
    _run_as_user mkdir -p "$INSTALL_DIR"

    # Under `curl ... | bash` there is no script file ("$0" is the shell).
    local src="${BASH_SOURCE[0]:-}"
    if [ ! -f "$src" ]; then
        print_error "Cannot copy the loader: not running from a file (${src}). Download the script and run it from disk."
        report_run_status_failed "loader_copy_failed" "Loader not running from a file (${src})"
        return 1
    fi

    local current_path
    current_path=$(realpath "$src" 2>/dev/null || echo "$src")
    local target_path
    target_path=$(realpath "$LOADER_SCRIPT_PATH" 2>/dev/null || echo "$LOADER_SCRIPT_PATH")

    if [ "$current_path" != "$target_path" ]; then
        # The copy embeds the API key: owner-only.
        if ! write_user_file "$LOADER_SCRIPT_PATH" 700 < "$src"; then
            print_error "Failed to install the loader script to ${LOADER_SCRIPT_PATH}"
            report_run_status_failed "loader_copy_failed" "Failed to write ${LOADER_SCRIPT_PATH} (uid $(id -u))"
            return 1
        fi
        print_info "Loader script installed to ${LOADER_SCRIPT_PATH}"
    fi
}

# Write and load the systemd user units. The service ExecStart points at the
# loader script (not the binary) so each periodic fire goes through the
# auto-update path before delegating to the binary.
#
# Mirrors dev-machine-guard internal/systemd/systemd.go field-for-field except
# for ExecStart — same unit name so an existing binary-installed pair gets
# cleanly replaced.
# Without linger the user's systemd manager, and the timer with it, stops at
# logout, and an install with no session (cron, SSH automation) finds no
# manager at all. Enabling it (root, or the user where polkit allows) also
# starts the manager now; wait briefly for its bus.
ensure_linger() {
    command -v loginctl &>/dev/null || return 0
    if [ "$(loginctl show-user "$LOGGED_IN_USER" -p Linger 2>/dev/null | sed 's/^[^=]*=//' || true)" = "yes" ]; then
        return 0
    fi
    if loginctl enable-linger "$LOGGED_IN_USER" 2>/dev/null; then
        print_info "Enabled systemd linger for ${LOGGED_IN_USER}: scans continue while logged out"
        local i
        for i in 1 2 3 4 5 6 7 8 9 10; do
            [ -e "/run/user/${USER_UID}/bus" ] && break
            sleep 0.5
        done
        return 0
    fi
    print_info "Could not enable systemd linger; scans stop while ${LOGGED_IN_USER} is logged out."
    print_info "  To keep them running: sudo loginctl enable-linger ${LOGGED_IN_USER}"
}

configure_systemd() {
    # Launch cadence in minutes. Launches are cheap: on each fire the binary
    # checks in with the backend and only scans when the tenant's cadence
    # (StepSecurity dashboard, 4h default) says a scan is due.
    local minutes="${SCAN_FREQUENCY_MINUTES:-15}"
    if ! [[ "$minutes" =~ ^[0-9]+$ ]] || [ "$minutes" -le 0 ]; then
        print_info "SCAN_FREQUENCY_MINUTES '${minutes}' is not a positive integer, defaulting to 15"
        minutes=15
    fi

    _run_as_user mkdir -p "$LOG_DIR" "$SYSTEMD_UNIT_DIR"
    ensure_linger

    local service timer proxy_env
    proxy_env=$(systemd_proxy_env)
    [ -z "$proxy_env" ] || proxy_env=$'\n'"$proxy_env"
    service=$(cat <<EOF
[Unit]
Description=StepSecurity Dev Machine Guard scan

[Service]
Type=oneshot
# Only HOME and the install's proxy settings are injected — the loader
# reads INSTALL_DIR_CONFIG itself.
# Quote the value so a $HOME with spaces survives systemd's whitespace
# splitting.
Environment="HOME=${USER_HOME}"${proxy_env}
ExecStart=/bin/bash ${LOADER_SCRIPT_PATH} send-telemetry
StandardOutput=append:${LOG_DIR}/agent.log
StandardError=append:${LOG_DIR}/agent.error.log
EOF
)
    timer=$(cat <<EOF
[Unit]
Description=StepSecurity Dev Machine Guard periodic scan

[Timer]
OnBootSec=5min
OnUnitActiveSec=${minutes}m
Persistent=true

[Install]
WantedBy=timers.target
EOF
)

    # A re-run with nothing changed leaves the active timer alone: disable +
    # enable --now restarts it, and a restarted timer whose OnBootSec has
    # passed fires at once, on top of the install's own first scan.
    if [ "$(_run_as_user cat "$SYSTEMD_SERVICE_PATH" 2>/dev/null || true)" = "$service" ] \
        && [ "$(_run_as_user cat "$SYSTEMD_TIMER_PATH" 2>/dev/null || true)" = "$timer" ] \
        && run_systemctl_user is-active --quiet "${SYSTEMD_UNIT_NAME}.timer" 2>/dev/null; then
        print_info "systemd user timer unchanged and already active: ${SYSTEMD_TIMER_PATH}"
        return 0
    fi

    # Disable any existing timer so the swap to a new ExecStart target is
    # clean. The `|| true` handles both first-install and stale state.
    run_systemctl_user disable --now "${SYSTEMD_UNIT_NAME}.timer" 2>/dev/null || true

    local mode=644
    if proxy_has_credentials; then
        mode=600
        print_info "A proxy URL carries credentials: ${SYSTEMD_SERVICE_PATH} is written owner-only"
    fi
    if ! printf '%s\n' "$service" | write_user_file "$SYSTEMD_SERVICE_PATH" "$mode"; then
        print_error "Failed to write ${SYSTEMD_SERVICE_PATH}"
        report_run_status_failed "systemd_unit_write_failed" "Failed to write ${SYSTEMD_SERVICE_PATH} (uid $(id -u))"
        return 1
    fi

    if ! printf '%s\n' "$timer" | write_user_file "$SYSTEMD_TIMER_PATH" 644; then
        print_error "Failed to write ${SYSTEMD_TIMER_PATH}"
        report_run_status_failed "systemd_unit_write_failed" "Failed to write ${SYSTEMD_TIMER_PATH} (uid $(id -u))"
        return 1
    fi

    if ! run_systemctl_user daemon-reload; then
        print_error "systemctl --user daemon-reload failed"
        report_run_status_failed "systemd_reload_failed" "systemctl --user daemon-reload failed"
        return 1
    fi

    if ! run_systemctl_user enable --now "${SYSTEMD_UNIT_NAME}.timer"; then
        print_error "systemctl --user enable failed for ${SYSTEMD_UNIT_NAME}.timer"
        report_run_status_failed "systemd_enable_failed" "systemctl --user enable failed for ${SYSTEMD_UNIT_NAME}.timer"
        return 1
    fi

    print_info "systemd user timer configured (interval: ${minutes}m)"
    print_info "  Service: ${SYSTEMD_SERVICE_PATH}"
    print_info "  Timer:   ${SYSTEMD_TIMER_PATH}"
    print_info "  Logs:    ${LOG_DIR}/agent.log"
}

#==============================================================================
# MAIN COMMAND HANDLER
#==============================================================================

# Capture this run's loader output into .loader_log (truncated fresh per run) so
# the dev-machine-guard binary folds it into its run-status logs and then deletes
# it (see seedLoaderLog). Self-bounding: only ever holds one run's output, even
# if no binary consumes it.
LOADER_LOG_FILE="${LOG_DIR:+$LOG_DIR/.loader_log}"
LOADER_LOG_BUFFER=""
if [ -z "$LOADER_LOG_FILE" ]; then
    :
elif [ "$(id -u)" -eq 0 ]; then
    # Root never opens the user's .loader_log; see flush_loader_log.
    LOADER_LOG_BUFFER=$(mktemp "${TMPDIR:-/tmp}/stepsecurity-loader-log.$$.XXXXXX" 2>/dev/null) || LOADER_LOG_FILE=""
else
    : 2>/dev/null > "$LOADER_LOG_FILE" || true
fi

# Uninstall: stop running agents first, so none keeps scanning, writing into
# the tree being removed, or holding the instance lock. TERM, then KILL.
stop_agent_processes() {
    local pids p _wait
    pids=$(agent_pids)
    [ -n "$pids" ] || return 0
    print_info "Stopping running agent processes: $(echo $pids)"
    kill -TERM $pids 2>/dev/null || true
    for _wait in 1 2 3 4 5 6 7 8 9 10; do
        pids=$(for p in $pids; do kill -0 "$p" 2>/dev/null && echo "$p"; done || true)
        [ -n "$pids" ] || return 0
        sleep 0.5
    done
    kill -KILL $pids 2>/dev/null || true
}

# Uninstall: the agent's instance locks (PID file, and the flock of >= 1.18.0),
# once no agent is left to hold them.
remove_instance_locks() {
    [ -z "$(agent_pids)" ] || return 0
    rm -f /tmp/stepsecurity-dev-machine-guard.lock /tmp/stepsecurity-dev-machine-guard.flock 2>/dev/null || true
}

# Uninstall: remove the rest of the install tree. The default tree
# (~/.stepsecurity) is the agent's own (logs, state, caches), so all of it
# goes; a custom install dir may hold other things, so only the files the
# loader and agent write go, and the directories only if then empty.
remove_install_tree() {
    local d
    for d in "$INSTALL_DIR_CONFIG" "$USER_HOME/.stepsecurity"; do
        if [ "$d" = "$USER_HOME/.stepsecurity" ]; then
            _run_as_user rm -rf "$d" 2>/dev/null || true
            continue
        fi
        _run_as_user rm -f "$d/bin/$BINARY_NAME" "$d/bin/$BINARY_NAME.prev" "$d/bin/stepsecurity-loader.sh" "$d/config.json" \
            "$d/.current_version" "$d/.loader_log" "$d/agent.log" "$d/agent.error.log" 2>/dev/null || true
        _run_as_user find "$d" -maxdepth 2 -type f \( -name "${BINARY_NAME}.??????" -o -name 'config.json.??????' \
            -o -name '.loader_log.??????' -o -name '.current_version.??????' -o -name 'stepsecurity-loader.sh.??????' \) \
            -exec rm -f {} + 2>/dev/null || true
        _run_as_user rmdir "$d/bin" "$d" 2>/dev/null || true
    done
}

# Record what an uninstall left behind for the current user context.
note_residue() {
    local f
    for f in "$@"; do
        if [ -e "$f" ] || [ -L "$f" ]; then UNINSTALL_RESIDUE="${UNINSTALL_RESIDUE} ${f}"; fi
    done
    return 0
}

# Tear down the install of the current user context (see set_user_context).
uninstall_for_user() {
    # Disable + remove the systemd units (loader-owned).
    run_systemctl_user disable --now "${SYSTEMD_UNIT_NAME}.timer" 2>/dev/null || true
    run_systemctl_user stop "${SYSTEMD_UNIT_NAME}.service" 2>/dev/null || true

    for unit_path in "$SYSTEMD_SERVICE_PATH" "$SYSTEMD_TIMER_PATH"; do
        if [ -f "$unit_path" ]; then
            _run_as_user rm -f "$unit_path" || true
            print_success "Removed ${unit_path}"
        fi
    done

    # disable can't reach a user manager that isn't running (no session).
    _run_as_user rm -f "$SYSTEMD_UNIT_DIR/timers.target.wants/${SYSTEMD_UNIT_NAME}.timer" || true

    run_systemctl_user daemon-reload 2>/dev/null || true

    # Best-effort binary uninstall — idempotent and tolerates missing units.
    if [ -x "$BINARY_PATH" ]; then
        # The binary's persisted retire_on_uninstall setting decides whether the
        # device is retired in the dashboard; no flag overrides it here.
        run_binary_as_user uninstall || true
    fi

    if [ -f "$BINARY_PATH" ]; then
        _run_as_user rm -f "$BINARY_PATH" || true
        print_success "Removed binary: ${BINARY_PATH}"
    fi

    if [ -f "$LOADER_SCRIPT_PATH" ]; then
        _run_as_user rm -f "$LOADER_SCRIPT_PATH" || true
        print_success "Removed loader script: ${LOADER_SCRIPT_PATH}"
    fi

    _run_as_user rm -f "$VERSION_FILE" || true

    # Remove the credential-bearing config: the install-tree copy and the
    # legacy bootstrap copy both hold the tenant API key.
    _run_as_user rm -f "$CONFIG_FILE" "$INSTALL_DIR_CONFIG/config.json" "$USER_HOME/.stepsecurity/config.json" || true

    # /etc/stepsecurity/device-id is kept: a reinstall then reports as the
    # same device instead of a new one.
    remove_install_tree
    note_residue "$SYSTEMD_SERVICE_PATH" "$SYSTEMD_TIMER_PATH" "$SYSTEMD_UNIT_DIR/timers.target.wants/${SYSTEMD_UNIT_NAME}.timer" \
        "$BINARY_PATH" "$LOADER_SCRIPT_PATH" "$INSTALL_DIR_CONFIG/config.json" "$USER_HOME/.stepsecurity/config.json"
}

sweep_stale_temp_files

case "$COMMAND" in
    send-telemetry|--send-telemetry)
        kill_stale_dmg_processes
        remove_stale_instance_lock
        ensure_binary_or_installed || exit 1
        write_config
        handoff_loader_log
        run_scan
        ;;
    install|--install)
        echo "StepSecurity Device Agent Loader"
        echo ""

        if [[ "$CUSTOMER_ID" == *"{{"* ]]; then
            print_error "This script needs to be customized with your customer details"
            print_error "Please download the installation script from your StepSecurity dashboard"
            exit 1
        fi

        # Create + own the install tree up front while we (may) have root, so
        # later unprivileged systemd-timer ticks never need to create a directory
        # under a root-owned parent (the inverse of the root-owned-files case).
        # The scheduled scans need systemd as init (not WSL without systemd,
        # not most containers): say so before downloading anything.
        if [ ! -d /run/systemd/system ]; then
            print_error "systemd is not running as the init system; the scheduled scan can't be installed"
            report_run_status_failed "systemd_unavailable" "systemd is not the init system (/run/systemd/system missing)"
            exit 1
        fi
        ensure_install_dir || exit 1
        ensure_binary || exit 1
        write_config

        # Loader owns the systemd units (replaces "$BINARY_PATH" install).
        # Periodic timer fires re-invoke this script with send-telemetry so
        # the binary version is checked on every tick.
        install_loader_script || exit 1
        configure_systemd || exit 1

        echo ""
        print_success "Installation complete!"
        print_info "The agent will check in every ${SCAN_FREQUENCY_MINUTES:-15} minutes and scan on the schedule set in your StepSecurity dashboard"
        # First scan through the service, like every later timer fire, so it
        # never overlaps a fire of the just-enabled timer, and so the
        # install's result is the install's, not the scan's (the agent
        # reports its own failures).
        kill_stale_dmg_processes
        handoff_loader_log
        if run_systemctl_user start --no-block "${SYSTEMD_UNIT_NAME}.service"; then
            print_info "Initial scan started (logs: ${LOG_DIR}/agent.log)"
        else
            print_info "Could not start the initial scan now; the timer runs it"
        fi
        ;;
    uninstall|--uninstall)
        echo "StepSecurity Device Agent Loader"
        echo ""

        stop_agent_processes
        UNINSTALL_RESIDUE=""
        _target_user="$LOGGED_IN_USER"
        if [ -n "$_target_user" ]; then
            uninstall_for_user
        fi
        # As root, every other account with an install too: shared hosts, and
        # headless hosts (cron) with no target user.
        if [ "$(id -u)" -eq 0 ]; then
            while IFS=: read -r _u _ _uid _ _ _h _ <&3; do
                [ -n "$_u" ] && [ "$_uid" != 0 ] && [ "$_u" != "$_target_user" ] && [ -d "$_h" ] || continue
                [ -e "$_h/.config/systemd/user/${SYSTEMD_UNIT_NAME}.timer" ] || [ -e "$_h/.stepsecurity" ] || continue
                print_info "Uninstalling for ${_u}"
                set_user_context "$_u" "$_h"
                uninstall_for_user
            done 3< <(getent passwd 2>/dev/null)
        fi
        remove_instance_locks

        if [ -n "$UNINSTALL_RESIDUE" ]; then
            print_error "Uninstall incomplete; still present:${UNINSTALL_RESIDUE}"
            report_run_status_failed "uninstall_incomplete" "Still present after uninstall:${UNINSTALL_RESIDUE}"
            exit 1
        fi
        print_success "Uninstall complete"
        ;;
    help|--help|-h)
        echo "StepSecurity Device Agent Loader"
        echo ""
        echo "This loader downloads the latest dev-machine-guard binary, configures it, and runs it."
        echo ""
        echo "Usage:"
        echo "  $0 install         - Download binary, configure, and enable periodic telemetry"
        echo "  $0 uninstall       - Remove periodic execution and binary"
        echo "  $0 send-telemetry  - Ensure binary is up-to-date and send telemetry"
        echo "  $0 help            - Show this help message"
        exit 0
        ;;
    default|""|run)
        kill_stale_dmg_processes
        remove_stale_instance_lock
        ensure_binary_or_installed || exit 1
        write_config
        handoff_loader_log
        run_scan
        ;;
    *)
        # Reached only if the default command baked into the script at
        # generation time is invalid. Unknown command-line arguments (e.g.
        # Jamf's mount-point "$1") are ignored by the scan above and fall back
        # to that default, so landing here means a misconfigured script, not an
        # MDM-passed argument — fail loudly rather than silently send telemetry.
        echo "Unknown command: $COMMAND"
        echo ""
        echo "Usage:"
        echo "  $0 install         - Download binary, configure, and enable periodic telemetry"
        echo "  $0 uninstall       - Remove periodic execution and binary"
        echo "  $0 send-telemetry  - Ensure binary is up-to-date and send telemetry"
        echo "  $0 help            - Show this help message"
        exit 1
        ;;
esac
