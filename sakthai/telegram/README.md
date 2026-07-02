# SakThai Telegram Bot

This directory contains a Telegram bot that allows you to interact with the SakThai agent.

## Setup

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure the bot:**
    *   Set the `TELEGRAM_BOT_TOKEN` environment variable to your Telegram bot token.
    *   Open the `config.py` file.
    *   Add your Telegram user ID to the `ALLOWED_USER_IDS` list.

    To get your Telegram Bot Token:
    1.  Open the Telegram app and search for the "BotFather" bot.
    2.  Start a chat with BotFather and send the `/newbot` command.
    3.  Follow the instructions to create a new bot. BotFather will give you a token for your new bot.

    To get your Telegram User ID:
    1.  Search for the "userinfobot" in the Telegram app.
    2.  Start a chat with this bot and it will return your user ID.

## Running the bot

To run the bot, execute the following command from the root of the project:

```bash
python -m sakthai.telegram
```

## Usage

Once the bot is running, you can interact with it from your Telegram account.

*   `/start`: Sends a welcome message.
*   `/workflows`: Lists the available workflows.
*   `/workflow <workflow_name>`: Executes a workflow. The available workflows are the skills in the `skills` directory.

For example, to run the `sakthai-coding-testing` skill, you would send the following message:

```
/workflow sakthai-coding-testing
```

The bot will then execute the skill and return the output to you.
