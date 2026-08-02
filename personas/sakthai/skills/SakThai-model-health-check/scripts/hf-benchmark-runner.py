#!/usr/bin/env python3
"""SakThai HF Benchmark Runner — local inference on a Nanthasit model."""
import datetime, json, os, time, yaml, traceback
import torch
from huggingface_hub import HfApi
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "Nanthasit/sakthai-context-0.5b-merged"
TRACKER_PATH = os.path.expanduser("~/profiles/sakthai/cron/hf-benchmarked.json")
TS = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")
REPORT_TS = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

TOOL_PROMPT = """<tools>
[
  {"name": "calculator", "description": "Perform arithmetic calculations",
   "parameters": {"type": "object", "properties": {
     "expression": {"type": "string", "description": "Math expression"},
     "type": {"type": "string", "enum": ["add", "multiply", "divide", "subtract"]}
   }, "required": ["expression", "type"]}},
  {"name": "get_weather", "description": "Get current weather for a city",
   "parameters": {"type": "object", "properties": {
     "location": {"type": "string", "description": "City name"},
     "units": {"type": "string", "enum": ["celsius", "fahrenheit"]}
   }, "required": ["location"]}}
]
</tools>

What is 3 * 12 + 5? Use the calculator tool.

<tool_call>"""

# --- Read tracker ---
tracker = {"version": 2, "created": TS, "last_run": TS, "runs": [], "summary": {}}
if os.path.exists(TRACKER_PATH):
    with open(TRACKER_PATH) as f:
        tracker = json.load(f)

api = HfApi()
token_path = os.path.expanduser("~/.cache/huggingface/token")
token = open(token_path).read().strip() if os.path.exists(token_path) else None

print(f"[{TS}] Benchmarking {MODEL_ID} locally on CPU...")
start = time.time()
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, token=token)
    load_start = time.time()
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, token=token, torch_dtype="auto", low_cpu_mem_usage=True)
    load_time = time.time() - load_start
    print(f"  Model loaded in {load_time:.1f}s")

    inputs = tokenizer(TOOL_PROMPT, return_tensors="pt")
    input_len = inputs.input_ids.shape[1]
    gen_start = time.time()
    with torch.no_grad():
        outputs = model.generate(
            **inputs, max_new_tokens=128, do_sample=True, temperature=0.7,
            pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id)
    gen_time = time.time() - gen_start
    total_time = time.time() - start

    output_ids = outputs[0][input_len:]
    response_text = tokenizer.decode(output_ids, skip_special_tokens=True)
    output_tokens = output_ids.shape[0]
    has_tool_call = "<tool_call>" in response_text or "calculator" in response_text.lower()
    print(f"  Generation: {gen_time:.2f}s, {output_tokens} tokens, tool_call={has_tool_call}")

    result = {
        "timestamp": TS, "model": MODEL_ID, "backend": "transformers-cpu",
        "status": 200, "load_time_s": round(load_time, 2),
        "gen_time_s": round(gen_time, 2), "total_time_s": round(total_time, 2),
        "input_tokens": input_len, "output_tokens": output_tokens,
        "has_tool_call": has_tool_call,
        "response_preview": response_text[:150], "error": None,
        "notes": f"Local CPU inference (fp32). Tool-call prompt with calculator.",
    }

    report = {
        "model": MODEL_ID, "benchmark_ts": REPORT_TS, "backend": "transformers-cpu",
        "prompt_type": "tool_calling", "prompt_length_chars": len(TOOL_PROMPT),
        "total_time_s": round(total_time, 2), "load_time_s": round(load_time, 2),
        "gen_time_s": round(gen_time, 2), "input_tokens": input_len,
        "output_tokens": output_tokens, "has_tool_call": has_tool_call,
        "response": response_text[:500], "device": "cpu", "dtype": str(model.dtype),
    }
    report_path = f".eval_results/benchmark-{TS}.yaml"
    api.upload_file(
        path_or_fileobj=yaml.dump(report, sort_keys=False, default_flow_style=False).encode(),
        path_in_repo=report_path, repo_id=MODEL_ID, repo_type="model", token=token)
    print(f"  Uploaded: {report_path}")
    result["report_url"] = f"https://huggingface.co/{MODEL_ID}/blob/main/{report_path}"

except Exception as e:
    total_time = time.time() - start
    print(f"  FAILED: {e}")
    result = {
        "timestamp": TS, "model": MODEL_ID, "backend": "try-local",
        "status": 0, "total_time_s": round(total_time, 2),
        "error": str(e)[:200], "notes": "Local inference failed.",
    }

tracker["last_run"] = TS
tracker["runs"].append(result)
tracker["summary"] = {
    "last_model": MODEL_ID, "last_status": result.get("status"),
    "last_backend": "transformers-cpu", "total_runs": len(tracker["runs"]),
    "nanthasit_models_on_router": 0,
}
os.makedirs(os.path.dirname(TRACKER_PATH), exist_ok=True)
with open(TRACKER_PATH, "w") as f:
    json.dump(tracker, f, indent=2)

print(f"\n=== DONE === {result.get('status')} — {result.get('output_tokens', 'N/A')} tokens in {result.get('total_time_s', 'N/A')}s")
