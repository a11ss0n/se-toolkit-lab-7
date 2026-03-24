"""Scores handler for /scores command."""

from bot.handlers.commands import HandlerContext


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
            "  lab-01, lab-02, lab-03, lab-04, lab-05, lab-06, lab-07"
        )

    # TODO: Fetch actual scores from LMS API
    # For now, return stub response
    lab_name = args.strip().upper()
    return (
        f"📊 Результаты: {lab_name}\n\n"
        f"🔹 Статус: доступна\n"
        f"🔹 Прогресс: 0/5 задач выполнено\n\n"
        "Задачи:\n"
        "  □ Task 1 - Не выполнено\n"
        "  □ Task 2 - Не выполнено\n"
        "  □ Task 3 - Не выполнено\n"
        "  □ Task 4 - Не выполнено\n"
        "  □ Task 5 - Не выполнено\n\n"
        "Выполните задачи лабораторной работы, чтобы увидеть прогресс."
    )
