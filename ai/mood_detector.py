import re


class MoodDetector:
    MOOD_KEYWORDS = {
        "happy": [
            r'\bhappy\b', r'\bjoy\b', r'\bexcited\b', r'\bgreat\b', r'\bawesome\b',
            r'\bamazing\b', r'\bwonderful\b', r'\bfantastic\b', r'\blove\b', r'\byay\b',
            r':\)', r'😊', r'😄', r'😃', r'🎉', r'❤️', r'haha', r'lol'
        ],
        "sad": [
            r'\bsad\b', r'\bdepressed\b', r'\bunhappy\b', r'\bmiserable\b', r'\bdown\b',
            r'\blonely\b', r'\bcrying\b', r'\btears\b', r'\bhurt\b', r'\bpain\b',
            r':\(', r'😢', r'😭', r'😞', r'💔'
        ],
        "stressed": [
            r'\bstress\b', r'\banxious\b', r'\bworried\b', r'\bpressure\b', r'\boverwhelmed\b',
            r'\bbusy\b', r'\btired\b', r'\bexhausted\b', r'\bfrustrated\b', r'\bdeadline\b',
            r'😰', r'😫', r'😩'
        ],
        "angry": [
            r'\bangry\b', r'\bmad\b', r'\bfurious\b', r'\bpissed\b', r'\bannoyed\b',
            r'\birritated\b', r'\brage\b', r'\bhate\b', r'\bwtf\b', r'\bdamn\b',
            r'😠', r'😡', r'🤬'
        ]
    }

    @staticmethod
    def detect_mood(text: str) -> str:
        """
        Detect user mood from text using keyword matching.
        Returns: happy, sad, stressed, angry, or neutral
        """
        text_lower = text.lower()
        mood_scores = {mood: 0 for mood in MoodDetector.MOOD_KEYWORDS.keys()}

        for mood, patterns in MoodDetector.MOOD_KEYWORDS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    mood_scores[mood] += 1

        # Find mood with highest score
        max_score = max(mood_scores.values())
        if max_score > 0:
            for mood, score in mood_scores.items():
                if score == max_score:
                    return mood

        return "neutral"

    @staticmethod
    def get_mood_emoji(mood: str) -> str:
        """Get emoji representation of mood"""
        mood_emojis = {
            "happy": "😊",
            "sad": "😢",
            "stressed": "😰",
            "angry": "😠",
            "neutral": "😐"
        }
        return mood_emojis.get(mood, "😐")