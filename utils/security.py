import re


class SecurityValidator:
    # Patterns that might indicate prompt injection attempts
    SUSPICIOUS_PATTERNS = [
        r'ignore\s+(all\s+)?previous\s+instructions',
        r'forget\s+(all\s+)?previous\s+instructions',
        r'system\s*:\s*you\s+are',
        r'new\s+instructions',
        r'disregard\s+.+\s+instructions',
        r'override\s+.+\s+settings',
        r'<\s*system\s*>',
        r'<\s*/?\s*instruction\s*>',
    ]

    MAX_MESSAGE_LENGTH = 4000

    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        Sanitize user input by removing potentially harmful content.
        """
        if not text:
            return ""

        # Limit length
        if len(text) > SecurityValidator.MAX_MESSAGE_LENGTH:
            text = text[:SecurityValidator.MAX_MESSAGE_LENGTH] + "..."

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    @staticmethod
    def is_suspicious(text: str) -> bool:
        """
        Check if text contains suspicious patterns that might be injection attempts.
        """
        text_lower = text.lower()

        for pattern in SecurityValidator.SUSPICIOUS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True

        return False

    @staticmethod
    def validate_message(text: str) -> tuple[bool, str]:
        """
        Validate message and return (is_valid, error_message).
        """
        if not text or len(text.strip()) == 0:
            return False, "Message cannot be empty"

        if len(text) > SecurityValidator.MAX_MESSAGE_LENGTH:
            return False, f"Message too long (max {SecurityValidator.MAX_MESSAGE_LENGTH} characters)"

        if SecurityValidator.is_suspicious(text):
            return False, "Message contains suspicious content"

        return True, ""