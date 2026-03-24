#!/usr/bin/env python3
"""LMS Telegram Bot entry point.

Supports two modes:
1. Telegram bot mode (production) - runs the aiogram bot
2. CLI test mode (development) - runs handlers directly and prints output

Usage:
    cd bot && uv run bot.py              # Run as Telegram bot
    cd bot && uv run bot.py --test "/start"  # Test /start command

Note: For module-style imports to work, run from the parent directory:
    uv run python -m bot --test "/start"
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path for imports when running as script
_script_dir = Path(__file__).parent
if str(_script_dir.parent) not in sys.path:
    sys.path.insert(0, str(_script_dir.parent))

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.config import settings
from bot.handlers import handle_help, handle_health, handle_labs, handle_scores, handle_start
from bot.handlers.commands import COMMAND_HANDLERS, HandlerContext

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Suppress httpx INFO logs (they clutter test output)
logging.getLogger("httpx").setLevel(logging.WARNING)


def create_handler_context() -> HandlerContext:
    """Create handler context from settings."""
    return HandlerContext(
        lms_api_base_url=settings.lms_api_base_url,
        lms_api_key=settings.lms_api_key,
        llm_api_base_url=settings.llm_api_base_url,
        llm_api_key=settings.llm_api_key,
        llm_api_model=settings.llm_api_model,
    )


async def run_test_mode(command: str) -> int:
    """Run a command in test mode and print the result.

    Args:
        command: Command string like "/start" or "/labs arg1 arg2"

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Parse command
    parts = command.strip().split()
    if not parts:
        print("Error: Empty command", file=sys.stderr)
        return 1

    cmd = parts[0]
    if cmd.startswith("/"):
        cmd = cmd[1:]

    args = " ".join(parts[1:]) if len(parts) > 1 else ""

    # Find handler
    handler = COMMAND_HANDLERS.get(cmd)
    ctx = create_handler_context()
    
    if handler is None:
        # Unknown command - print helpful message and exit with code 0
        print(f"❓ Неизвестная команда: '{cmd}'\n")
        print("Доступные команды:")
        for name in sorted(COMMAND_HANDLERS.keys()):
            print(f"  /{name}")
        print("\nПопробуйте /help для получения справки.")
        return 0

    # Run handler
    try:
        result = await handler(ctx, args)
        print(result)
        return 0
    except Exception as e:
        print(f"Error executing command: {e}", file=sys.stderr)
        return 1


async def run_telegram_bot() -> None:
    """Run the Telegram bot."""
    if settings.is_test_mode:
        logger.error("BOT_TOKEN is not set. Please set it in .env.bot.secret")
        logger.error("Or run in test mode: uv run bot.py --test '/start'")
        sys.exit(1)

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    ctx = create_handler_context()

    @dp.message(CommandStart())
    async def cmd_start(message: Message) -> None:
        """Handle /start command."""
        result = await handle_start(ctx)
        await message.answer(result)

    @dp.message(Command("help"))
    async def cmd_help(message: Message) -> None:
        """Handle /help command."""
        result = await handle_help(ctx)
        await message.answer(result)

    @dp.message(Command("health"))
    async def cmd_health(message: Message) -> None:
        """Handle /health command."""
        result = await handle_health(ctx)
        await message.answer(result)

    @dp.message(Command("labs"))
    async def cmd_labs(message: Message) -> None:
        """Handle /labs command."""
        result = await handle_labs(ctx)
        await message.answer(result)

    @dp.message(Command("scores"))
    async def cmd_scores(message: Message) -> None:
        """Handle /scores command."""
        # Extract lab argument from command
        args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
        result = await handle_scores(ctx, args)
        await message.answer(result)

    @dp.message()
    async def handle_message(message: Message) -> None:
        """Handle natural language messages via LLM intent routing.

        TODO: Implement LLM-based intent classification.
        For now, respond with a hint to use commands.
        """
        # TODO: Call LLM to classify intent and extract parameters
        # For now, just suggest using commands
        await message.answer(
            "Я пока учусь понимать естественный язык. 🤔\n\n"
            "Попробуйте использовать команды:\n"
            "/start, /help, /health, /labs, /scores"
        )

    logger.info("Starting bot...")
    await dp.start_polling(bot)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="LMS Telegram Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run bot.py                 Run as Telegram bot
  uv run bot.py --test "/start" Test /start command
  uv run bot.py --test "/help"  Test /help command
  uv run bot.py --test "/labs"  Test /labs command
""",
    )
    parser.add_argument(
        "--test",
        metavar="COMMAND",
        help="Run a command in test mode (e.g., '/start')",
    )

    args = parser.parse_args()

    if args.test:
        return asyncio.run(run_test_mode(args.test))
    else:
        asyncio.run(run_telegram_bot())
        return 0


if __name__ == "__main__":
    sys.exit(main())
