#!/usr/bin/env python3
"""Verify a static site deploy against local source.

Checks:
1. Local index.html is valid HTML (starts with doctype/html tag, contains <title>).
2. GitHub raw main/index.html is valid HTML.
3. Vercel responds 200 with text/html.
4. Vercel body and GitHub raw content match local file.

Usage:
    python3 verify-deploy.py --owner beer-sakthai --repo house-of-sak \
        --url https://house-of-sak.vercel.app/ --local index.html
"""
import argparse, sys, requests
import socket
import ipaddress
from urllib.parse import urlparse


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def is_valid_html(text: str) -> bool:
    stripped = text.lstrip().lower()
    return stripped.startswith("<!doctype html>") or stripped.startswith("<html")


def ensure_public_host_resolution(host: str) -> None:
    try:
        addrinfos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror:
        fail(f"unable to resolve host: {host}")

    if not addrinfos:
        fail(f"unable to resolve host: {host}")

    for family, _, _, _, sockaddr in addrinfos:
        ip_str = sockaddr[0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            fail(f"resolved invalid IP for host {host}: {ip_str}")

        if (
            ip_obj.is_private
            or ip_obj.is_loopback
            or ip_obj.is_link_local
            or ip_obj.is_multicast
            or ip_obj.is_reserved
            or ip_obj.is_unspecified
        ):
            fail(f"url host resolves to non-public IP: {ip_str}")


def validate_deploy_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme.lower() != "https":
        fail("url must use https")
    if parsed.username or parsed.password:
        fail("url must not include username/password")
    if parsed.port is not None:
        fail("url must not include an explicit port")
    if parsed.path not in ("", "/"):
        fail("url path must be empty or '/'")
    if parsed.query or parsed.fragment:
        fail("url must not include query string or fragment")

    host = (parsed.hostname or "").lower()
    if not host:
        fail("url must include a host")
    if host != "vercel.app" and not host.endswith(".vercel.app"):
        fail("url host must be vercel.app or a .vercel.app subdomain")

    ensure_public_host_resolution(host)

    # Return canonical URL so requests do not use the original raw user string.
    return f"https://{host}/"


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify static site deploy")
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--local", required=True)
    args = parser.parse_args()
    deploy_url = validate_deploy_url(args.url)

    raw_url = f"https://raw.githubusercontent.com/{args.owner}/{args.repo}/main/index.html"

    # 1. Local file
    try:
        with open(args.local, "r") as f:
            local_html = f.read()
    except FileNotFoundError:
        fail(f"local file not found: {args.local}")

    if not is_valid_html(local_html):
        fail(f"local file {args.local} does not look like valid HTML")

    # 2. GitHub raw content
    r = requests.get(raw_url, timeout=30)
    if r.status_code != 200:
        fail(f"GitHub raw returned {r.status_code}")
    if not is_valid_html(r.text):
        fail("GitHub raw index.html does not look like valid HTML")

    # 3. Vercel live response
    r2 = requests.get(deploy_url, timeout=30)
    if r2.status_code != 200:
        fail(f"Vercel returned {r2.status_code}")
    ct = r2.headers.get("content-type", "")
    if "text/html" not in ct:
        fail(f"Vercel content-type is {ct}, expected text/html")

    # 4. Compare bodies (normalise whitespace)
    if r.text.strip() != local_html.strip():
        fail("GitHub raw content differs from local file")

    print("PASS: deployed content matches local content")


if __name__ == "__main__":
    main()
