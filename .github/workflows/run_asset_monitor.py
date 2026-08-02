import ipaddress
import os
import socket
import subprocess
import sys
from urllib.parse import urlparse


def is_safe_url(url: str) -> tuple[bool, str | None, int | None, str | None]:
    """
    Validates a URL against SSRF vulnerabilities.
    Returns (is_safe, hostname, port, resolved_ip).
    """
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        if scheme not in ("http", "https"):
            print(f"Rejected URL scheme: {scheme}", file=sys.stderr)
            return False, None, None, None

        hostname = parsed.hostname
        if not hostname:
            print("Rejected URL: empty or missing hostname", file=sys.stderr)
            return False, None, None, None

        port = parsed.port
        if not port:
            port = 443 if scheme == "https" else 80

        # Try to parse hostname as IP address directly first
        try:
            ip = ipaddress.ip_address(hostname)
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_unspecified
                or ip.is_reserved
                or ip.is_multicast
            ):
                print(f"Rejected IP address (private/loopback/reserved): {ip}", file=sys.stderr)
                return False, None, None, None
            return True, hostname, port, str(ip)
        except ValueError:
            # Not a direct IP address, let's resolve the hostname
            pass

        try:
            addr_info = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
        except socket.gaierror as e:
            print(f"Failed to resolve hostname '{hostname}': {e}", file=sys.stderr)
            return False, None, None, None

        resolved_ips = []
        for res in addr_info:
            ip_str = res[4][0]
            try:
                ip = ipaddress.ip_address(ip_str)
                if (
                    ip.is_private
                    or ip.is_loopback
                    or ip.is_link_local
                    or ip.is_unspecified
                    or ip.is_reserved
                    or ip.is_multicast
                ):
                    print(
                        f"Rejected resolved IP address (private/loopback/reserved) for {hostname}: {ip}",
                        file=sys.stderr,
                    )
                    return False, None, None, None
                resolved_ips.append(str(ip))
            except ValueError:
                print(f"Failed to parse IP address: {ip_str}", file=sys.stderr)
                return False, None, None, None

        if not resolved_ips:
            print(f"No valid IP addresses resolved for hostname '{hostname}'", file=sys.stderr)
            return False, None, None, None

        return True, hostname, port, resolved_ips[0]

    except Exception as e:
        print(f"Error during URL safety validation: {e}", file=sys.stderr)
        return False, None, None, None


def verify_url(url: str, label: str) -> bool:
    """Return True if `url` is safe and responds with HTTP 200, False otherwise."""
    is_safe, hostname, port, resolved_ip = is_safe_url(url)
    if not is_safe or not hostname or not port or not resolved_ip:
        print(f"Blocked unsafe URL or validation failed for {label} ({url})", file=sys.stderr)
        return False

    try:
        # Format resolved IP correctly for IPv6 if needed
        if ":" in resolved_ip:
            resolve_arg = f"{hostname}:{port}:[{resolved_ip}]"
        else:
            resolve_arg = f"{hostname}:{port}:{resolved_ip}"

        # Pinned DNS resolution to avoid DNS rebinding via curl's --resolve parameter.
        # Restrict protocols to only http/https using --proto.
        result = subprocess.run(
            [
                "curl",
                "-s",
                "-o",
                "/dev/null",
                "-w",
                "%{http_code}",
                "--proto",
                "-all,http,https",
                "--resolve",
                resolve_arg,
                url,
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        return result.stdout == "200"
    except (subprocess.SubprocessError, OSError):
        print(f"Error verifying {label} ({url})", file=sys.stderr)
        return False


# We will simulate the telegram tool here for local execution and clarity.
def send_telegram_message(chat_id: str, message: str):
    """
    Simulates calling an external 'telegram' tool to send a message.
    In a real Hermes agent environment, this would be a call to the
    `telegram` tool via `execute_code` or a similar mechanism.
    """
    print("--- SIMULATING TELEGRAM ALERT ---")
    print(f"TO: {chat_id}")
    print(f"MESSAGE: {message}")
    print("-------------------------------")


def main():
    """
    Reads URLs from a config file, verifies them using the existing script,
    and sends a Telegram alert on failure.
    """
    urls_file = "/home/sakthai/config/asset_monitor_urls.txt"
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not chat_id:
        print("❌ ERROR: TELEGRAM_CHAT_ID environment variable not set.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(urls_file) as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"❌ ERROR: Configuration file not found at {urls_file}", file=sys.stderr)
        sys.exit(1)

    if not urls:
        print("No URLs to monitor. Exiting.", file=sys.stderr)
        sys.exit(0)

    print(f"Monitoring {len(urls)} assets...")
    failed_urls = []
    for i, url in enumerate(urls):
        if not verify_url(url, f"Resource #{i + 1}"):
            failed_urls.append(url)

    if not failed_urls:
        print("✅ All assets are available and accessible.")
    else:
        message = "🚨 Asset Monitor Failure!\nThe following assets may be down:\n" + "\n".join(
            f"- {url}" for url in failed_urls
        )
        send_telegram_message(chat_id, message)
        print(f"🔥 Alert sent for {len(failed_urls)} failed asset(s).", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
