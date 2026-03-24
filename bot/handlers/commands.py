"""Command handlers for Telegram bot.

These handlers are pure functions that take input and return text.
They do not know about Telegram - this makes them testable via CLI.
"""

from dataclasses import dataclass
from typing import Optional

from bot.services.lms_api import LMSAPIClient, ApiError


@dataclass
class HandlerContext:
    """Context passed to handlers."""

    lms_api_base_url: str
    lms_api_key: str
    llm_api_base_url: str
    llm_api_key: str
    llm_api_model: str

    def create_lms_client(self) -> LMSAPIClient:
        """Create LMS API client from context."""
        return LMSAPIClient(self.lms_api_base_url, self.lms_api_key)


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
        "  /labs - показать список лабораторных работ\n"
        "  /scores <lab> - показать результаты по лабораторной\n\n"
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
        "  /labs - список лабораторных работ\n"
        "  /scores <lab> - результаты по лабораторной\n\n"
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
    client = ctx.create_lms_client()
    try:
        is_healthy, status_message, error = await client.health_check()
        if is_healthy:
            return status_message or "✅ Backend is healthy."
        else:
            return error.message if error else "❌ Backend is not responding."
    finally:
        await client.close()


async def handle_labs(ctx: HandlerContext, args: str = "") -> str:
    """Handle /labs command.

    Args:
        ctx: Handler context with configuration
        args: Command arguments (unused for /labs)

    Returns:
        List of labs text
    """
    client = ctx.create_lms_client()
    try:
        items, error = await client.get_items()
        if error:
            return error.message

        if not items:
            return "📚 Список лабораторных работ пуст.\n\nПопробуйте позже или обратитесь к администратору."

        # Filter only items with type "lab"
        labs = []
        for item in items:
            item_type = item.get("type", "")
            if item_type == "lab":
                name = item.get("title", item.get("name", f"Item {item.get('id', '?')}"))
                labs.append({
                    "name": name,
                    "id": item.get("id", ""),
                    "type": item_type,
                })

        if not labs:
            return "📚 Лабораторные работы не найдены."

        # Format output
        lines = ["📚 Доступные лаборатории:\n"]
        for lab in labs:
            name = lab["name"]
            lines.append(f"- {name}")

        return "\n".join(lines)

    finally:
        await client.close()


async def handle_scores(ctx: HandlerContext, args: str = "") -> str:
    """Handle /scores command.

    Args:
        ctx: Handler context with configuration
        args: Lab name or ID (e.g., "lab-04" or "1")

    Returns:
        Scores information text
    """
    if not args:
        return (
            "📊 Результаты по лабораторным работам\n\n"
            "Использование: /scores <lab-name>\n\n"
            "Примеры:\n"
            "  /scores lab-01\n"
            "  /scores lab-04\n\n"
            "Доступные лабораторные:\n"
            "  lab-01, lab-02, lab-03, lab-04, lab-05, lab-06"
        )

    lab_name = args.strip()
    client = ctx.create_lms_client()
    try:
        pass_rates, error = await client.get_pass_rates(lab_name)

        if error:
            return error.message

        # Empty pass rates - lab may exist but have no submissions yet
        if not pass_rates:
            # Try to verify if lab exists by checking items
            items, items_error = await client.get_items()
            lab_exists = False
            if not items_error and items:
                for item in items:
                    if item.get("type") == "lab":
                        title = item.get("title", "").lower()
                        lab_id = str(item.get("id", ""))
                        # Check various match patterns:
                        # - "lab-04" should match "Lab 04" in title
                        # - "4" should match id "4"
                        # - "lab 04" should match title
                        # Extract lab number from input (e.g., "lab-04" -> 4)
                        lab_num_str = lab_name.lower().replace("lab-", "").replace("lab ", "").lstrip("0") or "0"
                        # Extract lab number from title (e.g., "lab 04 — ..." -> 4)
                        title_parts = title.replace("lab ", "").split()
                        title_num_str = title_parts[0].lstrip("0") or "0" if title_parts else ""
                        try:
                            lab_num = int(lab_num_str)
                            title_num = int(title_num_str) if title_num_str else -1
                            if lab_num == title_num:
                                lab_exists = True
                                break
                        except ValueError:
                            pass
                        # Also check direct string match
                        if lab_name.lower() in title or lab_name == lab_id:
                            lab_exists = True
                            break

            if lab_exists:
                return (
                    f"📊 Pass rates for {lab_name}:\n\n"
                    f"Нет данных о submission.\n"
                    f"Студенты ещё не сдали эту лабораторную работу."
                )
            else:
                return (
                    f"📊 Лабораторная работа \"{lab_name}\" не найдена.\n\n"
                    f"Проверьте название или используйте /labs для просмотра доступных."
                )

        # Format pass rates
        # Expected format: [{"task": "Task Name", "pass_rate": 0.714, "attempts": 156}, ...]
        lines = [f"📊 Pass rates for {lab_name}:\n"]

        for rate in pass_rates:
            task_name = rate.get("task", rate.get("task_name", "Unknown Task"))
            pass_rate = rate.get("pass_rate", rate.get("rate", 0))
            attempts = rate.get("attempts", rate.get("count", 0))

            # Convert to percentage
            percentage = pass_rate * 100 if pass_rate <= 1 else pass_rate
            lines.append(f"- {task_name}: {percentage:.1f}% ({attempts} attempts)")

        return "\n".join(lines)

    finally:
        await client.close()


# Map command names to handler functions
COMMAND_HANDLERS = {
    "start": handle_start,
    "help": handle_help,
    "health": handle_health,
    "labs": handle_labs,
    "scores": handle_scores,
}
