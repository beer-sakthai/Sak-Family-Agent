import subprocess
import sys

# Test 1: Run verify.py directly
res = subprocess.run([sys.executable, "verify.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
print("verify.py exit code:", res.returncode)
assert res.returncode == 0, f"Expected 0, got {res.returncode}"
print("verify.py output tail:\n", "\n".join(res.stdout.splitlines()[-10:]))
