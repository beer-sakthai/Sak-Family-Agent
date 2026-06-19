# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "huggingface_hub>=0.27",
# ]
# ///
"""
Deploy the SakThai model as an OpenAI-compatible HF Inference Endpoint (TGI).

This is the cloud path: TGI exposes a `/v1/chat/completions` API, so the agent's
existing OpenAI provider can talk to it with zero code changes — just point
`OPENAI_API_BASE` at the endpoint and `OPENAI_API_KEY` at your HF token.

IMPORTANT — billing: a running endpoint costs money continuously. This script
**dry-runs by default** and only prints the plan. Pass `--create` to actually
provision it. TGI serves a full model, not a bare PEFT adapter, so deploy a
*merged* repo (see export_ollama.py for merging, then `hf upload` the result).

Dry run (safe, no cost):
    uv run training/serving/deploy_hf_endpoint.py --repo Nanthasit/sakthai-toolcalling-1.5b-merged

Actually create it (billable):
    HF_TOKEN=... uv run training/serving/deploy_hf_endpoint.py \
        --repo Nanthasit/sakthai-toolcalling-1.5b-merged --create

Then run the agent against it:
    export OPENAI_API_BASE="https://<endpoint>.endpoints.huggingface.cloud/v1"
    export OPENAI_API_KEY="$HF_TOKEN"
    sakthai run --provider openai --model tgi "Remember I prefer dark mode"
"""
import argparse
import os


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="merged model repo id to serve")
    ap.add_argument("--name", default="sakthai-toolcalling", help="endpoint name")
    ap.add_argument("--instance", default="nvidia-l4", help="instance type")
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--create", action="store_true", help="actually provision (BILLABLE)")
    args = ap.parse_args()

    plan = (
        f"  endpoint name : {args.name}\n"
        f"  serving repo  : {args.repo}\n"
        f"  framework     : TGI (text-generation-inference), OpenAI-compatible /v1\n"
        f"  instance      : {args.instance} @ {args.region}\n"
    )

    if not args.create:
        print("== DRY RUN (no endpoint created). Plan:\n" + plan)
        print("Re-run with --create and HF_TOKEN set to provision (this incurs cost).")
        return

    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if not token:
        raise SystemExit("HF_TOKEN not set — required to create an endpoint.")

    from huggingface_hub import create_inference_endpoint

    print("== Creating endpoint (BILLABLE):\n" + plan)
    endpoint = create_inference_endpoint(
        name=args.name,
        repository=args.repo,
        framework="pytorch",
        task="text-generation",
        accelerator="gpu",
        instance_size="x1",
        instance_type=args.instance,
        region=args.region,
        vendor="aws",
        type="protected",
        custom_image={
            "health_route": "/health",
            "url": "ghcr.io/huggingface/text-generation-inference:latest",
            "env": {"MAX_INPUT_TOKENS": "3072", "MAX_TOTAL_TOKENS": "4096"},
        },
        token=token,
    )
    print("== Waiting for endpoint to be running...")
    endpoint.wait()
    print(f"== Running at: {endpoint.url}")
    print(
        "\nWire the agent up:\n"
        f'  export OPENAI_API_BASE="{endpoint.url}/v1"\n'
        '  export OPENAI_API_KEY="$HF_TOKEN"\n'
        '  sakthai run --provider openai --model tgi "Remember I prefer dark mode"\n'
    )


if __name__ == "__main__":
    main()
