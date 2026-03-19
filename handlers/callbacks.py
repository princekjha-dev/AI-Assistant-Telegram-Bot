from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler
from database.db import Database
from ui.keyboards import Keyboards
from ui.menus import MenuMessages
from api_manager import get_api_manager
import config
import logging

logger = logging.getLogger(__name__)


class CallbackHandler:
    """Enhanced callback handler with image and model selection support"""
    
    def __init__(self, db: Database):
        self.db = db
        self.api_manager = get_api_manager(db)

    def get_callback_query_handler(self):
        """Get the callback query handler for registration"""
        return CallbackQueryHandler(self.handle_callback)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all inline keyboard callbacks"""
        query = update.callback_query
        await query.answer()

        user = query.from_user
        db_user = await self.db.get_or_create_user(user.id, user.username or user.first_name)

        callback_data = query.data

        try:
            # Route to appropriate handler
            if callback_data.startswith("menu_"):
                await self._handle_menu(query, db_user, callback_data)
            elif callback_data.startswith("personality_"):
                await self._handle_personality(query, db_user, callback_data)
            elif callback_data.startswith("model_"):
                await self._handle_model_selection(query, db_user, callback_data)
            elif callback_data.startswith("image_"):
                await self._handle_image_style(query, db_user, callback_data)
            elif callback_data.startswith("settings_"):
                await self._handle_settings(query, db_user, callback_data)
            elif callback_data.startswith("confirm_"):
                await self._handle_confirmation(query, db_user, callback_data)
            
        except Exception as e:
            logger.error(f"Callback error: {str(e)}", exc_info=True)
            await query.edit_message_text(f"❌ Error: {str(e)}")

    async def _handle_menu(self, query, db_user, callback_data):
        """Handle main menu navigation"""
        action = callback_data.replace("menu_", "")

        if action == "main":
            text = MenuMessages.get_welcome_message(db_user)
            keyboard = Keyboards.get_main_menu()
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

        elif action == "chat":
            await query.edit_message_text(
                "💬 Just send me a message and I'll respond!",
                reply_markup=Keyboards.get_back_button()
            )

        elif action == "features":
            features_text = """✨ **Available Features**

🖼️ **Image Generation** - /imagine [description]
🎭 **Personalities** - /personality [name]
🧠 **Multiple Models** - /model [name]
📊 **Statistics** - /stats
🏆 **Achievements** - /achievements
🔄 **Clear History** - /clear
"""
            keyboard = Keyboards.get_back_button()
            await query.edit_message_text(features_text, reply_markup=keyboard, parse_mode='Markdown')

        elif action == "settings":
            settings_text = "⚙️ **Settings Menu**\n\nChoose what to configure:"
            keyboard = Keyboards.get_settings_menu()
            await query.edit_message_text(settings_text, reply_markup=keyboard, parse_mode='Markdown')

    async def _handle_personality(self, query, db_user, callback_data):
        """Handle personality selection"""
        personality = callback_data.replace("personality_", "")

        if personality in config.AVAILABLE_PERSONALITIES:
            db_user.personality_mode = personality
            await self.db.update_user(db_user)

            response_text = f"✨ Personality changed to **{personality.capitalize()}**"

            await query.edit_message_text(response_text, reply_markup=Keyboards.get_back_button(), parse_mode='Markdown')
        else:
            await query.edit_message_text("❌ Invalid personality")

    async def _handle_model_selection(self, query, db_user, callback_data):
        """Handle AI model selection"""
        model = callback_data.replace("model_", "")

        available_models = {
            "gpt4": config.PRIMARY_MODEL,
            "claude": config.FALLBACK_MODEL,
            "llama": config.LIGHTWEIGHT_MODEL
        }

        if model in available_models:
            db_user.llm_provider = model
            await self.db.update_user(db_user)

            response_text = f"🧠 Model: **{model.upper()}**"

            await query.edit_message_text(
                response_text,
                reply_markup=Keyboards.get_back_button(),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("❌ Invalid model")

    async def _handle_image_style(self, query, db_user, callback_data):
        """Handle image generation style"""
        style = callback_data.replace("image_", "")

        available_styles = ["realistic", "anime", "painting", "cartoon", "3d", "abstract"]

        if style in available_styles:
            await query.edit_message_text(
                f"🖼️ Image style: **{style}**",
                reply_markup=Keyboards.get_back_button(),
                parse_mode='Markdown'
            )

    async def _handle_settings(self, query, db_user, callback_data):
        """Handle settings options"""
        action = callback_data.replace("settings_", "")

        if action == "personality":
            text = "🎭 **Select Personality**"
            keyboard = Keyboards.get_personality_menu()
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

        elif action == "model":
            text = "🧠 **Select AI Model**"
            keyboard = Keyboards.get_model_menu()
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

        elif action == "clear":
            text = "⚠️ **Clear History?** This cannot be undone."
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Clear", callback_data="confirm_clear_yes")],
                [InlineKeyboardButton("❌ Cancel", callback_data="confirm_clear_no")],
                [InlineKeyboardButton("◀️ Back", callback_data="menu_settings")]
            ])
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def _handle_confirmation(self, query, db_user, callback_data):
        """Handle confirmation dialogs"""
        action = callback_data.replace("confirm_", "")

        if action == "clear_yes":
            await self.db.clear_chat_history(db_user.user_id)
            await query.edit_message_text(
                "✅ History cleared!",
                reply_markup=Keyboards.get_back_button()
            )
        elif action == "clear_no":
            await query.edit_message_text(
                "❌ Cancelled",
                reply_markup=Keyboards.get_back_button()
            )