from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class Keyboards:
    @staticmethod
    def get_main_menu() -> InlineKeyboardMarkup:
        """Main menu keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("💬 Chat", callback_data="menu_chat"),
                InlineKeyboardButton("🧠 Memory", callback_data="menu_memory")
            ],
            [
                InlineKeyboardButton("🎭 Personality", callback_data="menu_personality"),
                InlineKeyboardButton("🤖 AI Model", callback_data="menu_llm")
            ],
            [
                InlineKeyboardButton("🏆 Achievements", callback_data="menu_achievements"),
                InlineKeyboardButton("📊 Stats", callback_data="menu_stats")
            ],
            [
                InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_personality_menu(current: str) -> InlineKeyboardMarkup:
        """Personality selection keyboard"""
        personalities = [
            ("😊 Friendly", "personality_friendly"),
            ("💼 Professional", "personality_professional"),
            ("💪 Motivational", "personality_motivational"),
            ("😏 Sarcastic", "personality_sarcastic")
        ]

        keyboard = []
        for name, callback in personalities:
            # Add checkmark for current personality
            if callback.split("_")[1] == current:
                name = f"✅ {name}"
            keyboard.append([InlineKeyboardButton(name, callback_data=callback)])

        keyboard.append([InlineKeyboardButton("« Back to Menu", callback_data="menu_main")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_llm_menu(current: str) -> InlineKeyboardMarkup:
        """LLM provider selection keyboard"""
        providers = [
            ("🤖 OpenAI (ChatGPT)", "llm_openai"),
            ("🧠 Claude (Anthropic)", "llm_claude"),
            ("✨ Gemini (Google)", "llm_gemini"),
            ("💻 Local LLM", "llm_local")
        ]

        keyboard = []
        for name, callback in providers:
            # Add checkmark for current provider
            if callback.split("_")[1] == current:
                name = f"✅ {name}"
            keyboard.append([InlineKeyboardButton(name, callback_data=callback)])

        keyboard.append([InlineKeyboardButton("« Back to Menu", callback_data="menu_main")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_settings_menu() -> InlineKeyboardMarkup:
        """Settings menu keyboard"""
        keyboard = [
            [InlineKeyboardButton("🗑 Clear History", callback_data="settings_clear_history")],
            [InlineKeyboardButton("🔄 Reset Streak", callback_data="settings_reset_streak")],
            [InlineKeyboardButton("ℹ️ About", callback_data="settings_about")],
            [InlineKeyboardButton("« Back to Menu", callback_data="menu_main")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_confirmation_keyboard(action: str) -> InlineKeyboardMarkup:
        """Confirmation keyboard for destructive actions"""
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_{action}"),
                InlineKeyboardButton("❌ Cancel", callback_data="menu_settings")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def get_back_button() -> InlineKeyboardMarkup:
        """Simple back button"""
        keyboard = [[InlineKeyboardButton("« Back to Menu", callback_data="menu_main")]]
        return InlineKeyboardMarkup(keyboard)