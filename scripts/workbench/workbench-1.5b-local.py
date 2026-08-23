#!/usr/bin/env python3
"""Workbench test — load merged 1.5B model, run 6 test prompts, record results."""
import json, time, os, sys
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = "Nanthasit/sakthai-context-1.5b-merged"
OUTPUT = "/opt/data/sakthai-workbench-record.json"

# Load model + tokenizer
print(f"Loading {MODEL}...", flush=True)
start = time.time()
tokenizer = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL,
    trust_remote_code=True,
    torch_dtype=torch.float16,
    device_map="auto",
    low_cpu_mem_usage=True
)
load_time = time.time() - start
print(f"Loaded in {load_time:.1f}s on {model.device}", flush=True)

# Test prompts
tests = [
    {
        "name": "basic_greeting",
        "desc": "Say hello in one sentence",
        "messages": [
            {"role": "system", "content": "You are SakThai, a helpful assistant. Be concise."},
            {"role": "user", "content": "Say hello in one sentence."}
        ]
    },
    {
        "name": "tool_call",
        "desc": "Tool-use intent",
        "messages": [
            {"role": "system", "content": "You are SakThai with tools: search(query), read_file(path), run_command(command)."},
            {"role": "user", "content": "Search for the latest AI news"}
        ]
    },
    {
        "name": "name_recall",
        "desc": "Remember name across 3 turns",
        "messages": [
            {"role": "system", "content": "You are SakThai."},
            {"role": "user", "content": "My name is Beer."},
            {"role": "assistant", "content": "Nice to meet you, Beer!"},
            {"role": "user", "content": "What's my name?"}
        ]
    },
    {
        "name": "factual_qa",
        "desc": "Simple factual question",
        "messages": [
            {"role": "system", "content": "You are SakThai. Be concise."},
            {"role": "user", "content": "What is the capital of Japan?"}
        ]
    },
    {
        "name": "json_output",
        "desc": "Structured JSON",
        "messages": [
            {"role": "system", "content": "You are SakThai. Only respond with valid JSON."},
            {"role": "user", "content": 'List 3 ML frameworks: {"frameworks": ["a","b","c"]}'}
        ]
    },
    {
        "name": "instruction_following",
        "desc": "Follow formatting instruction",
        "messages": [
            {"role": "system", "content": "You are SakThai. Exactly one sentence."},
            {"role": "user", "content": "Explain what a transformer is."}
        ]
    }
]

results = []
for i, test in enumerate(tests):
    print(f"\n--- TEST {i+1}: {test['name']} ---", flush=True)
    
    try:
        prompt = tokenizer.apply_chat_template(
            test["messages"],
            tokenize=False,
            add_generation_prompt=True
        )
        
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        t0 = time.time()
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=256,
                temperature=0.1,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        elapsed = time.time() - t0
        
        input_len = inputs.input_ids.shape[1]
        response = tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True).strip()
        
        prompt_tokens = input_len
        completion_tokens = outputs.shape[1] - input_len
        
        checks = []
        if len(response) > 0:
            checks.append("non_empty")
        if len(response) > 10:
            checks.append("substantial")
        if test["name"] == "name_recall" and "beer" in response.lower():
            checks.append("name_recall")
        if test["name"] == "factual_qa" and "tokyo" in response.lower():
            checks.append("correct")
        if test["name"] == "json_output":
            try:
                json.loads(response)
                checks.append("valid_json")
            except:
                pass
        
        result = {
            "name": test["name"],
            "passed": len(checks) > 0,
            "response_preview": response[:300],
            "response_length": len(response),
            "latency_seconds": round(elapsed, 2),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "checks": checks
        }
        
        print(f"  ✅ {response[:150]}", flush=True)
        print(f"  ⏱ {elapsed:.2f}s | 📝 {prompt_tokens}→{completion_tokens} | ✅ {checks}", flush=True)
        
    except Exception as e:
        result = {"name": test["name"], "passed": False, "error": str(e)[:300]}
        print(f"  ❌ {e}", flush=True)
    
    results.append(result)
    sys.stdout.flush()

# Summary
print(f"\n{'='*50}", flush=True)
print("WORKBENCH TEST — SakThai Context 1.5B", flush=True)
passed = sum(1 for r in results if r.get("passed"))
print(f"Passed: {passed}/{len(results)}", flush=True)
for r in results:
    status = "✅" if r.get("passed") else "❌"
    lat = f"{r.get('latency_seconds',0):.1f}s" if r.get("passed") else "  -  "
    detail = str(r.get("checks", r.get("error","?")))[:60]
    print(f"  {status} {r['name']:<20} ⏱ {lat} {detail}", flush=True)

record = {
    "type": "workbench_local",
    "model": MODEL,
    "load_time_seconds": round(load_time, 1),
    "device": str(model.device),
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "results": results,
    "summary": f"{passed}/{len(results)} passed"
}

with open(OUTPUT, "w") as f:
    json.dump(record, f, indent=2)
print(f"\nSaved to {OUTPUT}", flush=True)