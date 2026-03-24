#!/usr/bin/env python3
"""LMS Telegram Bot entry point.

Supports two modes:
1. Telegram bot mode (production) - runs the aiogram bot
2. CLI test mode (development) - runs handlers directly and prints output

Usage:
    uv run python -m bot              # Run as Telegram bot
    uv run python -m bot --test "/start"  # Test /start command
"""

import argparse
import asyncio
import logging
import sys
from typing import Any

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.config import settings
from bot.handlers import handle_help, handle_health, handle_labs, handle_start
from bot.handlers.commands import COMMAND_HANDLERS, HandlerContext

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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
    if handler is None:
        print(f"Error: Unknown command '{cmd}'", file=sys.stderr)
        print(f"Available commands: {', '.join(COMMAND_HANDLERS.keys())}", file=sys.stderr)
        return 1

    # Run handler
    ctx = create_handler_context()
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
        logger.error("Or run in test mode: uv run python -m bot --test '/start'")
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
            "/start, /help, /health, /labs"
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
  uv run python -m bot                 Run as Telegram bot
  uv run python -m bot --test "/start" Test /start command
  uv run python -m bot --test "/help"  Test /help command
  uv run python -m bot --test "/labs"  Test /labs command
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
