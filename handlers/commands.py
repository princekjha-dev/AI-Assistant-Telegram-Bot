"""
Enhanced command handlers with image generation and model selection
"""

from telegram import Update
from telegram.ext import ContextTypes
from database.db import Database
from ui.keyboards import Keyboards
from ui.menus import MenuMessages
from gamification.achievements import AchievementManager
from api_manager import get_api_manager
import config
import logging

logger = logging.getLogger(__name__)


class CommandHandlers:
    """Handle all Telegram commands"""
    
    def __init__(self, db: Database):
        self.db = db
        self.achievement_manager = AchievementManager(db)
        self.api_manager = get_api_manager(db)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        db_user = await self.db.get_or_create_user(user.id, user.username or user.first_name)

        welcome_text = f"""👋 Welcome to your AI Assistant, {user.first_name}!

I'm a smart Telegram bot powered by OpenRouter AI. I can:
🤖 Have natural conversations with persistent memory
🎭 Adapt my personality to your preferences
😊 Detect and respond to your mood
🖼️ Generate images from descriptions
📊 Track your engagement with streaks & achievements

Use /menu to see all options or just start chatting!"""

        await update.message.reply_text(welcome_text, reply_markup=Keyboards.get_main_menu())

    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /menu command"""
        user = update.effective_user
        db_user = await self.db.get_or_create_user(user.id, user.username or user.first_name)

        menu_text = MenuMessages.get_welcome_message(db_user)
        await update.message.reply_text(menu_text, reply_markup=Keyboards.get_main_menu(), parse_mode='Markdown')

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        user = update.effective_user
        db_user = await self.db.get_or_create_user(user.id, user.username or user.first_name)

        stats_text = MenuMessages.get_stats_message(db_user)
        await update.message.reply_text(stats_text, reply_markup=Keyboards.get_back_button(), parse_mode='Markdown')

    async def achievements_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /achievements command"""
        user = update.effective_user
        db_user = await self.db.get_or_create_user(user.id, user.username or user.first_name)

        progress_text = await self.achievement_manager.get_user_progress(db_user)
        await update.message.reply_text(progress_text, reply_markup=Keyboards.get_back_button(), parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """🤖 **Bot Commands**

**Main Commands:**
/start - Start the bot
/menu - Open main menu
/stats - View statistics
/achievements - View achievements
/help - Show this message

**Advanced Features:**
/imagine [prompt] - Generate images
/model [name] - Select AI model (gpt4, claude, llama)
/personality [mode] - Change personality
/clear - Clear chat history
/settings - Bot settings

**Personalities:** friendly | professional | motivational | sarcastic | creative

**How to Use:**
Just message me naturally! I'll adapt to your mood and preferences."""

        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def imagine_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /imagine command for image generation"""
        user = update.effective_user
        
        if not config.ENABLE_IMAGE_GENERATION:
            await update.message.reply_text("❌ Image generation is disabled")
            return
        
        if not context.args:
            await update.message.reply_text(
                "📸 Usage: /imagine [description]\n"
                "Example: /imagine a cat wearing sunglasses, digital art"
            )
            return
        
        prompt = " ".join(context.args)
        
        if len(prompt) > 500:
            await update.message.reply_text("❌ Prompt too long (max 500 characters)")
            return
        
        try:
            db_user = await self.db.get_or_create_user(user.id, user.username or user.first_name)
            
            # Send processing message
            status_msg = await update.message.reply_text("🎨 Generating image... This may take a moment...")
            
            # Generate image using unified API manager
            image_url = await self.api_manager.generate_image(
                prompt=prompt,
                user_id=user.id
            )
            
            if image_url:
                # Update score
                db_user.interaction_score += config.POINTS_PER_IMAGE
                await self.db.update_user(db_user)
                
                # Send image
                await update.message.reply_photo(
                    image_url,
                    caption=f"🖼️ Generated: {prompt[:100]}..."
                )
                
                await status_msg.delete()
            else:
                await status_msg.edit_text("❌ Failed to generate image")
                
        except Exception as e:
            logger.error(f"Image generation error: {str(e)}", exc_info=True)
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command"""
        user = update.effective_user
        db_user = await self.db.get_or_create_user(user.id, user.username or user.first_name)
        
        settings_text = f"""⚙️ **Your Settings**

🎭 **Personality:** {db_user.personality_mode}
🧠 **AI Model:** {db_user.llm_provider}
😊 **Current Mood:** {db_user.mood_state}
📊 **Score:** {db_user.interaction_score}
🔥 **Streak:** {db_user.streak_count} days

Use the menu to change these settings."""
        
        await update.message.reply_text(settings_text, reply_markup=Keyboards.get_settings_menu(), parse_mode='Markdown')

    async def model_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /model command"""
        user = update.effective_user
        db_user = await self.db.get_or_create_user(user.id, user.username or user.first_name)
        
        if not context.args:
            model_text = f"""🧠 **AI Models**

Current: **{db_user.llm_provider.upper()}**

Available:
• gpt4 - OpenAI GPT-4 Turbo
• claude - Anthropic Claude 3 Sonnet
• llama - Meta Llama 2 70B

Usage: /model gpt4"""
            await update.message.reply_text(model_text, parse_mode='Markdown')
            return
        
        model = context.args[0].lower()
        
        valid_models = ["gpt4", "claude", "llama"]
        if model in valid_models:
            db_user.llm_provider = model
            await self.db.update_user(db_user)
            await update.message.reply_text(f"✅ Model changed to **{model.upper()}**", parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Unknown model. Use: {', '.join(valid_models)}")

    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clear command"""
        user = update.effective_user
        
        try:
            await self.db.clear_chat_history(user.id)
            await update.message.reply_text("✅ Chat history cleared!")
        except Exception as e:
            logger.error(f"Clear command error: {str(e)}")
            await update.message.reply_text(f"❌ Error: {str(e)}")