# Lab 7 — Build a Client with an AI Coding Agent

[Sync your fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/syncing-a-fork#syncing-a-fork-branch-from-the-command-line) regularly — the lab gets updated.

## Product brief

> Build a Telegram bot that lets users interact with the LMS backend through chat. Users should be able to check system health, browse labs and scores, and ask questions in plain language. The bot should use an LLM to understand what the user wants and fetch the right data. Deploy it alongside the existing backend on the VM.

This is what a customer might tell you. Your job is to turn it into a working product using an AI coding agent (Qwen Code) as your development partner.

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  ┌──────────────┐     ┌──────────────────────────────────┐   │
│  │  Telegram    │────▶│  Your Bot                        │   │
│  │  User        │◀────│  (aiogram / python-telegram-bot) │   │
│  └──────────────┘     └──────┬───────────────────────────┘   │
│                              │                               │
│                              │ slash commands + plain text    │
│                              ├───────▶ /start, /help         │
│                              ├───────▶ /health, /labs        │
│                              ├───────▶ intent router ──▶ LLM │
│                              │                    │          │
│                              │                    ▼          │
│  ┌──────────────┐     ┌──────┴───────┐    tools/actions      │
│  │  Docker      │     │  LMS Backend │◀───── GET /items      │
│  │  Compose     │     │  (FastAPI)   │◀───── GET /analytics  │
│  │              │     │  + PostgreSQL│◀───── POST /sync      │
│  └──────────────┘     └──────────────┘                       │
└──────────────────────────────────────────────────────────────┘
```

## Requirements

### P0 — Must have

1. Testable handler architecture — handlers work without Telegram
2. CLI test mode: `cd bot && uv run bot.py --test "/command"` prints response to stdout
3. `/start` — welcome message
4. `/help` — lists all available commands
5. `/health` — calls backend, reports up/down status
6. `/labs` — lists available labs
7. `/scores <lab>` — per-task pass rates
8. Error handling — backend down produces a friendly message, not a crash

### P1 — Should have

1. Natural language intent routing — plain text interpreted by LLM
2. All 9 backend endpoints wrapped as LLM tools
3. Inline keyboard buttons for common actions
4. Multi-step reasoning (LLM chains multiple API calls)

### P2 — Nice to have

1. Rich formatting (tables, charts as images)
2. Response caching
3. Conversation context (multi-turn)

### P3 — Deployment

1. Bot containerized with Dockerfile
2. Added as service in `docker-compose.yml`
3. Deployed and running on VM
4. README documents deployment

## Learning advice

Notice the progression above: **product brief** (vague customer ask) → **prioritized requirements** (structured) → **task specifications** (precise deliverables + acceptance criteria). This is how engineering work flows.

You are not following step-by-step instructions — you are building a product with an AI coding agent. The learning comes from planning, building, testing, and debugging iteratively.

## Learning outcomes

By the end of this lab, you should be able to say:

1. I turned a vague product brief into a working Telegram bot.
2. I can ask it questions in plain language and it fetches the right data.
3. I used an AI coding agent to plan and build the whole thing.

## Tasks

### Prerequisites

1. Complete the [lab setup](./lab/setup/setup-simple.md#lab-setup)

> **Note**: First time in this course? Do the [full setup](./lab/setup/setup-full.md#lab-setup) instead.

### Required

1. [Plan and Scaffold](./lab/tasks/required/task-1.md) — P0: project structure + `--test` mode
2. [Backend Integration](./lab/tasks/required/task-2.md) — P0: slash commands + real data
3. [Intent-Based Natural Language Routing](./lab/tasks/required/task-3.md) — P1: LLM tool use
4. [Containerize and Document](./lab/tasks/required/task-4.md) — P3: containerize + deploy

### Optional

1. [Flutter Web Chatbot](./lab/tasks/optional/task-1.md)

## Deploy

### Prerequisites

- Docker and Docker Compose installed on VM
- `.env.docker.secret` file with required environment variables

### Required environment variables

Create `.env.docker.secret` in the project root with:

```bash
# Telegram Bot
BOT_TOKEN=your-bot-token-from-botfather

# LMS Backend
LMS_API_KEY=your-lms-api-key
LMS_API_BASE_URL=http://backend:8000

# LLM API
LLM_API_BASE_URL=http://localhost:42005  # or your LLM proxy URL
LLM_API_KEY=your-llm-api-key
LLM_API_MODEL=your-model-name

# Other required vars (from existing .env.docker.secret.example)
BACKEND_HOST_ADDRESS=127.0.0.1
BACKEND_HOST_PORT=42002
BACKEND_CONTAINER_PORT=8000
BACKEND_NAME=lms-backend
BACKEND_DEBUG=false
BACKEND_CONTAINER_ADDRESS=0.0.0.0
BACKEND_ENABLE_INTERACTIONS=true
BACKEND_ENABLE_LEARNERS=true
AUTOCHECKER_API_URL=http://localhost:42001
AUTOCHECKER_API_LOGIN=admin
AUTOCHECKER_API_PASSWORD=admin
CONST_POSTGRESQL_SERVICE_NAME=postgres
CONST_POSTGRESQL_DEFAULT_PORT=5432
POSTGRES_DB=lms
POSTGRES_USER=lms
POSTGRES_PASSWORD=your-password
POSTGRES_HOST_ADDRESS=127.0.0.1
POSTGRES_HOST_PORT=42004
PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=admin
LMS_API_HOST_ADDRESS=127.0.0.1
LMS_API_HOST_PORT=42002
CADDY_CONTAINER_PORT=80
QWEN_CODE_API_URL=http://localhost:42005
```

### Deploy commands

```bash
# SSH to VM
ssh root@your-vm-ip

# Navigate to project
cd ~/se-toolkit-lab-7

# Pull latest changes
git pull origin main

# Stop any running bot processes (if running outside Docker)
pkill -f "bot.py" 2>/dev/null || true

# Build and start all services
docker compose --env-file .env.docker.secret up --build -d

# Check status
docker compose --env-file .env.docker.secret ps

# View bot logs
docker compose --env-file .env.docker.secret logs bot --tail 50

# View all logs
docker compose --env-file .env.docker.secret logs --tail 20
```

### Verify deployment

1. **Check containers are running:**
   ```bash
   docker ps | grep se-toolkit
   ```
   Should show: backend, postgres, pgadmin, caddy, bot

2. **Check backend health:**
   ```bash
   curl -sf http://localhost:42002/items/ | head -c 200
   ```

3. **Test bot in Telegram:**
   - `/start` — welcome message
   - `/health` — backend status
   - "what labs are available?" — natural language query
   - "which lab has the lowest pass rate?" — multi-step reasoning

### Troubleshooting

**Bot container keeps restarting:**
```bash
docker compose logs bot --tail 50
```
Check for missing env vars or import errors.

**LLM queries fail:**
Ensure `LLM_API_BASE_URL` points to your LLM proxy (not localhost if running in Docker).

**Backend connection fails:**
Ensure `LMS_API_BASE_URL=http://backend:8000` (Docker service name, not localhost).

### Update deployment

```bash
cd ~/se-toolkit-lab-7
git pull origin main
docker compose --env-file .env.docker.secret up --build -d
```
