import http.client
import subprocess
import time
import os
import signal

def test_server(cmd, port):
    print(f"Testing server: {cmd}")
    proc = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid)
    time.sleep(2)
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port)
        conn.request("GET", "/")
        resp = conn.getresponse()
        headers = {k.lower(): v for k, v in resp.getheaders()}
        print(f"Status: {resp.status}")

        expected = [
            "x-frame-options",
            "x-content-type-options",
            "referrer-policy",
            "content-security-policy"
        ]

        for h in expected:
            if h in headers:
                print(f"Found {h}: {headers[h]}")
            else:
                print(f"MISSING {h}")
    finally:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)

# Ensure dist exists for CLI test
os.makedirs("dashboard/dist", exist_ok=True)
with open("dashboard/dist/index.html", "w") as f:
    f.write("test")

# Test CLI dashboard (port 3003)
test_server("uv run sakthai dashboard --port 3003 --no-open", 3003)

# Test web server (port 3001)
test_server("uv run python3 sakthai/web/server.py", 3001)

# Test scripts/serve_api.py (port 3002)
test_server("uv run python3 scripts/serve_api.py", 3002)
