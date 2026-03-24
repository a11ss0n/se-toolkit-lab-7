"""Command handlers for Telegram bot.

These handlers are pure functions that take input and return text.
They do not know about Telegram - this makes them testable via CLI.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class HandlerContext:
    """Context passed to handlers."""

    lms_api_base_url: str
    lms_api_key: str
    llm_api_base_url: str
    llm_api_key: str
    llm_api_model: str


async def handle_start(ctx: HandlerContext, args: str = "") -> str:
    """Handle /start command.

    Args:
        ctx: Handler context with configuration
        args: Command arguments (unused for /start)

    Returns:
        Welcome message text
    """
    return (
        "👋 Добро пожаловать в LMS Bot!\n\n"
        "Я помогу вам взаимодействовать с системой управления обучением.\n\n"
        "📚 Доступные команды:\n"
        "  /help - показать справку\n"
        "  /health - проверить статус системы\n"
        "  /labs - показать список лабораторных работ\n\n"
        "Вы также можете писать мне обычным языком - я постараюсь понять ваш запрос!"
    )


async def handle_help(ctx: HandlerContext, args: str = "") -> str:
    """Handle /help command.

    Args:
        ctx: Handler context with configuration
        args: Command arguments (unused for /help)

    Returns:
        Help message text
    """
    return (
        "📖 Справка по боту\n\n"
        "🔹 Slash-команды:\n"
        "  /start - приветственное сообщение\n"
        "  /help - эта справка\n"
        "  /health - статус backend-системы\n"
        "  /labs - список лабораторных работ\n\n"
        "🔹 Естественный язык:\n"
        "Просто напишите, что вам нужно, например:\n"
        "  • 'покажи мои лабораторные'\n"
        "  • 'как сдать проект?'\n"
        "  • 'какой дедлайн по лабе 3?'\n\n"
        "Бот использует AI для понимания ваших запросов."
    )


async def handle_health(ctx: HandlerContext, args: str = "") -> str:
    """Handle /health command.

    Args:
        ctx: Handler context with configuration
        args: Command arguments (unused for /health)

    Returns:
        Health status text
    """
    # TODO: Implement actual health check via LMS API
    # For now, return stub response
    return (
        "✅ Статус системы:\n\n"
        f"🔹 LMS Backend: {ctx.lms_api_base_url}\n"
        "   Статус: OK (заглушка)\n\n"
        f"🔹 LLM API: {ctx.llm_api_base_url or 'не настроен'}\n"
        "   Статус: OK (заглушка)\n\n"
        "Все системы работают нормально."
    )


async def handle_labs(ctx: HandlerContext, args: str = "") -> str:
    """Handle /labs command.

    Args:
        ctx: Handler context with configuration
        args: Command arguments (unused for /labs)

    Returns:
        List of labs text
    """
    # TODO: Implement actual labs fetch via LMS API
    # For now, return stub response
    return (
        "📚 Список лабораторных работ:\n\n"
        "🔹 Lab 1 - Введение в разработку\n"
        "   Статус: доступна\n\n"
        "🔹 Lab 2 - Основы тестирования\n"
        "   Статус: доступна\n\n"
        "🔹 Lab 3 - Работа с API\n"
        "   Статус: доступна\n\n"
        "🔹 Lab 4 - Контейнеризация\n"
        "   Статус: доступна\n\n"
        "🔹 Lab 5 - AI-агенты\n"
        "   Статус: доступна\n\n"
        "🔹 Lab 6 - Деплой\n"
        "   Статус: доступна\n\n"
        "🔹 Lab 7 - Telegram-бот\n"
        "   Статус: в разработке\n\n"
        "Выберите лабораторную для получения деталей."
    )


# Map command names to handler functions
COMMAND_HANDLERS = {
    "start": handle_start,
    "help": handle_help,
    "health": handle_health,
    "labs": handle_labs,
}
