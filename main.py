"""
Main entry point for the AI Assistant Telegram Bot.
Supports both polling and webhook modes.
"""

from __future__ import annotations

import logging
import sys

import config


# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


class BotApplication:
    """Main bot application class."""

    def __init__(self):
        from telegram.ext import Application, CommandHandler, MessageHandler, filters

        from database.db import Database
        from handlers.callbacks import CallbackHandler
        from handlers.commands import CommandHandlers
        from handlers.messages import MessageHandler as MessageHandlerClass

        self.db = Database()
        self.db._init_db_sync()
        self.application = None

        self.application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

        command_handlers = CommandHandlers(self.db)
        message_handlers = MessageHandlerClass(self.db)
        callback_handler = CallbackHandler(self.db)

        self.application.add_handler(CommandHandler("start", command_handlers.start_command))
        self.application.add_handler(CommandHandler("menu", command_handlers.menu_command))
        self.application.add_handler(CommandHandler("stats", command_handlers.stats_command))
        self.application.add_handler(CommandHandler("achievements", command_handlers.achievements_command))
        self.application.add_handler(CommandHandler("help", command_handlers.help_command))
        self.application.add_handler(CommandHandler("settings", command_handlers.settings_command))
        self.application.add_handler(CommandHandler("imagine", command_handlers.imagine_command))
        self.application.add_handler(CommandHandler("model", command_handlers.model_command))
        self.application.add_handler(CommandHandler("clear", command_handlers.clear_command))
        self.application.add_handler(CommandHandler("remember", command_handlers.remember_command))
        self.application.add_handler(CommandHandler("forget", command_handlers.forget_command))
        self.application.add_handler(CommandHandler("memories", command_handlers.memories_command))
        self.application.add_handler(CommandHandler("remindme", command_handlers.remindme_command))
        self.application.add_handler(CommandHandler("export", command_handlers.export_command))
        self.application.add_handler(CommandHandler("invite", command_handlers.invite_command))
        self.application.add_handler(CommandHandler("admin", command_handlers.admin_command))

        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_message))
        self.application.add_handler(MessageHandler(filters.PHOTO, message_handlers.handle_image))
        self.application.add_handler(MessageHandler(filters.VOICE, message_handlers.handle_voice))
        self.application.add_handler(callback_handler.get_callback_query_handler())
        self.application.add_error_handler(self.error_handler)

        logger.info("Bot application initialized successfully")

    def start(self):
        """Start the bot entrypoint."""
        try:
            logger.info("Initializing bot application...")
            if config.RUN_MODE == "webhook":
                logger.info(f"Starting bot in webhook mode on {config.HOST}:{config.PORT}")
                self.application.run_webhook(
                    listen=config.HOST,
                    port=config.PORT,
                    url_path=config.WEBHOOK_URL or "telegram",
                    webhook_url=(
                        f"{config.WEBHOOK_URL}/{config.WEBHOOK_URL.split('/')[-1]}"
                        if config.WEBHOOK_URL
                        else None
                    ),
                    secret_token=config.WEBHOOK_SECRET_TOKEN or None,
                )
            else:
                logger.info("Starting bot in polling mode...")
                self.application.run_polling()
        except KeyboardInterrupt:
            logger.info("Bot interrupted by user")
        except Exception as exc:
            logger.error(f"Bot error: {exc}", exc_info=True)
            raise

    async def error_handler(self, update, context):
        """Handle errors."""
        logger.error(f"Update {update} caused error: {context.error}", exc_info=True)
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ An unexpected error occurred. Please try again later or contact support."
                )
            except Exception as exc:
                logger.error(f"Failed to send error message: {exc}")


def create_health_app():
    """Create a lightweight app export for deployment platforms like Vercel."""

    def app(environ, start_response):
        path = environ.get("PATH_INFO", "/")
        if path in {"/", "/health", "/healthz"}:
            status = "200 OK"
            body = b'{"status":"ok","service":"ai-assistant-telegram-bot"}'
        else:
            status = "404 Not Found"
            body = b'{"error":"Not Found"}'

        headers = [("Content-Type", "application/json")]
        start_response(status, headers)
        return [body]

    return app


app = create_health_app()
application = app


def main():
    """Main function."""
    config_errors = config.validate_config()
    if config_errors:
        logger.error("Configuration errors:")
        for error in config_errors:
            logger.error(f"  - {error}")
        sys.exit(1)

    logger.info(f"Starting bot in {config.ENVIRONMENT} mode")
    logger.info(f"LLM Provider: {config.LLM_PROVIDER}")
    logger.info(f"Primary Model: {config.PRIMARY_MODEL}")
    logger.info(f"Image Generation: {'Enabled' if config.ENABLE_IMAGE_GENERATION else 'Disabled'}")

    bot = BotApplication()
    bot.start()


if __name__ == "__main__":
    main()

