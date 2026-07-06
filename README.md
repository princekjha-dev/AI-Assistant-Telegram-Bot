# AI Assistant Telegram Bot

A production-oriented Telegram AI assistant built with Python, `python-telegram-bot`, OpenRouter, and SQLite.

## Features
- Async Telegram bot with polling or webhook mode
- OpenRouter chat completions with runtime model switching
- Rolling conversation memory with compact historical summaries
- Durable per-user memories via `/remember`, `/forget`, and `/memories`
- Image generation and a simple image-analysis flow
- Reminder, export, invite, and admin commands
- SQLite-backed persistence and a modular service layer

## Setup
1. Copy [.env.example](.env.example) to `.env` and fill in the required values.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the bot:
   ```bash
   python main.py
   ```

## Run modes
- Polling:
  ```bash
  RUN_MODE=polling
  ```
- Webhook:
  ```bash
  RUN_MODE=webhook
  WEBHOOK_URL=https://your-domain.example.com
  WEBHOOK_SECRET_TOKEN=change-me
  ```

## Group mode
Add the bot to a group and mention it or reply to its messages to have it respond. Configure group-specific rate limiting and admin restrictions in the service layer as you extend the bot.

## Adding a new feature
- Commands live in [handlers/commands.py](handlers/commands.py)
- Message handling lives in [handlers/messages.py](handlers/messages.py)
- LLM integrations live in [llm/openrouter.py](llm/openrouter.py)
- Persistent business logic lives in [services/assistant_service.py](services/assistant_service.py)

## Docker Compose
```bash
docker compose up --build
```

MIT License - see LICENSE file for details

## 📧 Support

- Issues: GitHub Issues
- Questions: Open Discussion
- Email: support@example.com

## 🙏 Acknowledgments

- [OpenRouter](https://openrouter.ai) - AI model routing
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram integration
- [Anthropic](https://anthropic.com) - Claude API
- [OpenAI](https://openai.com) - GPT models
- [Hugging Face](https://huggingface.co) - Transformers & inference

## 🔗 Useful Links

- [Telegram Bot API](https://core.telegram.org/bots)
- [OpenRouter Documentation](https://openrouter.ai/docs)
- [python-telegram-bot Documentation](https://python-telegram-bot.readthedocs.io/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)

---

**Last Updated**: January 2026  
**Version**: 2.0  
**Status**: Production Ready
