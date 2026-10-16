#!/usr/bin/env python3
"""Poll endpoint until running."""

import sys
import time
from typing import Any

# Ensure we can import huggingface_hub
if "/opt/data/.venv/lib/python3.13/site-packages" not in sys.path:
    sys.path.insert(0, "/opt/data/.venv/lib/python3.13/site-packages")

from huggingface_hub import HfApi


def get_token() -> str:
    with open("/opt/data/profiles/sakthai/home/.cache/huggingface/token") as f:
        return f.read().strip()


def poll(api: Any, max_polls: int = 15, sleep_time: int = 30) -> int:
    for i in range(max_polls):
        try:
            eps = [e for e in api.list_inference_endpoints() if "sakthai" in e.name]
            if eps:
                ep = eps[0]
                print(f"Poll {i + 1}: Status={ep.status}, URL={ep.url}", flush=True)
                if ep.status == "running":
                    print("LIVE!", flush=True)
                    return 0
            else:
                print(f"Poll {i + 1}: No endpoint found", flush=True)
        except Exception as e:
            print(f"Poll {i + 1}: Error: {e}", flush=True)
        time.sleep(sleep_time)

    print("TIMEOUT - endpoint never reached running", flush=True)
    return 1


def main() -> None:
    token = get_token()
    api = HfApi(token=token)
    sys.exit(poll(api))


if __name__ == "__main__":
    main()
