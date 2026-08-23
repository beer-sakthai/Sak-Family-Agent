#!/usr/bin/env python3
"""HF Jobs workbench test: SakThai Context 7B merged model, 4-bit, T4 GPU."""

import json, time, os, sys
import torch

MODEL = "Nanthasit/sakthai-context-7b-merged"
HF_TOKEN = os.environ.get("HF_TOKEN", "")
os.environ["HF_TOKEN"] = HF_TOKEN
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

print("=" * 60)
print(f"WORKBENCH TEST — SakThai Context 7B")
print(f"Model: {MODEL}")
print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NONE'}")
print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB" if torch.cuda.is_available() else "N/A")
print(f"Time: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print("=" * 60)
sys.stdout.flush()

# Load model with 4-bit quantization
print("\n📥 Loading model in 4-bit...", flush=True)
t0 = time.time()
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
)

tokenizer = AutoTokenizer.from_pretrained(MODEL, token=HF_TOKEN)
model = AutoModelForCausalLM.from_pretrained(
    MODEL,
    quantization_config=bnb_config,
    device_map="auto",
    torch_dtype=torch.bfloat16,
    token=HF_TOKEN,
    trust_remote_code=True,
)
load_time = time.time() - t0
print(f"✅ Loaded in {load_time:.1f}s on {model.device}", flush=True)
print(f"   VRAM: {torch.cuda.memory_allocated() / 1e9:.2f}GB used", flush=True)

# Tests
tests = [
    {"name": "basic_greeting", "desc": "Say hello",
     "messages": [
         {"role": "system", "content": "You are SakThai, a helpful assistant. Be concise."},
         {"role": "user", "content": "Say hello in one sentence."}
     ]},
    {"name": "tool_call_intent", "desc": "Tool-use intent",
     "messages": [
         {"role": "system", "content": "You are SakThai with tools: search(query), read_file(path), run_command(command)."},
         {"role": "user", "content": "Search for the latest AI news"}
     ]},
    {"name": "name_recall", "desc": "Remember name across 3 turns",
     "messages": [
         {"role": "system", "content": "You are SakThai."},
         {"role": "user", "content": "My name is Beer."},
         {"role": "assistant", "content": "Nice to meet you, Beer!"},
         {"role": "user", "content": "What's my name?"}
     ]},
    {"name": "factual_qa", "desc": "Capital of Japan",
     "messages": [
         {"role": "system", "content": "You are SakThai. Be concise."},
         {"role": "user", "content": "What is the capital of Japan?"}
     ]},
    {"name": "json_output", "desc": "Structured JSON",
     "messages": [
         {"role": "system", "content": "You are SakThai. Respond only with valid JSON."},
         {"role": "user", "content": 'List 3 ML frameworks: {"frameworks": ["a","b","c"]}'}
     ]},
    {"name": "instruction_following", "desc": "One sentence only",
     "messages": [
         {"role": "system", "content": "You are SakThai. Exactly one sentence."},
         {"role": "user", "content": "Explain what a transformer is."}
     ]},
    {"name": "multi_step_reasoning", "desc": "Math reasoning",
     "messages": [
         {"role": "system", "content": "You are SakThai, a helpful assistant."},
         {"role": "user", "content": "If you have 3 apples and give away 1, then buy 5 more, how many do you have? Show your work."}
     ]},
    {"name": "context_window", "desc": "Recall from context",
     "messages": [
         {"role": "system", "content": "You are SakThai."},
         {"role": "user", "content": "'Attention Is All You Need' introduced the transformer architecture with multi-head self-attention, positional encodings, and encoder-decoder structure. BERT, GPT, T5 build on it. What year was the paper published?"}
     ]},
]

results = []
for i, test in enumerate(tests):
    print(f"\n{'─'*60}", flush=True)
    print(f"TEST {i+1}: {test['name']} — {test['desc']}", flush=True)

    try:
        prompt = tokenizer.apply_chat_template(
            test["messages"], tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        t1 = time.time()
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=256,
                temperature=0.1,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
            )
        elapsed = time.time() - t1

        input_len = inputs.input_ids.shape[1]
        response = tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True).strip()
        prompt_tokens = input_len
        completion_tokens = outputs.shape[1] - input_len

        # Quality checks
        checks = []
        if len(response) > 0:    checks.append("non_empty")
        if len(response) > 10:   checks.append("substantial")
        if test["name"] == "name_recall" and "beer" in response.lower():
            checks.append("name_recall")
        if test["name"] == "factual_qa" and "tokyo" in response.lower():
            checks.append("correct")
        if test["name"] == "context_window" and "2017" in response:
            checks.append("correct_answer")
        if test["name"] == "json_output":
            try:
                json.loads(response)
                checks.append("valid_json")
            except:
                pass
        if test["name"] == "multi_step_reasoning":
            if any(c in response for c in ["7", "seven"]) and ("apple" in response.lower()):
                checks.append("correct_answer")

        passed = len(response) > 0  # at minimum non-empty
        result = {
            "name": test["name"], "passed": passed,
            "response_preview": response[:200],
            "response_length": len(response),
            "latency_seconds": round(elapsed, 2),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "checks": checks,
        }
        status = "✅" if passed else "❌"
        print(f"  {status} {response[:120]}", flush=True)
        print(f"  ⏱ {elapsed:.2f}s | 📝 {prompt_tokens}→{completion_tokens} | ✅ {checks}", flush=True)

    except Exception as e:
        result = {"name": test["name"], "passed": False, "error": str(e)[:300]}
        print(f"  ❌ {e}", flush=True)

    results.append(result)
    sys.stdout.flush()

# Summary
print(f"\n{'='*60}", flush=True)
passed = sum(1 for r in results if r.get("passed"))
total = len(results)
print(f"📊 7B WORKBENCH SUMMARY: {passed}/{total} passed", flush=True)
for r in results:
    status = "✅" if r.get("passed") else "❌"
    lat = f"{r.get('latency_seconds',0):.1f}s" if r.get("passed") else "  -  "
    detail = str(r.get("checks", r.get("error","?")[:60]))
    print(f"  {status} {r['name']:<22} ⏱ {lat} {detail}", flush=True)

# Save record
record = {
    "type": "workbench_hf_jobs",
    "model": MODEL,
    "load_time_seconds": round(load_time, 1),
    "device": str(model.device),
    "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
    "vram_used_gb": round(torch.cuda.memory_allocated() / 1e9, 2) if torch.cuda.is_available() else 0,
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "results": results,
    "summary": f"{passed}/{total} passed",
}

record_path = "/tmp/sakthai-7b-workbench-record.json"
with open(record_path, "w") as f:
    json.dump(record, f, indent=2)
print(f"\n💾 Saved: {record_path}", flush=True)

# Upload record to HF repo
try:
    from huggingface_hub import HfApi, login
    login(token=HF_TOKEN)
    api = HfApi()
    api.upload_file(
        path_or_fileobj=record_path,
        path_in_repo=f"eval/workbench-7b-{time.strftime('%Y-%m-%d')}.json",
        repo_id="Nanthasit/sakthai-context-7b-merged",
        repo_type="model",
    )
    print(f"📤 Uploaded to HF repo", flush=True)
except Exception as e:
    print(f"⚠️ Upload failed: {e}", flush=True)

print("\n🏁 Done.", flush=True)
