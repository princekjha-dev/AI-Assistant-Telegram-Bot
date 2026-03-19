# AI Assistant Telegram Bot

A powerful, feature-rich Telegram bot powered by OpenRouter AI with image generation, personality modes, mood detection, and gamification.

## 🚀 Features

- **Multi-Model AI Support**: OpenRouter integration supporting GPT-4, Claude, Llama, and more
- **Image Generation**: Generate images from text descriptions (Stable Diffusion, DALL-E compatible)
- **Personality Modes**: Friendly, Professional, Motivational, Sarcastic, Creative
- **Mood Detection**: AI adapts responses based on detected user mood
- **Persistent Memory**: Long-term conversation context with summarization
- **Gamification**: Streaks, achievements, points system, leaderboards
- **Rate Limiting**: Built-in protection against spam and abuse
- **Security**: Input validation, sanitization, and authentication
- **Analytics**: Track user engagement and interactions
- **Multi-Language Support**: Extensible to support multiple languages

## 📋 Prerequisites

- Python 3.9+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- OpenRouter API Key (from [openrouter.ai](https://openrouter.ai))
- Optional: Hugging Face or Replicate API key for image generation

## 🔧 Installation

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/ai-bot
cd ai-bot
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Required configuration:
```env
TELEGRAM_BOT_TOKEN=your_token_here
OPENROUTER_API_KEY=your_key_here
```

### 5. Run Bot
```bash
python main.py
```

## 🐳 Docker Installation

### Using Docker Compose (Recommended)
```bash
docker-compose up -d
```

### Manual Docker Build
```bash
docker build -t ai-bot .
docker run -d --name ai-bot --env-file .env -v $(pwd)/data:/app/data ai-bot
```

## 📱 Bot Commands

### Basic Commands
- `/start` - Start the bot
- `/menu` - Open main menu
- `/help` - Show available commands
- `/stats` - View your statistics
- `/achievements` - View achievements

### Advanced Commands
- `/imagine [description]` - Generate an image
- `/model [name]` - Change AI model (gpt4, claude, llama)
- `/personality [mode]` - Change personality (friendly, professional, motivational, sarcastic, creative)
- `/clear` - Clear chat history
- `/settings` - View and modify settings

## ⚙️ Configuration

Edit `.env` file to configure:

### API Keys
```env
TELEGRAM_BOT_TOKEN=your_token
OPENROUTER_API_KEY=your_key
HF_API_TOKEN=your_huggingface_token  # For image generation
```

### Models
```env
PRIMARY_MODEL=openai/gpt-4-turbo
FALLBACK_MODEL=anthropic/claude-3-sonnet
LIGHTWEIGHT_MODEL=meta-llama/llama-2-70b-chat
```

### Features
```env
ENABLE_IMAGE_GENERATION=true
ENABLE_VOICE=true
ENABLE_WEB_SEARCH=false
ENABLE_ANALYTICS=true
```

### Performance
```env
MAX_RESPONSE_TOKENS=2000
TEMPERATURE=0.7
CONTEXT_WINDOW_SIZE=10
RATE_LIMIT_REQUESTS=30
RATE_LIMIT_WINDOW=60
```

## 📊 Database

Bot uses SQLite for local data storage:
- `data/bot_database.db` - Main database
- `data/backups/` - Automatic backups
- `data/media/` - User media storage
- `data/generated_images/` - Generated image cache

## 📈 Project Structure

```
bot/
├── ai/                    # AI modules
│   ├── image_generator.py # Image generation
│   ├── memory_manager.py  # Conversation memory
│   ├── mood_detector.py   # Mood analysis
│   └── prompt_builder.py  # Prompt construction
├── database/              # Database layer
│   ├── db.py             # Database operations
│   └── models.py         # Data models
├── handlers/              # Telegram handlers
│   ├── commands.py       # Command handlers
│   ├── messages.py       # Message handlers
│   └── callbacks.py      # Callback handlers
├── llm/                   # LLM integrations
│   ├── base.py           # Base class
│   ├── openrouter.py     # OpenRouter client
│   └── claude.py         # Claude client
├── gamification/          # Gamification features
│   ├── achievements.py   # Achievement system
│   └── streaks.py        # Streak tracking
├── ui/                    # UI components
│   ├── keyboards.py      # Inline keyboards
│   └── menus.py          # Menu messages
├── utils/                 # Utilities
│   ├── rate_limit.py     # Rate limiting
│   └── security.py       # Security validation
├── main.py               # Entry point
├── config.py             # Configuration
├── requirements.txt      # Dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose config
└── .env.example          # Environment template
```

## 🚀 Deployment

### Local Deployment
```bash
python main.py
```

### Production with Gunicorn
```bash
gunicorn -w 1 -b 0.0.0.0:8080 main:app
```

### Docker Deployment
```bash
docker-compose up -d
```

### Webhook Mode (For High Traffic)
Update `.env`:
```env
POLLING_MODE=false
WEBHOOK_URL=https://your-domain.com/webhook
```

## 🔒 Security Features

- **Input Validation**: All user inputs validated
- **Rate Limiting**: Prevents API abuse
- **SQL Injection Prevention**: Parameterized queries
- **XSS Protection**: Content sanitization
- **Authentication**: Telegram-based user authentication
- **API Key Protection**: Environment-based credential management

## 📊 Analytics

The bot tracks:
- User interactions
- Conversation topics
- Feature usage
- Performance metrics
- Error rates

Access analytics via `/stats` command.

## 🐛 Troubleshooting

### Bot not responding
1. Check TELEGRAM_BOT_TOKEN is correct
2. Ensure OPENROUTER_API_KEY is valid
3. Check logs: `tail -f logs/bot.log`

### Image generation fails
1. Verify HF_API_TOKEN or REPLICATE_API_TOKEN
2. Check image storage permissions
3. Verify ENABLE_IMAGE_GENERATION=true

### Rate limiting issues
1. Increase RATE_LIMIT_REQUESTS in .env
2. Adjust RATE_LIMIT_WINDOW if needed

### Database errors
1. Check database file permissions
2. Verify data/ directory exists
3. Review SQLite logs

## 📝 Logging

Logs are stored in `logs/bot.log`. Configure logging level:
```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## 🤝 Contributing

Contributions welcome! Please:
1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open pull request

## 📄 License

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
