#!/usr/bin/env python3
"""
verify-file-bytes.py — Display-layer redaction detector.

Verifies current file bytes against git HEAD and flags potential
display-layer transformations (token redaction, backslash doubling).

The display layer can transform content in conversation output:
  - $GITHUB_TOKEN -> ***  (token redaction)
  - <token> -> ***        (placeholder redaction)
  - \\ -> \\\\               (backslash escaping)
  - backticks consumed as markdown formatting

Use this BEFORE any content-modifying action motivated by a perceived
issue detected through read_file, grep, cat, or search_files.

Usage:
    verify-file-bytes.py <file>                          show hex for all lines
    verify-file-bytes.py <file> --line N                 show hex for line N (1-indexed)
    verify-file-bytes.py <file> --search "text"          find and hex-dump lines
    verify-file-bytes.py <file> --git-diff               byte diff current vs HEAD
    verify-file-bytes.py <file> --line N --expect "\\n"   verify line contains exact bytes

Exit codes:
    0  all checks passed (or info-only mode)
    1  issues found (redaction, git mismatch, or no match for --expect)
    2  file not found or not readable
"""

import argparse
import os
import subprocess
import sys


def hex_dump(data: bytes, label: str = "") -> None:
    """Print od -A x -t x1z style hex dump."""
    if label:
        print(f"--- {label} ---")
    for i in range(0, len(data), 16):
        chunk = data[i:i + 16]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        offset = f"{i:06x}"
        print(f"{offset} {hex_part:<48s}  >{ascii_part}<")
    print()


def get_git_version(path: str) -> bytes | None:
    """Get file content from git HEAD, or None if not available."""
    try:
        abs_path = os.path.abspath(path)
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return None
        repo_root = result.stdout.strip()
        rel_path = os.path.relpath(abs_path, repo_root)
        result = subprocess.run(
            ["git", "show", f"HEAD:{rel_path}"],
            capture_output=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        return None


def read_file_bytes(path: str) -> bytes:
    """Read file as raw bytes."""
    with open(path, "rb") as f:
        return f.read()


def redaction_risk_patterns(data: bytes) -> list[str]:
    """Check for patterns the display layer might redact."""
    warnings = []
    patterns = {
        b"$GITHUB_TOKEN": "$GITHUB_TOKEN present (may display as ***)",
        b"$GH_TOKEN": "$GH_TOKEN present (may display as ***)",
        b"<token>": "<token> present (may display as ***)",
        b"$API_KEY": "$API_KEY present (may display as ***)",
        b"$SECRET": "$SECRET present (may display as ***)",
        b"$PAT": "$PAT present (may display as ***)",
        b"$ACCESS_TOKEN": "$ACCESS_TOKEN present (may display as ***)",
        b"$TOKEN": "$TOKEN present (may display as ***)",
    }
    for pattern, warning in patterns.items():
        if pattern in data:
            warnings.append(warning)
    return warnings


def check_backslash_doubling(path: str, data: bytes) -> list[str]:
    """Check for lines where read_file would double backslashes."""
    warnings = []
    lines = data.split(b"\n")
    for i, line in enumerate(lines, 1):
        bs_count = line.count(b"\\")
        if bs_count > 0 and len(warnings) < 5:
            preview = line[:100].decode("utf-8", errors="replace")
            warnings.append(
                f"  Line {i}: {bs_count} backslash(es) — read_file will show "
                f"double (\\\\n → \\\\\\\\n). Raw: {preview!r}"
            )
    if len(warnings) == 5 and any(line.count(b"\\") > 0 for line in lines[5:]):
        remaining = sum(1 for line in lines[5:] if line.count(b"\\") > 0)
        warnings.append(f"  ... and {remaining} more line(s) with backslashes")
    return warnings


def main():
    parser = argparse.ArgumentParser(
        description="Verify file bytes against display-layer evidence.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("file", help="Path to the file to inspect")
    parser.add_argument("--line", type=int, default=None,
                        help="Show hex for a specific line (1-indexed)")
    parser.add_argument("--search", type=str, default=None,
                        help="Find lines containing this substring and dump their hex")
    parser.add_argument("--git-diff", action="store_true",
                        help="Show byte-for-byte diff between current file and git HEAD")
    parser.add_argument("--expect", type=str, default=None,
                        help="With --line: verify line contains exact bytes. "
                             "Use \\n for newline, \\r for CR, \\t for tab.")
    parser.add_argument("--all", action="store_true",
                        help="Show hex for all lines")

    args = parser.parse_args()

    # Validate file
    target = os.path.expanduser(args.file)
    if not os.path.isfile(target):
        print(f"ERROR: File not found: {target}", file=sys.stderr)
        sys.exit(2)

    try:
        data = read_file_bytes(target)
    except PermissionError:
        print(f"ERROR: Permission denied: {target}", file=sys.stderr)
        sys.exit(2)
    except OSError as e:
        print(f"ERROR: Cannot read {target}: {e}", file=sys.stderr)
        sys.exit(2)

    file_size = len(data)
    lines = data.split(b"\n")
    print(f"File: {target}")
    print(f"Size: {file_size} bytes, {len(lines)} lines")
    print()

    # Redaction risk scan
    redaction_warnings = redaction_risk_patterns(data)
    if redaction_warnings:
        print("!!! DISPLAY-LAYER REDACTION RISK !!!")
        print("These patterns may be redacted (shown as ***) in conversation output:")
        for w in redaction_warnings:
            print(f"  - {w}")
        print()
        print("  --> Use the hex dumps below to verify what's ACTUALLY in the file.")
        print()

    # Backslash doubling check
    bs_warnings = check_backslash_doubling(target, data)
    if bs_warnings:
        print("!!! BACKSLASH DOUBLING RISK !!!")
        print("read_file displays doubled backslashes (\\n -> \\\\n):")
        for w in bs_warnings:
            print(w)
        print()

    # Mode: --search
    if args.search:
        search_bytes = args.search.encode("utf-8")
        found = False
        for i, line in enumerate(lines, 1):
            if search_bytes in line:
                found = True
                hex_dump(line, label=f"Line {i} (match for {args.search!r})")
        if not found:
            print(f"No lines contain {args.search!r}")
            print(f"  (Display layer may show *** — the actual bytes may differ.)")
            sys.exit(0)

    # Mode: --git-diff
    if args.git_diff:
        git_content = get_git_version(target)
        if git_content is None:
            print("NOTE: Not a git repository or file not tracked — skipping git diff.")
        else:
            git_bytes = git_content
            if data == git_bytes:
                print("GIT DIFF: Current file matches HEAD (no changes).")
            else:
                git_lines = git_bytes.split(b"\n")
                data_lines = data.split(b"\n")
                max_lines = max(len(git_lines), len(data_lines))
                print(f"GIT DIFF: Current file DIFFERS from HEAD "
                      f"({len(git_lines)} vs {len(data_lines)} lines)")
                print()
                diffs = 0
                for i in range(max_lines):
                    old = git_lines[i] if i < len(git_lines) else b""
                    new = data_lines[i] if i < len(data_lines) else b""
                    if old != new:
                        if diffs < 10:
                            hex_dump(old, label=f"HEAD:L{i+1}")
                            hex_dump(new, label=f"CURRENT:L{i+1}")
                            diffs += 1
                        else:
                            diffs += 1
                if diffs > 10:
                    print(f"... and {diffs - 10} more differing line(s)")
                sys.exit(1)

    # Mode: --line [--expect]
    if args.line is not None:
        line_idx = args.line - 1
        if line_idx < 0 or line_idx >= len(lines):
            print(f"ERROR: Line {args.line} does not exist (file has {len(lines)} lines)")
            sys.exit(2)
        line = lines[line_idx]
        hex_dump(line, label=f"Line {args.line}")

        if args.expect is not None:
            expected = args.expect.encode("utf-8").decode("unicode_escape").encode("latin-1")
            if expected in line:
                print(f"MATCH: Line {args.line} contains expected bytes "
                      f"{args.expect!r}")
                sys.exit(0)
            else:
                print(f"MISMATCH: Line {args.line} does NOT contain "
                      f"expected bytes {args.expect!r}")
                print(f"  Expected hex: {' '.join(f'{b:02x}' for b in expected)}")
                sys.exit(1)

    # Mode: --all (default if nothing else specified)
    if args.all or (args.line is None and not args.search and not args.git_diff):
        for i, line in enumerate(lines, 1):
            hex_dump(line, label=f"Line {i}")

    # Summary
    if not redaction_warnings and not bs_warnings:
        print("No display-layer issues detected in file content.")
    else:
        print(f"Found {len(redaction_warnings)} redaction risk(s) and "
              f"{len(bs_warnings)} backslash-doubling line(s).")
        print("The file content is correct — these are display warnings, not file errors.")


if __name__ == "__main__":
    main()
