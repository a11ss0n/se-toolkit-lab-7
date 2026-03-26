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
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import settings
from bot.handlers import (
    handle_groups,
    handle_help,
    handle_health,
    handle_labs,
    handle_natural_language,
    handle_scores,
    handle_start,
    handle_top_learners,
)
from bot.handlers.commands import COMMAND_HANDLERS, HandlerContext

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Suppress httpx INFO logs (they clutter test output)
logging.getLogger("httpx").setLevel(logging.WARNING)


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Create main inline keyboard with common actions."""
    builder = InlineKeyboardBuilder()
    
    # Row 1: Labs and Scores
    builder.button(text="📋 Labs", callback_data="labs")
    builder.button(text="📊 Scores lab-04", callback_data="scores_lab-04")
    
    # Row 2: Top learners and Groups
    builder.button(text="🏆 Top 5 students", callback_data="top5_lab-04")
    builder.button(text="👥 Groups lab-03", callback_data="groups_lab-03")
    
    # Row 3: Help and Health
    builder.button(text="❓ Help", callback_data="help")
    builder.button(text="💚 Health", callback_data="health")
    
    builder.adjust(2, 2, 2)  # 2 buttons per row
    return builder.as_markup()


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with back button."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Back to menu", callback_data="back")
    return builder.as_markup()


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
        command: Command string like "/start" or "/labs arg1 arg2" or plain text

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Parse command
    parts = command.strip().split()
    if not parts:
        print("Error: Empty command", file=sys.stderr)
        return 1

    ctx = create_handler_context()
    cmd = parts[0]

    # Check if it's a slash command
    if cmd.startswith("/"):
        cmd = cmd[1:]
        args = " ".join(parts[1:]) if len(parts) > 1 else ""

        # Find handler
        handler = COMMAND_HANDLERS.get(cmd)

        if handler is None:
            # Unknown command - print helpful message and exit with code 0
            print(f"Unknown command: '{cmd}'\n")
            print("Available commands:")
            for name in sorted(COMMAND_HANDLERS.keys()):
                print(f"  /{name}")
            print("\nTry /help for more information.")
            return 0

        # Run handler
        try:
            result = await handler(ctx, args)
            print(result)
            return 0
        except Exception as e:
            print(f"Error executing command: {e}", file=sys.stderr)
            return 1
    else:
        # Natural language message - use intent router
        try:
            result = await handle_natural_language(ctx, command)
            print(result)
            return 0
        except Exception as e:
            print(f"Error processing message: {e}", file=sys.stderr)
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
        await message.answer(result, reply_markup=get_main_keyboard())

    @dp.message(Command("help"))
    async def cmd_help(message: Message) -> None:
        """Handle /help command."""
        result = await handle_help(ctx)
        await message.answer(result, reply_markup=get_back_keyboard())

    @dp.message(Command("health"))
    async def cmd_health(message: Message) -> None:
        """Handle /health command."""
        result = await handle_health(ctx)
        await message.answer(result, reply_markup=get_back_keyboard())

    @dp.message(Command("labs"))
    async def cmd_labs(message: Message) -> None:
        """Handle /labs command."""
        result = await handle_labs(ctx)
        await message.answer(result, reply_markup=get_back_keyboard())

    @dp.message(Command("scores"))
    async def cmd_scores(message: Message) -> None:
        """Handle /scores command."""
        # Extract lab argument from command
        args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
        result = await handle_scores(ctx, args)
        await message.answer(result, reply_markup=get_back_keyboard())

    @dp.callback_query(lambda c: c.data == "labs")
    async def callback_labs(callback_query: types.CallbackQuery) -> None:
        """Handle Labs button click."""
        result = await handle_labs(ctx)
        await callback_query.message.answer(result, reply_markup=get_back_keyboard())
        await callback_query.answer()

    @dp.callback_query(lambda c: c.data == "help")
    async def callback_help(callback_query: types.CallbackQuery) -> None:
        """Handle Help button click."""
        result = await handle_help(ctx)
        await callback_query.message.answer(result, reply_markup=get_back_keyboard())
        await callback_query.answer()

    @dp.callback_query(lambda c: c.data == "health")
    async def callback_health(callback_query: types.CallbackQuery) -> None:
        """Handle Health button click."""
        result = await handle_health(ctx)
        await callback_query.message.answer(result, reply_markup=get_back_keyboard())
        await callback_query.answer()

    @dp.callback_query(lambda c: c.data.startswith("scores_"))
    async def callback_scores(callback_query: types.CallbackQuery) -> None:
        """Handle Scores button click."""
        lab = callback_query.data.replace("scores_", "")
        result = await handle_scores(ctx, lab)
        await callback_query.message.answer(result, reply_markup=get_back_keyboard())
        await callback_query.answer()

    @dp.callback_query(lambda c: c.data.startswith("top5_"))
    async def callback_top5(callback_query: types.CallbackQuery) -> None:
        """Handle Top 5 students button click."""
        lab = callback_query.data.replace("top5_", "")
        result = await handle_top_learners(ctx, f"{lab} 5")
        await callback_query.message.answer(result, reply_markup=get_back_keyboard())
        await callback_query.answer()

    @dp.callback_query(lambda c: c.data.startswith("groups_"))
    async def callback_groups(callback_query: types.CallbackQuery) -> None:
        """Handle Groups button click."""
        lab = callback_query.data.replace("groups_", "")
        result = await handle_groups(ctx, lab)
        await callback_query.message.answer(result, reply_markup=get_back_keyboard())
        await callback_query.answer()

    @dp.callback_query(lambda c: c.data == "back")
    async def callback_back(callback_query: types.CallbackQuery) -> None:
        """Handle Back button click."""
        result = await handle_start(ctx)
        await callback_query.message.answer(result, reply_markup=get_main_keyboard())
        await callback_query.answer()

    @dp.message()
    async def handle_message(message: Message) -> None:
        """Handle natural language messages via LLM intent routing.

        The LLM receives the user's message, a list of tools (backend endpoints),
        and a system prompt. It responds with tool calls. The bot executes them,
        feeds results back, and the LLM produces the final answer.
        """
        # Show typing indicator
        await message.action("typing")

        # Call natural language handler
        result = await handle_natural_language(ctx, message.text or "")
        await message.answer(result)

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
