"""
Enhanced Message Handler with image generation support
"""

from telegram import Update
from telegram.ext import ContextTypes
from database.db import Database
from api_manager import get_api_manager
from gamification.streaks import StreakManager
from gamification.achievements import AchievementManager
from utils.security import SecurityValidator
import config
import logging

logger = logging.getLogger(__name__)


class MessageHandler:
    """Enhanced message handler with unified API integration"""
    
    def __init__(self, db: Database):
        self.db = db
        self.achievement_manager = AchievementManager(db)
        self.api_manager = get_api_manager(db)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text messages"""
        user = update.effective_user
        message_text = update.message.text

        # Security validation
        is_valid, error_msg = SecurityValidator.validate_message(message_text)
        if not is_valid:
            await update.message.reply_text(f"❌ {error_msg}")
            return

        # Check if message is too long
        if len(message_text) > config.MAX_MESSAGE_LENGTH:
            await update.message.reply_text(
                f"❌ Message is too long (max {config.MAX_MESSAGE_LENGTH} characters)"
            )
            return

        # Sanitize input
        message_text = SecurityValidator.sanitize_input(message_text)

        # Get or create user
        db_user = await self.db.get_or_create_user(user.id, user.username or user.first_name)

        # Update streak
        streak_continued, streak_count = StreakManager.update_streak(db_user)
        if not streak_continued and streak_count > 3:
            streak_msg = StreakManager.get_streak_message(streak_count, streak_broken=True)
            await update.message.reply_text(streak_msg)

        # Update interaction score
        db_user.interaction_score += config.POINTS_PER_MESSAGE

        # Save user message to history
        await self.db.save_message(user.id, "user", message_text)

        # Get chat history
        chat_history = await self.db.get_chat_history(user.id, config.CONTEXT_WINDOW_SIZE)

        # Build context
        user_context = {
            "user_id": user.id,
            "username": db_user.username,
            "interaction_score": db_user.interaction_score,
            "streak_count": db_user.streak_count,
            "mood": db_user.mood_state,
            "personality": db_user.personality_mode,
            "temperature": 0.6 if db_user.personality_mode == "professional" else 0.8
        }

        # Prepare messages for LLM (convert ChatMessage objects to dicts)
        messages = [
            {"role": msg.role, "content": msg.message}
            for msg in chat_history
        ]

        # Send typing indicator
        await update.message.chat.send_action(action="typing")

        # Generate response using unified API manager
        response = await self.api_manager.generate_response(
            user_message=message_text,
            user_context=user_context,
            conversation_history=messages
        )

        # Save assistant response
        if response:
            await self.db.save_message(user.id, "assistant", response)

        # Update user in database
        await self.db.update_user(db_user)

        # Check for new achievements
        new_achievements = await self.achievement_manager.check_and_unlock(db_user)

        # Send response
        await update.message.reply_text(response)

        # Send achievement notifications
        for achievement in new_achievements:
            achievement_msg = AchievementManager.format_achievement_notification(achievement)
            await update.message.reply_text(achievement_msg, parse_mode='Markdown')

        # Streak reminder (if needed)
        if StreakManager.should_show_streak_reminder(db_user):
            reminder = f"⏰ Don't forget to chat tomorrow to maintain your {db_user.streak_count} day streak!"
            await update.message.reply_text(reminder)

    async def handle_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming images"""
        user = update.effective_user
        
        # Rate limiting
        is_allowed, remaining = await self.rate_limiter.check_rate_limit(user.id)
        if not is_allowed:
            await update.message.reply_text("❌ Rate limit exceeded. Please try again later.")
            return
        
        try:
            # Get image file
            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            
            # Check file size
            if photo.file_size > config.MAX_IMAGE_SIZE:
                await update.message.reply_text(
                    f"❌ Image too large (max {config.MAX_IMAGE_SIZE / 1024 / 1024:.1f}MB)"
                )
                return
            
            # Get or create user
            db_user = await self.db.get_or_create_user(user.id, user.username or user.first_name)
            
            # Get caption if provided
            caption = update.message.caption or "Analyze this image"
            
            # Send processing message
            processing_msg = await update.message.reply_text("🖼️ Processing your image...")
            
            # Download image
            image_data = await file.download_as_bytearray()
            
            # Build analysis prompt
            analysis_prompt = f"""Analyze this image in the style of {db_user.personality_mode} personality.
Keep your response under 500 characters. Focus on interesting details.

User's request: {caption}"""
            
            # Send typing indicator
            await update.message.chat.send_action(action="typing")
            
            # Generate response
            messages = [{"role": "user", "content": f"[Image provided]\n{analysis_prompt}"}]
            user_context = {
                "user_id": user.id,
                "username": db_user.username,
                "personality": db_user.personality_mode
            }
            
            response = await self.api_manager.generate_response(
                user_message=analysis_prompt,
                user_context=user_context,
                conversation_history=messages
            )
            
            # Save interaction
            db_user.interaction_score += config.POINTS_PER_MESSAGE
            await self.db.update_user(db_user)
            
            # Edit processing message with response
            await processing_msg.edit_text(f"🖼️ Analysis:\n\n{response}")
            
        except Exception as e:
            logger.error(f"Image handling error: {str(e)}", exc_info=True)
            await update.message.reply_text(f"❌ Error processing image: {str(e)}")

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming voice messages"""
        if not config.ENABLE_VOICE:
            await update.message.reply_text("❌ Voice messages are not enabled")
            return
        
        user = update.effective_user
        
        try:
            # Rate limiting
            is_allowed, remaining = await self.rate_limiter.check_rate_limit(user.id)
            if not is_allowed:
                await update.message.reply_text("❌ Rate limit exceeded")
                return
            
            # For now, just send a placeholder response
            # In production, you would use a speech-to-text API
            await update.message.reply_text(
                "🎤 Voice message received! "
                "(Speech-to-text integration coming soon)"
            )
            
        except Exception as e:
            logger.error(f"Voice handling error: {str(e)}")
            await update.message.reply_text("❌ Error processing voice message")