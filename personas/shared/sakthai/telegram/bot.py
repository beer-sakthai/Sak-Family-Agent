"""Telegram gateway for the SakThai agent loop."""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from ..agent.loop import run_agent
from ..config import (
    sakthai_default_model,
    sakthai_default_provider,
    sakthai_fast_mode,
    sakthai_system_prompt_prefix,
    sakthai_with_skills,
    telegram_allowed_user_ids,
    telegram_bot_token,
    telegram_session_db_path,
)
from ..memory.store import MemoryStore
from . import workflow_executor

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

SUPPORTED_PERSONAS = ("sakthai", "sakking", "saktan", "saksee", "saksit", "sakjules")
RECOMMENDED_MODELS = (
    "huggingface/Kimi-K2-Instruct",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "ollama/qwen2.5-coder",
    "ollama/sakthai",
    "gpt-4o",
)


@dataclass
class TelegramSession:
    """Per-chat persistent state for the Telegram bot."""

    db_path: Path
    store: MemoryStore
    model: str | None = None
    persona: str | None = None


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _ensure_main_thread_event_loop() -> None:
    """Register a current event loop for python-telegram-bot startup."""
    asyncio.set_event_loop(asyncio.new_event_loop())


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
    provider = sakthai_default_provider()
    model = session.model or sakthai_default_model() or "huggingface/Kimi-K2-Instruct"
    system_prompt_prefix = sakthai_system_prompt_prefix() or ""


    if session.persona:
        system_prompt_prefix = f"Active Persona: {session.persona.capitalize()}\n" + system_prompt_prefix

    combined_skills = tuple(skills) + tuple(sakthai_with_skills())
    # run_agent is a long, synchronous LLM round-trip; run it in a worker
    # thread so the polling loop keeps serving other chats meanwhile.
    result = await asyncio.to_thread(
        run_agent,
        task,
        store=session.store,
        skills=list(combined_skills),
        provider=provider,
        model=model,
        fast=sakthai_fast_mode(),
        stateless=_env_bool("SAKTHAI_STATELESS", False),
        system_prompt_prefix=system_prompt_prefix,
    )
    await update.message.reply_text(result.text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the /start command is issued."""
    user = update.effective_user
    if not _is_authorized(user.id if user else None):
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return
    await update.message.reply_text(
        "Welcome to the Sak-Family-Agent bot.\n"
        "• Send any message to chat with the agent.\n"
        "• Use /model <name> to pick a model dynamically.\n"
        "• Use /persona <name> to switch agent persona.\n"
        "• Use /models to list available models.\n"
        "• Use /status to check current session settings.\n"
        "• Use /workflow <name> to run a specific skill."
    )


async def set_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Dynamically set the active LLM model for this chat session."""
    user = update.effective_user
    if not _is_authorized(user.id if user else None):
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return
    if not context.args:
        await update.message.reply_text(
            "Please specify a model name. Example: /model gemini-2.5-pro or /model qwen2.5-coder\n"
            "Use /models to see recommendations."
        )
        return

    chosen_model = context.args[0].strip()
    session_id = _session_key(update.effective_chat.id if update.effective_chat else None, user.id)
    session = _get_chat_session(context, session_id)
    session.model = chosen_model

    await update.message.reply_text(f"🤖 Model set to '{chosen_model}' for this chat session.")


async def set_persona(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Dynamically set the active agent persona for this chat session."""
    user = update.effective_user
    if not _is_authorized(user.id if user else None):
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return
    if not context.args:
        await update.message.reply_text(
            f"Please specify a persona name. Choose from: {', '.join(SUPPORTED_PERSONAS)}\n"
            "Example: /persona sakking"
        )
        return

    chosen_persona = context.args[0].strip().lower()
    if chosen_persona not in SUPPORTED_PERSONAS:
        await update.message.reply_text(
            f"Unknown persona '{chosen_persona}'. Available options: {', '.join(SUPPORTED_PERSONAS)}"
        )
        return

    session_id = _session_key(update.effective_chat.id if update.effective_chat else None, user.id)
    session = _get_chat_session(context, session_id)
    session.persona = chosen_persona

    await update.message.reply_text(f"👑 Persona set to '{chosen_persona.capitalize()}' for this chat session.")


async def list_models(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List recommended model choices."""
    user = update.effective_user
    if not _is_authorized(user.id if user else None):
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return

    msg = "Available & Recommended Models:\n" + "\n".join(f"• `{m}`" for m in RECOMMENDED_MODELS)
    msg += "\n\nTo pick any model: `/model <model-name>`"
    await update.message.reply_text(msg, parse_mode="Markdown")


async def session_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current session settings (active model and persona)."""
    user = update.effective_user
    if not _is_authorized(user.id if user else None):
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return

    session_id = _session_key(update.effective_chat.id if update.effective_chat else None, user.id)
    session = _get_chat_session(context, session_id)


    current_model = session.model or sakthai_default_model() or "huggingface/Kimi-K2-Instruct (default)"
    current_persona = session.persona.capitalize() if session.persona else "SakThai (default)"

    msg = (
        f"⚙️ **Chat Session Settings**\n"
        f"• **Active Model**: `{current_model}`\n"
        f"• **Active Persona**: `{current_persona}`\n\n"
        f"Use `/model <name>` or `/persona <name>` to change at any time."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


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
    if workflow_name not in available_workflows:
        if available_workflows:
            await update.message.reply_text(
                "Workflow not found. Available workflows are: " + ", ".join(available_workflows)
            )
        else:
            await update.message.reply_text("Workflow not found. No workflows are installed.")
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
        "/model <name> - Dynamically switch the LLM model for this chat\n"
        "/persona <name> - Switch active agent persona (sakthai, sakking, saktan, saksee, saksit, sakjules)\n"
        "/models - List recommended models\n"
        "/status - Check current active model & persona\n"
        "/workflows - List available workflows\n"
        "/workflow <name> - Execute a specific workflow\n"
        "/help - Display this help message"
    )


def main() -> None:
    """Start the bot."""
    token = telegram_bot_token()
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set!")

    _ensure_main_thread_event_loop()
    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("model", set_model))
    application.add_handler(CommandHandler("m", set_model))
    application.add_handler(CommandHandler("persona", set_persona))
    application.add_handler(CommandHandler("agent", set_persona))
    application.add_handler(CommandHandler("models", list_models))
    application.add_handler(CommandHandler("status", session_status))
    application.add_handler(CommandHandler("workflow", workflow))
    application.add_handler(CommandHandler("workflows", workflows))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    application.run_polling()


if __name__ == "__main__":
    main()
