"""Verify that public Hugging Face assets (datasets/models) are reachable.

Used by `.github/workflows/verify-assets.yml` to confirm the published
datasets/model adapters documented in the SakThai-sakthai-mlops-hf-train-
manual-upload skill are still publicly reachable. Requires no auth: a plain
`curl` HEAD-equivalent status check against each URL.
"""

from __future__ import annotations

import ipaddress
import socket
import subprocess
import sys
import urllib.parse


def verify_url(url: str, resource_name: str) -> bool:
    """Return True if `url` responds with an HTTP 200 status code."""
    print(f"Verifying {resource_name} at {url}...")

    # Prevent option smuggling
    if url.strip().startswith("-"):
        print(f"ERROR: URL {url!r} starts with '-' (option smuggling is blocked).")
        return False

    try:
        parsed = urllib.parse.urlparse(url)
        scheme = parsed.scheme.lower()
        if scheme not in ("http", "https"):
            print(f"ERROR: URL scheme {scheme!r} is not allowed (only HTTP/HTTPS).")
            return False

        host = parsed.hostname
        if not host:
            print("ERROR: URL has no hostname.")
            return False

        # Determine port for resolution and pinning
        port = parsed.port
        if not port:
            port = 443 if scheme == "https" else 80

        # Perform DNS resolution and IP validation (SSRF/DNS Rebinding mitigation)
        addrinfos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
        resolved_ip = None
        for _family, _type, _proto, _canon, sockaddr in addrinfos:
            ip_str = sockaddr[0]
            try:
                ip = ipaddress.ip_address(ip_str)
            except ValueError:
                continue

            # Check if IP is global, multicast or private
            if not ip.is_global or ip.is_multicast:
                print(
                    f"ERROR: Refusing to request non-public address {ip_str} "
                    f"(resolved from {host!r}); private/loopback/link-local/unspecified/multicast/reserved addresses are blocked."
                )
                return False

            if resolved_ip is None:
                resolved_ip = ip_str

        if not resolved_ip:
            print(f"ERROR: No valid public IP resolved for host {host!r}.")
            return False

        # Use curl --resolve to pin host resolution to pre-validated IP
        resolve_arg = f"{host}:{port}:{resolved_ip}"
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--resolve", resolve_arg, url],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
        OSError,
    ) as exc:
        print(f"ERROR: Verification command failed. {exc}")
        return False

    status_code = result.stdout.strip()
    if status_code == "200":
        print(f"SUCCESS: {resource_name} found (HTTP 200).")
        return True
    print(f"FAILURE: {resource_name} not found. HTTP status: {status_code}.")
    return False


def main() -> None:
    urls_to_check = sys.argv[1:]
    if not urls_to_check:
        print("Usage: python3 verify_hf_upload.py <url1> [<url2>...]")
        print(
            "Example: python3 verify_hf_upload.py https://huggingface.co/datasets/my-user/my-dataset"
        )
        sys.exit(1)
        return

    all_successful = True
    for i, url in enumerate(urls_to_check):
        if not verify_url(url, f"Resource #{i + 1}"):
            all_successful = False

    if not all_successful:
        print(
            "\nOne or more verifications failed. Please check the URLs and ensure the assets are public."
        )
        sys.exit(1)
        return

    print("\nAll resources verified successfully.")


if __name__ == "__main__":
    main()
