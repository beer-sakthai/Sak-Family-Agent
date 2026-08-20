---
name: SakSee-gemini-computer-use
description: "Build UI automation agents with Gemini Computer Use."
---

# Gemini Computer Use

This skill covers building browser, mobile, and desktop automation agents with the Gemini API `computer_use` tool through the Interactions API. It explains how to send screenshots, receive UI actions, execute them safely, and return results in a loop.

It does NOT cover non-interactive text/image generation, general function calling, or the legacy `generateContent` API path for Computer Use.

## When to Use

- "Build a Gemini agent that controls a browser."
- "Use Computer Use with Playwright."
- "Set up desktop or mobile automation via Gemini API."
- "Handle Gemini Computer Use safety decisions and confirmations."

## Prerequisites

- `GOOGLE_API_KEY` environment variable with a valid Gemini API key. Get one at https://ai.google.dev/gemini-api/docs/api-key.
- Python 3.11+ and `google-genai>=2.7.0`.
- Playwright for browser/desktop environments: `pip install playwright` then `playwright install chromium`.
- A sandboxed VM or container for production desktop automation.

## How to Run

Invoke setup and example scripts through the `terminal` tool after writing them with `write_file`.

## Quick Reference

| Item | Value |
|---|---|
| Docs | https://ai.google.dev/gemini-api/docs/computer-use |
| Reference implementation | https://github.com/google-gemini/computer-use-preview |
| Recommended model | `gemini-3.5-flash` |
| API method | `client.interactions.create(...)` |
| Tool type | `computer_use` |
| Environments | `browser`, `mobile`, `desktop` |
| Coordinates | Normalized `0-999`, scale to viewport |
| Paid pricing | Input $1.50/1M tokens, Output $9.00/1M tokens |

## Procedure

1. Install dependencies through `terminal`:
   ```bash
   pip install google-genai playwright
   playwright install chromium
   ```

2. Export your API key through `terminal`:
   ```bash
   export GOOGLE_API_KEY="YOUR_KEY"
   ```

3. Create a minimal browser agent with `write_file`:
   ```python
   # gemini_browser_agent.py
   import base64, json, time
   from playwright.sync_api import sync_playwright
   from google import genai

   SCREEN_WIDTH, SCREEN_HEIGHT = 1440, 900

   def denormalize(x, y):
       return int(x / 1000 * SCREEN_WIDTH), int(y / 1000 * SCREEN_HEIGHT)

   def execute(step, page):
       name = step.name
       args = step.arguments
       if name in ("click", "click_at"):
           x, y = denormalize(args["x"], args["y"])
           page.mouse.click(x, y)
       elif name in ("type", "type_text_at"):
           x, y = denormalize(args.get("x", 0), args.get("y", 0))
           if args.get("x") is not None:
               page.mouse.click(x, y)
           page.keyboard.press("Meta+A")
           page.keyboard.press("Backspace")
           page.keyboard.type(args["text"])
           if args.get("press_enter"):
               page.keyboard.press("Enter")
       elif name == "navigate":
           page.goto(args["url"])
       elif name == "wait":
           time.sleep(args.get("seconds", 1))
       page.wait_for_load_state(timeout=5000)
       time.sleep(1)

   def capture(page, results):
       screenshot = page.screenshot(type="png")
       url = page.url
       return [
           {
               "type": "function_result",
               "name": name,
               "call_id": call_id,
               "result": [
                   {"type": "text", "text": json.dumps({"url": url, **result})},
                   {"type": "image", "data": base64.b64encode(screenshot).decode(), "mime_type": "image/png"},
               ],
           }
           for name, call_id, result in results
       ]

   client = genai.Client()
   with sync_playwright() as p:
       browser = p.chromium.launch(headless=False)
       page = browser.new_context(
           viewport={"width": SCREEN_WIDTH, "height": SCREEN_HEIGHT}
       ).new_page()
       page.goto("https://www.google.com")
       screenshot = page.screenshot(type="png")

       interaction = client.interactions.create(
           model="gemini-3.5-flash",
           input=[
               {"type": "text", "text": "Search for 'Gemini API'."},
               {"type": "image", "data": base64.b64encode(screenshot).decode(), "mime_type": "image/png"},
           ],
           tools=[{
               "type": "computer_use",
               "environment": "browser",
               "enable_prompt_injection_detection": True,
           }],
       )

       for turn in range(10):
           calls = [s for s in interaction.steps if s.type == "function_call"]
           if not calls:
               break
           results = []
           for call in calls:
               execute(call, page)
               results.append((call.name, call.id, {}))
           interaction = client.interactions.create(
               model="gemini-3.5-flash",
               previous_interaction_id=interaction.id,
               input=capture(page, results),
               tools=[{
                   "type": "computer_use",
                   "environment": "browser",
                   "enable_prompt_injection_detection": True,
               }],
           )
       browser.close()
   ```

4. Run the script through `terminal`:
   ```bash
   python gemini_browser_agent.py
   ```

5. For desktop or mobile, change `environment` to `desktop` or `mobile` and provide an appropriate executor (e.g. PyAutoGUI or Android debug bridge).

6. Handle safety decisions. If a `function_call` includes `safety_decision.decision == "require_confirmation"`, ask the user and set `safety_acknowledgement: true` in the `function_result` before continuing.

## Pitfalls

- Coordinates are normalized `0-999`; always scale to the actual viewport before executing.
- `gemini-3.5-flash` uses streamlined names (`click`, `type`); legacy `gemini-2.5-computer-use-preview-10-2025` uses `click_at`/`type_text_at`. Handle both for legacy support.
- The model may return `safety_decision: blocked`; halt execution or ask the user.
- Computer Use is a Preview capability with security risks; run in a sandbox or container, never on a host with sensitive data.
- Do not use it for financial transactions, account creation, sending communications, accepting legal terms, or solving CAPTCHAs without explicit human confirmation.
- Free tier input/output is free of charge but content may be used to improve products; paid tier rates apply after upgrading.

## Verification

Run a one-turn API check through `terminal`:
```bash
python - <<'PY'
from google import genai
client = genai.Client()
interaction = client.interactions.create(
    model="gemini-3.5-flash",
    input="Hello.",
    tools=[{"type": "computer_use", "environment": "browser"}],
)
print("interaction id:", interaction.id)
print("step types:", [s.type for s in interaction.steps])
PY
```

A successful run prints an `interaction id` and a list of step types, confirming the API accepts the `computer_use` tool configuration.
