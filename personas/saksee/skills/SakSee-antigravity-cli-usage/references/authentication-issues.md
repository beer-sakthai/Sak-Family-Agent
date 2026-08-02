# Authentication Issues with Antigravity CLI

## Problem

In headless environments, the Antigravity CLI (`agy`) often fails to authenticate with the error:
```
Error: authentication failed or timed out
```

## Solution

For headless environments, use the Python SDK instead of the CLI binary:

1. Install the Python SDK:
   ```bash
   uv pip install google-antigravity
   ```

2. Obtain a GEMINI_API_KEY from Google Cloud Platform

3. Use the SDK with the API key:
   ```bash
   export GEMINI_API_KEY='your-api-key-here'
   python3 your_script.py
   ```

## Test Script

A simple test script to verify the Python SDK is working:

```python
#!/usr/bin/env python3
import asyncio
import os

async def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY environment variable not set.")
        return

    try:
        from google.antigravity.agent import Agent
        from google.antigravity.connections.local.local_connection_config import LocalAgentConfig

        async with Agent(config=LocalAgentConfig()) as agent:
            result = await agent.chat("Hello, this is a test")
            text = await result.text()
            print(text)
            
    except ImportError:
        print("Google Antigravity SDK not installed.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```