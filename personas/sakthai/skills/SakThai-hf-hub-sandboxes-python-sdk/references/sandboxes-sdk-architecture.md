# Hugging Face Sandboxes Python SDK Architecture & Reference

Detailed architecture, authentication, and execution recipes for `huggingface_hub` Sandboxes (`Sandbox` & `SandboxPool`).

## 1. Architecture: "No New Service"
- Built entirely atop HF Jobs running `sbx-server` (a static Rust binary proxy).
- Two execution modes:
  - **Dedicated Sandbox (`Sandbox.create()`)**: 1 Job = 1 VM, supports GPU hardware, isolated kernel.
  - **Pooled Sandbox (`SandboxPool`)**: 1 VM hosting multiple tenant sandboxes isolated via Linux Landlock + UID namespaces.

## 2. Python SDK Usage

### Dedicated Sandbox
```python
from huggingface_hub import Sandbox

# Create dedicated sandbox
sandbox = Sandbox.create(
    hardware="cpu-basic",  # or "t4-small"
    image="python:3.11-slim"
)

# Run remote commands
result = sandbox.run(["python", "-c", "print('Hello from HF Sandbox!')"])
print(result.stdout)

# File transfer
sandbox.upload_file("local_script.py", "/workspace/script.py")
sandbox.download_file("/workspace/output.txt", "local_output.txt")

# Cleanup
sandbox.terminate()
```

### Sandbox Pool
```python
from huggingface_hub import SandboxPool

pool = SandboxPool.create(hardware="cpu-basic", capacity=5)
tenant_sbx = pool.acquire()
tenant_sbx.run(["echo", "Running inside Landlock sandbox"])
pool.release(tenant_sbx)
```

## 3. CLI Management
```bash
# Spin up via CLI
hf jobs sandbox create --hardware cpu-basic --image python:3.11-slim
hf jobs sandbox list
hf jobs sandbox terminate <JOB_ID>
```
