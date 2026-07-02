"""Telegram gateway for the SakThai agent loop."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from ..agent.loop import run_agent
from ..config import telegram_allowed_user_ids, telegram_bot_token, telegram_session_db_path
from ..memory.store import MemoryStore
from . import workflow_executor

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


@dataclass
class TelegramSession:
    """Per-chat persistent state for the Telegram bot."""

    db_path: Path
    store: MemoryStore


def _is_authorized(user_id: int | None) -> bool:
    allowed = telegram_allowed_user_ids()
    return user_id is not None and user_id in allowed


def _session_key(chat_id: int | None, user_id: int | None) -> int | None:
    return chat_id if chat_id is not None else user_id


def _get_chat_session(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> TelegramSession:
    sessions = context.application.bot_data.setdefault("telegram_sessions", {})
    session = sessions.get(chat_id)
    if session is None:
        db_path = telegram_session_db_path(chat_id)
        session = TelegramSession(db_path=db_path, store=MemoryStore(db_path))
        sessions[chat_id] = session
    return session


async def _reply_with_agent_result(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    task: str,
    *,
    skills: tuple[str, ...] = (),
) -> None:
    user = update.effective_user
    chat = getattr(update, "effective_chat", None)
    if not _is_authorized(user.id if user else None):
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return
    if chat is None:
        await update.message.reply_text("Sorry, I could not determine the chat session.")
        return

    session_id = _session_key(getattr(chat, "id", None), user.id if user else None)
    if session_id is None:
        await update.message.reply_text("Sorry, I could not determine the chat session.")
        return

    session = _get_chat_session(context, session_id)
    result = await asyncio.to_thread(
        run_agent,
        task,
        store=session.store,
        skills=list(skills),
        stateless=False,
    )
    await update.message.reply_text(result.text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the /start command is issued."""
    user = update.effective_user
    if not _is_authorized(user.id if user else None):
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return
    await update.message.reply_text(
        "Welcome to the Sak-Family-Agent bot. Send a message to chat with the agent "
        "or use /workflow <name> to run a specific skill."
    )


async def workflow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run one workflow skill through the main agent loop."""
    user = update.effective_user
    if not _is_authorized(user.id if user else None):
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return

    if not context.args:
        await update.message.reply_text(
            "Please specify a workflow to run. Usage: /workflow <workflow_name>"
        )
        return

    workflow_name = context.args[0]
    available_workflows = workflow_executor.get_available_workflows()
    if available_workflows and workflow_name not in available_workflows:
        await update.message.reply_text(
            "Workflow not found. Available workflows are: " + ", ".join(available_workflows)
        )
        return

    await update.message.reply_text(f"Executing workflow: {workflow_name}")
    await _reply_with_agent_result(
        update,
        context,
        f"Execute the {workflow_name} skill and report the result.",
        skills=(workflow_name,),
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run the main agent loop for free-form text messages."""
    message = getattr(update.message, "text", "") if update.message else ""
    if not message:
        return
    await _reply_with_agent_result(update, context, message)


async def workflows(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List the available workflows."""
    user = update.effective_user
    if not _is_authorized(user.id if user else None):
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return

    available_workflows = workflow_executor.get_available_workflows()
    if available_workflows:
        message = "Available workflows:\n" + "\n".join(f"- {name}" for name in available_workflows)
    else:
        message = "No workflows found."
    await update.message.reply_text(message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display instructions on how to use the bot."""
    await update.message.reply_text(
        "You can use the following commands:\n"
        "/start - Start interacting with the bot\n"
        "/workflows - List available workflows\n"
        "/workflow <workflow_name> - Execute a workflow\n"
        "Or send a plain message to chat with the agent.\n"
        "/help - Display this help message"
    )


def main() -> None:
    """Start the bot."""
    token = telegram_bot_token()
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set!")

    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("workflow", workflow))
    application.add_handler(CommandHandler("workflows", workflows))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    application.run_polling()


if __name__ == "__main__":
    main()
