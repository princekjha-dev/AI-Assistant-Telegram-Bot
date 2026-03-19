"""
Main entry point for the AI Assistant Telegram Bot
Supports both polling and webhook modes
"""

import asyncio
import logging
import config
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Import handlers
from handlers.commands import CommandHandlers
from handlers.messages import MessageHandler as MessageHandlerClass
from handlers.callbacks import CallbackHandler
from database.db import Database


class BotApplication:
    """Main bot application class"""
    
    def __init__(self):
        self.db = Database()
        self.db._init_db_sync()
        self.application = None
        
        # Create application
        self.application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        
        # Initialize handlers
        command_handlers = CommandHandlers(self.db)
        message_handlers = MessageHandlerClass(self.db)
        callback_handler = CallbackHandler(self.db)
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", command_handlers.start_command))
        self.application.add_handler(CommandHandler("menu", command_handlers.menu_command))
        self.application.add_handler(CommandHandler("stats", command_handlers.stats_command))
        self.application.add_handler(CommandHandler("achievements", command_handlers.achievements_command))
        self.application.add_handler(CommandHandler("help", command_handlers.help_command))
        self.application.add_handler(CommandHandler("settings", command_handlers.settings_command))
        self.application.add_handler(CommandHandler("imagine", command_handlers.imagine_command))
        self.application.add_handler(CommandHandler("model", command_handlers.model_command))
        self.application.add_handler(CommandHandler("clear", command_handlers.clear_command))
        
        # Add message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_message))
        self.application.add_handler(MessageHandler(filters.PHOTO, message_handlers.handle_image))
        self.application.add_handler(MessageHandler(filters.VOICE, message_handlers.handle_voice))
        
        # Add callback handler for button presses
        self.application.add_handler(callback_handler.get_callback_query_handler())
        
        # Add error handler
        self.application.add_error_handler(self.error_handler)
        
        logger.info("Bot application initialized successfully")
    
    def start(self):
        """Start the bot - entry point that manages event loops properly"""
        try:
            logger.info("Initializing bot application...")
            # Now start the application (this manages its own event loop)
            if config.POLLING_MODE:
                logger.info("Starting bot in polling mode...")
                self.application.run_polling()
            else:
                logger.info(f"Starting bot in webhook mode on {config.HOST}:{config.PORT}")
                self.application.run_webhook(
                    listen=config.HOST,
                    port=config.PORT,
                    url_path=config.WEBHOOK_URL,
                    webhook_url=config.WEBHOOK_URL
                )
        except KeyboardInterrupt:
            logger.info("Bot interrupted by user")
        except Exception as e:
            logger.error(f"Bot error: {str(e)}", exc_info=True)
            raise
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error: {context.error}", exc_info=True)
        
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ An unexpected error occurred. Please try again later or contact support."
                )
            except Exception as e:
                logger.error(f"Failed to send error message: {str(e)}")


def main():
    """Main function"""
    # Validate configuration
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
    
    # Create and start bot
    bot = BotApplication()
    bot.start()


if __name__ == "__main__":
    main()
