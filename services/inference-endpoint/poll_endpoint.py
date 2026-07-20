#!/usr/bin/env python3
"""Poll endpoint until running."""

import sys
import time

sys.path.insert(0, "/opt/data/.venv/lib/python3.13/site-packages")
from huggingface_hub import HfApi

token = open("/opt/data/profiles/sakthai/home/.cache/huggingface/token").read().strip()
api = HfApi(token=token)

for i in range(15):
    try:
        eps = [e for e in api.list_inference_endpoints() if "sakthai" in e.name]
        if eps:
            ep = eps[0]
            print(f"Poll {i + 1}: Status={ep.status}, URL={ep.url}", flush=True)
            if ep.status == "running":
                print("LIVE!", flush=True)
                sys.exit(0)
        else:
            print(f"Poll {i + 1}: No endpoint found", flush=True)
    except Exception as e:
        print(f"Poll {i + 1}: Error: {e}", flush=True)
    time.sleep(30)

print("TIMEOUT - endpoint never reached running", flush=True)
sys.exit(1)
