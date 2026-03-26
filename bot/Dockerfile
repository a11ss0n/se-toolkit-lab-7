# Bot Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy bot files
COPY bot/pyproject.toml bot/uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy bot source code
COPY bot/ ./

# Run the bot
CMD ["uv", "run", "bot.py"]
