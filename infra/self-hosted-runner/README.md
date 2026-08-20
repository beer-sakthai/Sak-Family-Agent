# Self-hosted Actions runner

A self-hosted runner for `beer-sakthai/Sak-Family-Agent`: install scripts, a
systemd unit, and the wiring that lets a workflow use it **without** any
workflow becoming dependent on it.

| File | What it does |
|---|---|
| `install-runner.sh` | Downloads, verifies and registers the runner (ephemeral) |
| `bootstrap-toolchain.sh` | Installs git / uv / Node 22 / pnpm; `--check` reports without changing anything |
| `github-actions-runner.service` | systemd unit — one job per process, restart into a fresh registration |

---

## Read this part first

**A self-hosted runner executes the code of whatever commit it is given, on
your hardware, as the runner user.** GitHub-hosted runners are destroyed after
every job; a self-hosted host is not, unless you make it behave that way. Two
rules follow, and everything in this directory is built around them.

**1. Never expose this runner to pull requests from forks.** GitHub's own
documentation is unusually blunt about it, and the reason is that a fork's pull
request is an arbitrary person's code arriving with permission to run. This
repository is public-adjacent and takes agent-authored branches routinely.
Before setting `CI_RUNNER_LABEL` (below), confirm in **Settings → Actions →
General** that *"Require approval for all external contributors"* is enabled —
that setting, not the workflow files, is what holds a fork's job until a
maintainer releases it.

**2. The runner is registered `--ephemeral`.** It accepts one job, then
deregisters and exits; systemd restarts it into a fresh registration. This is
what stops state from crossing between jobs — a poisoned dependency cache, a
file left in `_work`, a `~/.gitconfig` or `~/.netrc` a previous job wrote. It
costs a few seconds per job and it is not optional.

The runner user must not be root, must not be in `sudo`, and must not be in
`docker` (membership of `docker` is root, one `docker run -v /:/host` away).

---

## Install

```bash
# On the runner host, as the runner user.
sudo adduser --system --group --home /home/gh-runner --shell /bin/bash gh-runner
sudo -u gh-runner -i

git clone https://github.com/beer-sakthai/Sak-Family-Agent
cd Sak-Family-Agent/infra/self-hosted-runner

./bootstrap-toolchain.sh                 # git, uv, Node 22, pnpm
./bootstrap-toolchain.sh --check         # confirm

# Registration token from Settings -> Actions -> Runners -> New self-hosted
# runner. It expires after one hour and it is a credential.
./install-runner.sh --token <TOKEN> --labels sak-linux-x64
```

Then run it as a service:

```bash
sudo cp github-actions-runner.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now github-actions-runner
journalctl -u github-actions-runner -f
```

`RUNNER_SHA256=<digest from the release page> ./install-runner.sh …` verifies
the downloaded tarball. Unset, the script prints the digest it got and says in
as many words that nothing was verified — it does not pretend otherwise.

---

## Pointing workflows at it

`ci.yml` reads its runner from a repository variable:

```yaml
runs-on: ${{ vars.CI_RUNNER_LABEL || 'ubuntu-latest' }}
```

Set **Settings → Secrets and variables → Actions → Variables →
`CI_RUNNER_LABEL`** to the label you registered (`sak-linux-x64`) and CI moves
onto your hardware. **Delete the variable and it is back on `ubuntu-latest` on
the next run** — no workflow edit, no pull request, nothing to revert.

That fallback is the whole design. A hard-coded `runs-on: [self-hosted]` makes
every workflow in the repository depend on a host staying up: when the VM is
down or the disk fills, jobs do not fail, they queue — silently, for up to 24
hours, and then expire. A repository variable makes the dependency something
you switch off in ten seconds from a settings page.

Only `ci.yml` is wired this way on purpose. The security and analysis workflows
(CodeQL, Scorecard, gitleaks, bandit, dependency-review) stay on GitHub-hosted
runners: their value is that they run in an environment nobody in this
repository controls, and moving them onto a host that a compromised job could
have touched defeats the point.

### Checking the runner is actually there

`.github/workflows/self-hosted-runner-health.yml` — manual, plus a daily
schedule — sends a job to the label in `CI_RUNNER_LABEL` and reports the
toolchain it finds. It is skipped entirely when the variable is unset, so it
costs nothing on a repository with no runner, and it fails fast (10-minute
timeout) rather than queueing when the host is down. Run it after any change to
the host, and read it first when CI starts behaving strangely.

---

## Operating notes

**Disk.** `_work` is not cleaned between ephemeral registrations, and this
repository is large: a python CodeQL database is hundreds of megabytes, and
`uv` and the pnpm store both cache under `$HOME`. Budget 50 GB and watch it; a
full disk on a self-hosted runner produces failures that look nothing like
"disk full".

**Updates.** The runner self-updates its own binary by default. The toolchain
does not — re-run `bootstrap-toolchain.sh` after any change to the Node floor
or the Python matrix in `ci.yml`.

**Deregistering.** `./config.sh remove --token <REMOVAL_TOKEN>` from
`~/actions-runner`, after `sudo systemctl disable --now
github-actions-runner`. Removing the VM without deregistering leaves an offline
runner in the repository settings that jobs will still be dispatched to.

**Relationship to `infra/vm-agents/`.** Different thing, same kind of host.
`vm-agents/` runs the six personas as long-lived Telegram services; this runs
CI jobs. Do not put both on one machine — a CI job that fills the disk or pegs
the CPU would take the personas down with it.
