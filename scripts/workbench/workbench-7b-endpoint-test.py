#!/usr/bin/env python3
"""Workbench test: 7B merged model via Inference Endpoint."""
import json, time, os, sys
import requests

MODEL = "Nanthasit/sakthai-context-7b-merged"
ENDPOINT_URL = None  # Set dynamically after deployment

# Read endpoint URL from args or env
if len(sys.argv) > 1:
    ENDPOINT_URL = sys.argv[1]
elif "ENDPOINT_URL" in os.environ:
    ENDPOINT_URL = os.environ["ENDPOINT_URL"]
else:
    print("Usage: python3 sakthai-7b-workbench-test.py <endpoint_url>")
    print("Or set ENDPOINT_URL env var")
    sys.exit(1)

TOKEN_PATH = "/opt/data/profiles/sakthai/home/.cache/huggingface/token"
with open(TOKEN_PATH) as f:
    HF_TOKEN = f.read().strip()

HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}

tests = [
    {
        "name": "basic_greeting",
        "desc": "Say hello in one sentence",
        "messages": [
            {"role": "system", "content": "You are SakThai, a helpful assistant. Be concise."},
            {"role": "user", "content": "Say hello in one sentence."}
        ],
        "checks": ["non_empty", "substantial"]
    },
    {
        "name": "tool_call_intent",
        "desc": "Tool-use intent",
        "messages": [
            {"role": "system", "content": "You are SakThai with tools: search(query), read_file(path), run_command(command)."},
            {"role": "user", "content": "Search for the latest AI news"}
        ],
        "checks": ["non_empty", "substantial"]
    },
    {
        "name": "name_recall",
        "desc": "Remember name across 3 turns",
        "messages": [
            {"role": "system", "content": "You are SakThai."},
            {"role": "user", "content": "My name is Beer."},
            {"role": "assistant", "content": "Nice to meet you, Beer!"},
            {"role": "user", "content": "What's my name?"}
        ],
        "checks": ["non_empty", "name_recall"]
    },
    {
        "name": "factual_qa",
        "desc": "Simple factual question",
        "messages": [
            {"role": "system", "content": "You are SakThai. Be concise."},
            {"role": "user", "content": "What is the capital of Japan?"}
        ],
        "checks": ["non_empty", "correct"]
    },
    {
        "name": "json_output",
        "desc": "Structured JSON",
        "messages": [
            {"role": "system", "content": "You are SakThai. Only respond with valid JSON."},
            {"role": "user", "content": 'List 3 ML frameworks: {"frameworks": ["a","b","c"]}'}
        ],
        "checks": ["non_empty", "valid_json"]
    },
    {
        "name": "instruction_following",
        "desc": "Follow formatting instruction",
        "messages": [
            {"role": "system", "content": "You are SakThai. Exactly one sentence."},
            {"role": "user", "content": "Explain what a transformer is."}
        ],
        "checks": ["non_empty", "substantial"]
    },
    {
        "name": "multi_step_reasoning",
        "desc": "Multi-step reasoning",
        "messages": [
            {"role": "system", "content": "You are SakThai, a helpful assistant."},
            {"role": "user", "content": "If you have 3 apples and give away 1, then buy 5 more, how many do you have? Show your work."}
        ],
        "checks": ["non_empty", "substantial"]
    },
    {
        "name": "context_window",
        "desc": "Longer context understanding",
        "messages": [
            {"role": "system", "content": "You are SakThai. Be concise."},
            {"role": "user", "content": "The transformer architecture introduced in 'Attention Is All You Need' revolutionized NLP by replacing recurrent layers with multi-head self-attention. It uses positional encodings, layer normalization, and feed-forward networks in an encoder-decoder structure. BERT, GPT, and T5 all build on this foundation. What year was the original transformer paper published?"}
        ],
        "checks": ["non_empty", "correct_answer"]
    }
]

print(f"🧪 WORKBENCH TEST — SakThai Context 7B")
print(f"   Endpoint: {ENDPOINT_URL}")
print(f"   Model: {MODEL}")
print(f"   Time: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()

results = []
for i, test in enumerate(tests):
    print(f"{'─'*60}")
    print(f"TEST {i+1}: {test['name']} — {test['desc']}")
    print(f"  Turns: {len(test['messages'])}", flush=True)

    try:
        t0 = time.time()
        resp = requests.post(
            f"{ENDPOINT_URL}/v1/chat/completions",
            headers=HEADERS,
            json={
                "model": "tgi",
                "messages": test["messages"],
                "max_tokens": 256,
                "temperature": 0.1,
            },
            timeout=120
        )
        elapsed = time.time() - t0

        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        choice = data["choices"][0]
        content = choice["message"]["content"].strip()
        finish = choice.get("finish_reason", "")
        usage = data.get("usage", {})

        # Run quality checks
        checks = []
        if len(content) > 0:
            checks.append("non_empty")
        if len(content) > 10:
            checks.append("substantial")

        if "beer" in content.lower() and test["name"] == "name_recall":
            checks.append("name_recall")
        if "tokyo" in content.lower() and test["name"] == "factual_qa":
            checks.append("correct")
        if "2017" in content and test["name"] == "context_window":
            checks.append("correct_answer")
        if test["name"] == "json_output":
            try:
                json.loads(content)
                checks.append("valid_json")
            except:
                pass

        result = {
            "name": test["name"],
            "passed": len(checks) > 0,
            "response_preview": content[:200],
            "response_length": len(content),
            "latency_seconds": round(elapsed, 2),
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "finish_reason": finish,
            "checks": checks
        }

        print(f"  {'✅' if result['passed'] else '❌'} Response: {content[:150]}")
        print(f"  ⏱ {elapsed:.2f}s | ✅ {checks} | 🔚 {finish}")
        if result.get("prompt_tokens"):
            print(f"  📝 {result['prompt_tokens']}→{result['completion_tokens']}")

    except Exception as e:
        result = {
            "name": test["name"],
            "passed": False,
            "error": str(e)[:300]
        }
        print(f"  ❌ FAIL: {e}")

    results.append(result)
    sys.stdout.flush()

# Summary
print(f"\n{'='*60}")
passed = sum(1 for r in results if r.get("passed"))
total = len(results)
print(f"📊 WORKBENCH SUMMARY — 7B ({MODEL})")
print(f"\nResults: {passed}/{total} passed")
print()

for r in results:
    status = "✅" if r.get("passed") else "❌"
    name = r["name"].ljust(22)
    lat = f"{r.get('latency_seconds', 0):.1f}s" if r.get("passed") else "  -  "
    detail = str(r.get("checks", r.get("error", "?")[:60]))
    print(f"  {status} {name} ⏱ {lat} {detail}")

# Save record
record = {
    "test_run": f"workbench-{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
    "model": MODEL,
    "endpoint_url": ENDPOINT_URL,
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "results": results,
    "summary": f"{passed}/{total} passed"
}

output_path = "/opt/data/sakthai-7b-workbench-test-record.json"
with open(output_path, "w") as f:
    json.dump(record, f, indent=2)
print(f"\n💾 Saved: {output_path}")
print("🏁 Done.")
