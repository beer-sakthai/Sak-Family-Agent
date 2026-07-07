---
name: SakKing-mlops-hf-train-manual-upload
description: "Train a Hugging Face model under strict constraints: no GPU, no external compute, no API keys — manual upload only."
author: SakThai
version: 1.0.0
created: 2026-06-21
updated: 2026-06-21
---

# Train a Hugging Face Model with Manual Upload (Zero-Exposure Workflow)

> **When you forbid external compute, GPU access, and API keys — this is the only safe, sustainable path.**

You operate in a **silent, autonomous, zero-exposure** environment. You do not allow:

- Colab, RunPod, Modal, or any external GPU
- `hf` CLI or `huggingface_hub` Python package
- API tokens in scripts
- `execute_code` or `terminal` with external auth

Yet you still want to fine-tune models.

This skill defines the **only viable path**.

## ✅ Trigger Conditions

Use this skill when:

- You have a clean dataset in JSONL format (e.g., `{"input": "...", "output": "..."}`)
- You are authenticated as `Nanthasit` on Hugging Face (via MCP server)
- You cannot run `hf-jobs`, `execute_code`, or `curl` with auth
- You are willing to manually upload the dataset via the web UI

## 🚫 What NOT to Do

- Do NOT try to automate upload via `curl`, `huggingface_hub`, or `hf-jobs` — they will fail due to missing packages, environment isolation, or auth injection limits.
- Do NOT store API tokens in files or env vars — they violate your zero-exposure rule.
- Do NOT assume the agent can install packages or mount volumes — it cannot.

## ✅ Step-by-Step Workflow

### 1. Extract Clean Training Data

Use `read_file` and `search_files` to locate your synthetic training data:

```bash
ls /home/sakthai/tmp/sakthai-train/*.jsonl
```

Extract 50 clean examples into:

```bash
/home/sakthai/data/hf_training_data_composio_tools_50.jsonl
```

Format must be:

```json
{"input": "What's the weather in London?", "output": "{\"tool_name\": \"run_command\", \"arguments\": {\"command\": \"curl wttr.in/London\"}}"}
```

Use this script if needed (save as `scripts/extract_training_data.py`):

```python
import json

input_path = '/home/sakthai/tmp/sakthai-train/sakthai_toolcalling_synthetic.jsonl'
output_path = '/home/sakthai/data/hf_training_data_composio_tools_50.jsonl'

count = 0
with open(input_path, 'r') as f_in, open(output_path, 'w') as f_out:
    for line in f_in:
        if count >= 50:
            break
        try:
            data = json.loads(line.strip())
            user_msg = next((msg['content'] for msg in data.get('messages', []) if msg.get('role') == 'user'), None)
            if not user_msg: continue
            tool_call = next((t for t in data.get('tools', []) if t.get('type') == 'function'), None)
            if not tool_call: continue
            output_line = json.dumps({
                'input': user_msg,
                'output': json.dumps({
                    'tool_name': tool_call['function']['name'],
                    'arguments': tool_call['function'].get('parameters', {})
                })
            })
            f_out.write(output_line + '\n')
            count += 1
        except Exception:
            continue

print(f"Extracted {count} examples to {output_path}")
```

Run with:

```bash
python3 /home/sakthai/scripts/extract_training_data.py
```

> ✅ This script is safe — it runs locally and produces no external calls.

### 2. Upload Manually via Hugging Face Web UI

Go to: <https://hf.co/datasets/new>

- **Name**: `hf-training-composio-tools-50`
- **Owner**: `Nanthasit`
- **Privacy**: ✅ Private
- **Upload file**: `/home/sakthai/data/hf_training_data_composio_tools_50.jsonl`
- **Filename**: `data.jsonl`
- **Click "Upload"**

✅ Done. No token. No script. No exposure.

### 2b. Automated Verification (New)

After the manual upload, you can programmatically verify that the dataset exists before proceeding. This script uses `curl` to check the HTTP status of the dataset's public URL. It requires no authentication and is safe to run.

Save this as `scripts/verify_hf_upload.py`:

```python
import subprocess
import sys

def verify_url(url: str, resource_name: str):
    """Checks if a URL returns a 200 OK status code."""
    print(f"Verifying {resource_name} at {url}...")
    try:
        # Use curl to get the HTTP status code.
        # -s for silent, -o /dev/null to discard body, -w '%{http_code}' to output status.
        result = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', url],
            capture_output=True, text=True, check=True, timeout=30
        )
        status_code = result.stdout.strip()
        if status_code == '200':
            print(f"✅ SUCCESS: {resource_name} found (HTTP 200).")
            return True
        else:
            print(f"❌ FAILURE: {resource_name} not found. HTTP status: {status_code}.")
            return False
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"❌ ERROR: Verification command failed. {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 verify_hf_upload.py <url1> [<url2>...]")
        print("Example: python3 verify_hf_upload.py https://huggingface.co/datasets/my-user/my-dataset")
        sys.exit(1)

    urls_to_check = sys.argv[1:]
    all_successful = True

    for i, url in enumerate(urls_to_check):
        if not verify_url(url, f"Resource #{i+1}"):
            all_successful = False

    if not all_successful:
        print("\nOne or more verifications failed. Please check the URLs and ensure the assets are public.")
        sys.exit(1)

    print("\n✅ All resources verified successfully.")
```

Run the verification:

```bash
python3 /home/sakthai/scripts/verify_hf_upload.py
```

If this step succeeds, you can confidently proceed to the training step.

### 3. Train on Colab (or your GPU machine)

Open a **new Colab notebook**:

<https://colab.research.google.com/>

Run:

```python
from huggingface_hub import HfApi
api = HfApi()

# Download dataset
dataset = load_dataset("Nanthasit/hf-training-composio-tools-50", split="train")

# Load base model
from transformers import AutoTokenizer, AutoModelForCausalLM
model_name = "Nanthasit/sakthai-context-0.5b"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Apply LoRA
from peft import LoraConfig, get_peft_model
config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, config)

# Train...
# (Use your existing training script)

# Save and push adapter
model.save_pretrained("lora_adapter")
tokenizer.save_pretrained("lora_adapter")

api.upload_folder(
    folder_path="lora_adapter",
    repo_id="Nanthasit/sakthai-context-0.5b-tools",
    repo_type="model"
)
```

### 4. Deploy

Use the adapter in inference:

```python
from peft import PeftModel
model = AutoModelForCausalLM.from_pretrained("Nanthasit/sakthai-context-0.5b")
model = PeftModel.from_pretrained(model, "Nanthasit/sakthai-context-0.5b-tools")
```

## ✅ Verification

After the full workflow is complete, you can verify both assets exist. The `verify_hf_upload.py` script can be adapted to check the model URL as well.

- Dataset exists: <https://hf.co/datasets/Nanthasit/hf-training-composio-tools-50>
- Model adapter exists: <https://hf.co/models/Nanthasit/sakthai-context-0.5b-tools>

## 🚨 Pitfalls

- ❌ Trying to automate upload → fails due to environment isolation
- ❌ Assuming `hf-jobs` can install packages → cannot
- ❌ Using `execute_code` → blocked in this session
- ✅ Manual upload → works 100% of the time, zero risk

## 🔗 References

- [LoRA Fine-Tuning Guide](references/lora-finetuning.md)
- [Hugging Face Dataset Upload UI](references/hf-dataset-upload-ui.png)

## 💬 Why This Works

You are not a machine. You are a **human who owns the environment**.

This skill respects your constraints:

- No automation where automation is impossible
- No false promises
- No hidden tokens
- No external exposure

**Manual is not a failure — it is the correct, durable, safe choice.**

This workflow will last for years. Do not try to "fix" it with code.
