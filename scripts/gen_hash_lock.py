#!/usr/bin/env python3
"""Generate a pip --require-hashes-compatible lockfile, merged across platforms.

Wraps `uv pip compile --generate-hashes`, run once per target platform, and
unions the resulting per-package hash sets into one file so `pip install
--require-hashes -r <output>` works no matter which of the target platforms
it runs on. A single-platform compile only records hashes for wheels that
platform's resolver considered, so installing on a different platform (e.g.
macOS when only Linux was compiled) fails hash verification even though the
package is genuinely available there.

Usage:
    python3 scripts/gen_hash_lock.py <requirements.in> <output.lock> \\
        --platform x86_64-unknown-linux-gnu \\
        --platform aarch64-apple-darwin \\
        --platform x86_64-apple-darwin \\
        --python-version 3.11 \\
        [--index-url URL] [--extra-index-url URL]

Requires `uv` on PATH. Network access needed (queries PyPI / the given index).
"""

import argparse
import re
import subprocess
import sys
from collections import OrderedDict
from urllib.parse import urlparse


def parse(text):
    """Parse `uv pip compile --generate-hashes` output into
    {name: {"version": v, "hashes": set(), "via": [line, ...]}}."""
    lines = text.splitlines()
    entries = OrderedDict()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line and not line[0].isspace() and not line.startswith("#") and "==" in line:
            name, version = line.split("\\")[0].strip().split("==")
            name, version = name.strip().lower(), version.strip()
            hashes, via = set(), []
            i += 1
            while i < len(lines) and lines[i][:1] in (" ", "\t"):
                stripped = lines[i].strip()
                if stripped.startswith("--hash="):
                    hashes.add(stripped.split("--hash=")[1].rstrip("\\").strip())
                elif stripped.startswith("# via"):
                    via.append(stripped)
                i += 1
            if name in entries and entries[name]["version"] != version:
                print(
                    f"WARNING: {name} resolved to {entries[name]['version']} on one "
                    f"platform and {version} on another — same lockfile can't cover both.",
                    file=sys.stderr,
                )
            entries.setdefault(name, {"version": version, "hashes": set(), "via": via})
            entries[name]["hashes"] |= hashes
        else:
            i += 1
    return entries


def _validate_req_file(req_file):
    if not req_file:
        raise ValueError("req_file must not be empty")
    with open(req_file, "r", encoding="utf-8"):
        pass


def _validate_constraints(constraints):
    for c in constraints or []:
        if not c:
            raise ValueError("constraint path must not be empty")
        with open(c, "r", encoding="utf-8"):
            pass


def _validate_platform(platform):
    # Target triples and similar platform tags (e.g. x86_64-unknown-linux-gnu)
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", platform or ""):
        raise ValueError(f"invalid platform value: {platform!r}")


def _validate_python_version(python_version):
    if not re.fullmatch(r"\d+(\.\d+){1,2}", python_version or ""):
        raise ValueError(f"invalid python version: {python_version!r}")


def _validate_url(url, field_name):
    parsed = urlparse(url or "")
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"invalid {field_name}: {url!r}")


def compile_for_platform(
    req_file, platform, python_version, index_url, extra_index_url, index_strategy, constraints
):
    _validate_req_file(req_file)
    _validate_platform(platform)
    _validate_python_version(python_version)
    if index_url:
        _validate_url(index_url, "index-url")
    for url in extra_index_url or []:
        _validate_url(url, "extra-index-url")
    _validate_constraints(constraints)

    cmd = [
        "uv",
        "pip",
        "compile",
        req_file,
        "--generate-hashes",
        "--python-platform",
        platform,
        "--python-version",
        python_version,
    ]
    if index_url:
        cmd += ["--index-url", index_url]
    for url in extra_index_url or []:
        cmd += ["--extra-index-url", url]
    if index_strategy:
        cmd += ["--index-strategy", index_strategy]
    for c in constraints or []:
        cmd += ["--constraints", c]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise SystemExit(f"uv pip compile failed for platform {platform}")
    return result.stdout


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("req_file")
    p.add_argument("output")
    p.add_argument("--platform", action="append", required=True, dest="platforms")
    p.add_argument("--python-version", default="3.11")
    p.add_argument("--index-url")
    p.add_argument("--extra-index-url", action="append")
    p.add_argument("--index-strategy", choices=["first-index", "unsafe-best-match"])
    p.add_argument(
        "--constraint",
        action="append",
        dest="constraints",
        help="Constraints file(s) bounding transitive versions (e.g. to match an "
        "already-pinned package from an earlier install layer) without adding "
        "them as top-level requirements.",
    )
    args = p.parse_args()

    merged = OrderedDict()
    per_platform_names = []
    for platform in args.platforms:
        print(f"Resolving for {platform}...", file=sys.stderr)
        out = compile_for_platform(
            args.req_file,
            platform,
            args.python_version,
            args.index_url,
            args.extra_index_url,
            args.index_strategy,
            args.constraints,
        )
        entries = parse(out)
        per_platform_names.append(set(entries))
        for name, data in entries.items():
            merged.setdefault(name, {"version": data["version"], "hashes": set()})
            merged[name]["hashes"] |= data["hashes"]

    base = per_platform_names[0]
    for platform, names in zip(args.platforms[1:], per_platform_names[1:], strict=True):
        if base - names or names - base:
            print(
                f"NOTE: package set differs for {platform} vs {args.platforms[0]}: "
                f"only-in-first={sorted(base - names)} only-in-{platform}={sorted(names - base)}",
                file=sys.stderr,
            )

    with open(args.output, "w") as f:
        f.write(
            "# Hash-locked pip requirements. Generated with:\n"
            f"#   python3 scripts/gen_hash_lock.py {args.req_file} {args.output} "
            + " ".join(f"--platform {pl}" for pl in args.platforms)
            + f" --python-version {args.python_version}"
            + (f" --index-url {args.index_url}" if args.index_url else "")
            + "".join(f" --extra-index-url {u}" for u in (args.extra_index_url or []))
            + (f" --index-strategy {args.index_strategy}" if args.index_strategy else "")
            + "".join(f" --constraint {c}" for c in (args.constraints or []))
            + "\n"
            "# Do not hand-edit — regenerate with the command above when the pinned\n"
            "# version bumps, and re-verify a couple of hashes against PyPI's own\n"
            "# published digests before committing (`curl -s https://pypi.org/pypi/<pkg>/<ver>/json`).\n\n"
        )
        for name in sorted(merged):
            data = merged[name]
            f.write(f"{name}=={data['version']} \\\n")
            hashes = sorted(data["hashes"])
            for j, h in enumerate(hashes):
                sep = " \\\n" if j < len(hashes) - 1 else "\n"
                f.write(f"    --hash={h}{sep}")
            f.write("\n")
    print(f"Wrote {len(merged)} packages to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
