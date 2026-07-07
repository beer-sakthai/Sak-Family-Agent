#!/usr/bin/env python3
"""Test the 1.5B merged model on HF Inference API and record results."""
import os, json, time, sys

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

# 2) Init client
client = InferenceClient(MODEL, token=hf_token)

# 3) Test prompts
tests = [
    {
        "name": "tool_call_basic",
        "description": "Tool-use intent — ask model to search",
        "messages": [
            {"role": "system", "content": "You are SakThai, an AI assistant with tools: search, read_file, run_command. Use the appropriate tool when asked."},
            {"role": "user", "content": "Search for the latest news about AI"}
        ]
    },
    {
        "name": "instruction_following",
        "description": "Simple instruction — explain transformers",
        "messages": [
            {"role": "system", "content": "You are SakThai, a helpful assistant. Be concise."},
            {"role": "user", "content": "Write a one-sentence summary of how transformers work."}
        ]
    },
    {
        "name": "multi_turn_recall",
        "description": "Remember name across 3 turns",
        "messages": [
            {"role": "system", "content": "You are SakThai, a helpful assistant."},
            {"role": "user", "content": "My name is Beer."},
            {"role": "assistant", "content": "Nice to meet you, Beer! How can I help you today?"},
            {"role": "user", "content": "What's my name?"}
        ]
    },
    {
        "name": "json_output",
        "description": "Structured JSON output",
        "messages": [
            {"role": "system", "content": "You are SakThai. Always respond with valid JSON only, no markdown."},
            {"role": "user", "content": 'List 3 AI frameworks in JSON: {"frameworks": ["name1", "name2", "name3"]}'}
        ]
    },
    {
        "name": "tool_definition",
        "description": "Respond to tool-capable prompt",
        "messages": [
            {"role": "system", "content": "You are SakThai with access to:\n- search(query): Search the web\n- read_file(path): Read a file\n- run_command(command): Execute a shell command"},
            {"role": "user", "content": "Read the file /etc/hostname on my system using read_file."}
        ]
    },
    {
        "name": "context_window",
        "description": "Long context — provide a paragraph then ask",
        "messages": [
            {"role": "system", "content": "You are SakThai. Be concise."},
            {"role": "user", "content": "The transformer architecture introduced in 'Attention Is All You Need' revolutionized NLP by replacing recurrent layers with multi-head self-attention. It uses positional encodings, layer normalization, and feed-forward networks in an encoder-decoder structure. BERT, GPT, and T5 all build on this foundation. What year was the original transformer paper published?"}
        ]
    },
    {
        "name": "general_knowledge",
        "description": "General QA",
        "messages": [
            {"role": "system", "content": "You are SakThai, a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"}
        ]
    }
]

results = []
all_passed = True

for i, test in enumerate(tests):
    print(f"\n{'─'*60}")
    print(f"TEST {i+1}: {test['name']}")
    print(f"  Description: {test['description']}")
    print(f"  Last prompt: {test['messages'][-1]['content'][:80]}")
    
    try:
        start = time.time()
        response = client.chat_completion(
            messages=test["messages"],
            max_tokens=256,
            temperature=0.1,
        )
        elapsed = time.time() - start
        
        choice = response.choices[0]
        content = choice.message.content or ""
        finish = choice.finish_reason
        
        usage = response.usage
        pt = usage.prompt_tokens if usage else None
        ct = usage.completion_tokens if usage else None
        
        result = {
            "name": test["name"],
            "passed": True,
            "response": content,
            "response_length": len(content),
            "finish_reason": finish,
            "latency_seconds": round(elapsed, 2),
            "prompt_tokens": pt,
            "completion_tokens": ct
        }
        
        # Quality checks
        checks = []
        if len(content) > 0:
            checks.append("non_empty")
        if len(content) > 10:
            checks.append("substantial")
        if "beer" in content.lower() and test["name"] == "multi_turn_recall":
            checks.append("name_recall")
        if test["name"] == "json_output":
            try:
                parsed = json.loads(content)
                if "frameworks" in parsed:
                    checks.append("valid_json")
            except:
                pass
        if test["name"] == "general_knowledge" and "paris" in content.lower():
            checks.append("correct_answer")
        if test["name"] == "context_window" and ("2017" in content):
            checks.append("correct_answer")
        
        result["checks"] = checks
        print(f"  ✅ PASS")
        print(f"  Response: {content[:200]}")
        print(f"  Checks: {checks}")
        print(f"  ⏱ {elapsed:.2f}s | 📝 {pt}→{ct} | 🔚 {finish}")
        
    except Exception as e:
        all_passed = False
        result = {
            "name": test["name"],
            "passed": False,
            "error": str(e)
        }
        print(f"  ❌ FAIL: {e}")
    
    results.append(result)

# ---- Summary ----
print(f"\n\n{'='*60}")
print("📊 WORKBENCH TEST SUMMARY — SakThai Context 1.5B")
print(f"{'='*60}")

passed_count = sum(1 for r in results if r.get("passed"))
total = len(results)
print(f"\nResults: {passed_count}/{total} passed")
print()

for r in results:
    status = "✅" if r.get("passed") else "❌"
    name = r["name"].ljust(20)
    lat = f"{r.get('latency_seconds', 0):.1f}s" if r.get("passed") else "  -  "
    tokens = f"{r.get('prompt_tokens','?')}→{r.get('completion_tokens','?')}" if r.get("passed") else "   -   "
    detail = (r.get("checks", [r.get("error","?")]))
    print(f"  {status} {name} ⏱ {lat} 📝 {tokens} ✅ {detail}")

# Save as record
TIMESTAMP = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
record = {
    "test_run": f"workbench-{TIMESTAMP}",
    "model": MODEL,
    "model_id": info.id,
    "pipeline_tag": info.pipeline_tag,
    "downloads": info.downloads,
    "timestamp": TIMESTAMP,
    "results": results,
    "summary": {
        "total": total,
        "passed": passed_count,
        "failed": total - passed_count,
        "all_passed": passed_count == total
    }
}

output_path = "/opt/data/sakthai-1.5b-workbench-test-record.json"
with open(output_path, "w") as f:
    json.dump(record, f, indent=2)

print(f"\n💾 Record saved to: {output_path}")
print(f"🏁 All done.")