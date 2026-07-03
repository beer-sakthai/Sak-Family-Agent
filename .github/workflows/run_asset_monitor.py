import os
import sys

# Add the skills directory to the Python path to allow direct imports
sys.path.append('/home/sakthai')

# Import the verification function directly from the other skill's script
from personas.sakthai.skills.mlops.mlops-hf-train-manual-upload.scripts.verify_hf_upload import (
    verify_url,
)

# We will simulate the telegram tool here for local execution and clarity.
# We will simulate it here for local execution and clarity.
def send_telegram_message(chat_id: str, message: str):
    """
    Simulates calling an external 'telegram' tool to send a message.
    In a real Hermes agent environment, this would be a call to the
    `telegram` tool via `execute_code` or a similar mechanism.
    """
    print(f"--- SIMULATING TELEGRAM ALERT ---")
    print(f"TO: {chat_id}")
    print(f"MESSAGE: {message}")
    print(f"-------------------------------")
    # In a real environment, you might use:
    # subprocess.run(['telegram', 'send', '--chat_id', chat_id, '--text', message], check=True)


def main():
    """
    Reads URLs from a config file, verifies them using the existing script,
    and sends a Telegram alert on failure.
    """
    urls_file = "/home/sakthai/config/asset_monitor_urls.txt"
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not chat_id:
        print("❌ ERROR: TELEGRAM_CHAT_ID environment variable not set.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(urls_file, "r") as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"❌ ERROR: Configuration file not found at {urls_file}", file=sys.stderr)
        sys.exit(1)

    if not urls:
        print("No URLs to monitor. Exiting.", file=sys.stderr)
        sys.exit(0)

    print(f"Monitoring {len(urls)} assets...")
    failed_urls = []
    for i, url in enumerate(urls):
        if not verify_url(url, f"Resource #{i+1}"):
            failed_urls.append(url)

    if not failed_urls:
        print("✅ All assets are available and accessible.")
    else:
        message = "🚨 Asset Monitor Failure!\nThe following assets may be down:\n" + "\n".join(f"- {url}" for url in failed_urls)
        send_telegram_message(chat_id, message)
        print(f"🔥 Alert sent for {len(failed_urls)} failed asset(s).", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()