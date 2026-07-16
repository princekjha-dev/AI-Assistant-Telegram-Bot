# 🤖 Nexus — Self-Hosted Telegram AI Assistant

<div align="center">

```
███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗
████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝
██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗
██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║
██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║
╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
```

**A fully self-hosted, production-ready Telegram AI companion.**  
ChatGPT-style conversations • Memory • Image Generation • Voice • Gamification

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram&logoColor=white)

</div>

---

## ✨ Features

### 🧠 AI Chat Engine
- **OpenRouter** integration — access 100+ LLMs (Claude, GPT-4o, Gemini, Llama, Mistral...)
- **Persistent Memory** — remembers facts about you across conversations
- **Conversation Summaries** — auto-compresses long chats to save tokens
- **Context Window** — keeps last N messages for coherent conversations
- **Auto Memory Extraction** — learns from conversations automatically

### 🎭 Personality System (5 modes)
| Personality | Style |
|---|---|
| 😊 Friendly | Warm, casual, supportive |
| 💼 Professional | Concise, business-focused |
| 🔥 Motivational | Energetic coach |
| 😏 Sarcastic | Witty and playful |
| 🎨 Creative | Imaginative, artistic |

### 🎨 Multimodal Features
- **Image Generation** — `/image a cyberpunk city at night`
- **Voice Messages** — transcribe and reply to voice notes
- **File Analysis** — PDFs, text, code, documents
- **Photo Analysis** — describe and ask questions about images

### 💬 Conversation Management
- Multiple conversations per user
- Conversation history browsing
- Export conversations as JSON
- **Branching** — fork conversation at any point
- Auto-titling

### ⏰ Reminder System
- Natural language: _"Remind me tomorrow at 9am to call John"_
- Recurring: daily, weekly, monthly
- Background scheduler — fires reminders even while chatting

### 🏆 Gamification
- **XP & Points** for every interaction
- **Levels** (1 level per 100 XP)
- **Daily Streaks** with bonus rewards
- **16 Achievements** to unlock
- **Global Leaderboard**

### 👥 Group Chat Support
- Responds only when @mentioned
- Per-user tracking in groups
- Group leaderboard

### 🛡️ Safety & Limits
- Per-user rate limiting (per-minute and daily)
- Configurable limits via environment variables

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.12+
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- An OpenRouter API Key (from [openrouter.ai](https://openrouter.ai))

### 2. Clone & Configure

```bash
git clone https://github.com/your-username/nexus-bot
cd nexus-bot

# Copy example config
cp .env.example .env

# Edit .env — only two required fields:
# TELEGRAM_BOT_TOKEN=your_token_here
# OPENROUTER_API_KEY=your_key_here
nano .env
```

### 3. Install & Run

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the bot
python main.py
```

You should see the Nexus ASCII banner and `Nexus is running!` in the logs.

---

## 🐳 Docker Deployment

### Polling Mode (simplest)

```bash
# Copy and fill in your .env
cp .env.example .env
nano .env

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f nexus
```

### Webhook Mode (production)

```bash
# In .env, set:
# MODE=webhook
# WEBHOOK_URL=https://yourdomain.com
# WEBHOOK_PORT=8443
# WEBHOOK_SECRET=some_random_secret

# In docker-compose.yml, uncomment the ports section:
# ports:
#   - "8443:8443"

docker-compose up -d
```

> **Note:** For webhook mode, your server must have a valid SSL certificate and be accessible from the internet.

---

## ⚙️ Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | **required** | Your Telegram bot token |
| `OPENROUTER_API_KEY` | **required** | Your OpenRouter API key |
| `OPENROUTER_MODEL` | `anthropic/claude-3.5-sonnet` | Default AI model |
| `DATABASE_URL` | `sqlite:///data/nexus.db` | Database connection URL |
| `MODE` | `polling` | `polling` or `webhook` |
| `WEBHOOK_URL` | — | Public HTTPS URL (webhook mode) |
| `WEBHOOK_PORT` | `8443` | Port for webhook server |
| `MAX_TOKENS` | `2048` | Max tokens per LLM response |
| `TEMPERATURE` | `0.7` | LLM temperature (0-1) |
| `CONTEXT_WINDOW` | `20` | Recent messages kept in context |
| `RATE_LIMIT_ENABLED` | `true` | Enable/disable rate limiting |
| `MAX_REQUESTS_PER_MINUTE` | `20` | Per-user per-minute limit |
| `MAX_REQUESTS_PER_DAY` | `500` | Per-user daily limit |
| `IMAGE_GENERATION_ENABLED` | `true` | Enable image generation |
| `IMAGE_MODEL` | `black-forest-labs/flux-schnell` | Image generation model |
| `VOICE_ENABLED` | `true` | Enable voice message handling |
| `GAMIFICATION_ENABLED` | `true` | Enable XP/achievements |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FILE` | `logs/nexus.log` | Log file path |
| `ADMIN_USER_IDS` | — | Comma-separated admin Telegram IDs |

---

## 📋 Command Reference

| Command | Description |
|---|---|
| `/start` | Welcome message & main menu |
| `/help` | Full command reference |
| `/about` | About Nexus |
| `/chat <msg>` | Chat with AI |
| `/new` | Start new conversation |
| `/history` | Browse conversations |
| `/export` | Export conversation as JSON |
| `/branch` | Fork current conversation |
| `/personality` | Change AI personality |
| `/setpersonality <name>` | Set personality directly |
| `/model` | View/change AI model |
| `/settings` | Bot settings |
| `/memory` | View your memories |
| `/memoryadd <fact>` | Add a memory fact |
| `/memoryclear` | Clear all memories |
| `/image <prompt>` | Generate an image |
| `/remind <text>` | Set a reminder |
| `/reminders` | List pending reminders |
| `/delreminder <id>` | Delete a reminder |
| `/profile` | Your profile & stats |
| `/stats` | Detailed statistics |
| `/achievements` | View achievements |
| `/leaderboard` | Global leaderboard |

---

## 🏗️ Architecture

```
nexus/
├── app/
│   ├── ai/
│   │   ├── client.py        # OpenRouter async HTTP client
│   │   ├── engine.py        # Chat orchestration & context building
│   │   └── personalities.py # 5 personality definitions
│   ├── bot/
│   │   ├── app.py           # Application wiring & startup
│   │   ├── helpers.py       # Shared formatters & keyboards
│   │   ├── handlers/
│   │   │   ├── start.py        # /start, /help, /about
│   │   │   ├── chat.py         # Core message handling
│   │   │   ├── personality.py  # /personality
│   │   │   ├── memory.py       # /memory, /memoryadd
│   │   │   ├── image.py        # /image
│   │   │   ├── voice.py        # Voice messages
│   │   │   ├── files.py        # Documents & photos
│   │   │   ├── reminders.py    # /remind, /reminders
│   │   │   ├── profile.py      # /profile, /achievements, /leaderboard
│   │   │   ├── conversations.py # /new, /history, /export, /branch
│   │   │   ├── settings.py     # /settings, /model
│   │   │   └── callbacks.py    # All inline button handlers
│   │   └── middleware/
│   │       └── rate_limit.py   # Sliding window rate limiter
│   ├── config/
│   │   ├── settings.py      # Pydantic settings (env vars)
│   │   └── logging_config.py
│   ├── database/
│   │   ├── models.py        # SQLAlchemy ORM models
│   │   ├── engine.py        # Async session factory
│   │   └── repositories.py  # Data access layer
│   ├── gamification/
│   │   └── service.py       # XP, points, streaks, achievements
│   ├── media/
│   │   └── service.py       # PDF/text extraction, audio conversion
│   ├── reminders/
│   │   └── service.py       # Reminder CRUD & AI parsing
│   └── services/
│       └── scheduler.py     # Background reminder loop
├── tests/
│   ├── test_personalities.py
│   ├── test_media.py
│   ├── test_gamification.py
│   └── test_rate_limit.py
├── main.py                  # Entry point
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

### Data Flow

```
User Message → Rate Limiter → Message Handler
                                    ↓
                          Get/Create User (DB)
                                    ↓
                     Build Context (memories + history)
                                    ↓
                       OpenRouter API Call (LLM)
                                    ↓
                      Save Messages (DB) → Award XP
                                    ↓
                    Check Achievements → Send Response
                                    ↓
                   Auto-extract Memories (background)
```

---

## 🧪 Running Tests

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

---

## 🔧 Extending Nexus

### Adding a New Personality

In `app/ai/personalities.py`:

```python
PERSONALITIES["zen"] = Personality(
    key="zen",
    name="Zen",
    icon="🧘",
    description="Calm and mindful",
    system_prompt="You are Nexus, a calm and mindful AI...",
    greeting="🧘 Breathe. I'm here. What's on your mind?",
)
```

### Adding a New Achievement

In `app/gamification/service.py`, add to `ACHIEVEMENT_DEFINITIONS`:

```python
{"key": "night_owl", "name": "Night Owl", "description": "Chatted after midnight", "icon": "🦉", "points_reward": 30}
```

Then add the condition check in `_check_achievements()`.

### Using a Different LLM

Set in `.env`:
```
OPENROUTER_MODEL=openai/gpt-4o
```

Or a user can change it with `/model`.

---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with ❤️ using [python-telegram-bot](https://python-telegram-bot.org/) & [OpenRouter](https://openrouter.ai)

</div>
