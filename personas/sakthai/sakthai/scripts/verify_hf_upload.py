"""Verify that public Hugging Face assets (datasets/models) are reachable.

Used by `.github/workflows/verify-assets.yml` to confirm the published
datasets/model adapters documented in the SakThai-sakthai-mlops-hf-train-
manual-upload skill are still publicly reachable. Requires no auth: a plain
`curl` HEAD-equivalent status check against each URL.
"""

from __future__ import annotations

import subprocess
import sys


def verify_url(url: str, resource_name: str) -> bool:
    """Return True if `url` responds with an HTTP 200 status code."""
    print(f"Verifying {resource_name} at {url}...")
    try:
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", url],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
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
