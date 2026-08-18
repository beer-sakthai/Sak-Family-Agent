#!/usr/bin/env python3
"""Test the 1.5B merged model on HF Inference API and record results."""
import json
import os
import time

TOKEN_PATH = "/opt/data/profiles/sakthai/home/.cache/huggingface/token"
with open(TOKEN_PATH) as f:
    hf_token = f.read().strip()

os.environ["HF_TOKEN"] = hf_token
from huggingface_hub import InferenceClient, login, HfApi
login(token=hf_token)

MODEL = "Nanthasit/sakthai-context-1.5b-merged"

# 1) Verify model exists
api = HfApi()
info = api.model_info(MODEL)
print(f"✅ Model: {MODEL}")
print(f"   Pipeline: {info.pipeline_tag} | Downloads: {info.downloads} | Likes: {info.likes}")
print()

import os, json, time, sys


def _get_hf_token() -> str | None:
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if token and token.strip():
        return token.strip()
    default_token_path = os.path.expanduser("~/.cache/huggingface/token")
    if os.path.exists(default_token_path):
        try:
            with open(default_token_path) as f:
                content = f.read().strip()
                if content:
                    return content
        except OSError:
            pass
    return None


hf_token = _get_hf_token()
if hf_token:
    os.environ["HF_TOKEN"] = hf_token

from huggingface_hub import InferenceClient, login, HfApi

if hf_token:
    login(token=hf_token)
