import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from . import config
from . import workflow_executor

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message when the /start command is issued."""
    user = update.effective_user
    if user.id not in config.ALLOWED_USER_IDS:
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return
    await update.message.reply_text("Welcome to the Sak-Family-Agent bot! You can use /workflow <workflow_name> to run a workflow.")

async def workflow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Executes a workflow."""
    user = update.effective_user
    if user.id not in config.ALLOWED_USER_IDS:
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return

    if not context.args:
        await update.message.reply_text("Please specify a workflow to run. Usage: /workflow <workflow_name>")
        return

    workflow_name = context.args[0]
    await update.message.reply_text(f"Executing workflow: {workflow_name}")
    try:
        result = await workflow_executor.run_workflow(workflow_name)
        await update.message.reply_text(f"Workflow finished.\n{result}")
    except Exception as e:
        await update.message.reply_text(f"Error executing workflow: {e}")

async def workflows(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists the available workflows."""
    user = update.effective_user
    if user.id not in config.ALLOWED_USER_IDS:
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return

    available_workflows = workflow_executor.get_available_workflows()
    if available_workflows:
        message = "Available workflows:\n" + "\n".join(f"- {name}" for name in available_workflows)
    else:
        message = "No workflows found."
    await update.message.reply_text(message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays instructions on how to use the bot."""
    await update.message.reply_text(
        "You can use the following commands:\n"
        "/start - Start interacting with the bot\n"
        "/workflows - List available workflows\n"
        "/workflow <workflow_name> - Execute a workflow\n"
        "/help - Display this help message"
    )

def main():
    """Starts the bot."""
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("workflow", workflow))
    application.add_handler(CommandHandler("workflows", workflows))
    application.add_handler(CommandHandler("help", help_command))

    application.run_polling()

if __name__ == '__main__':
    main()