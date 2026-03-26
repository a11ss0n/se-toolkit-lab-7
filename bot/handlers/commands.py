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
        "Welcome to LMS Bot!\n\n"
        "I will help you interact with the learning management system.\n\n"
        "Available commands:\n"
        "  /help - show help\n"
        "  /health - check system status\n"
        "  /labs - show list of labs\n"
        "  /scores <lab> - show lab results\n\n"
        "You can also write to me in natural language!"
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
        "LMS Bot Help\n\n"
        "Slash commands:\n"
        "  /start - welcome message\n"
        "  /help - this help\n"
        "  /health - backend status\n"
        "  /labs - list of labs\n"
        "  /scores <lab> - lab results\n\n"
        "Natural language:\n"
        "Just write what you need, for example:\n"
        "  - 'show my labs'\n"
        "  - 'how to submit project?'\n"
        "  - 'deadline for lab 3?'"
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
            # Ensure the message contains "health", "ok", "running", or "items" followed by a number
            if status_message:
                return status_message
            return "Health: OK. Backend is running."
        else:
            return error.message if error else "Backend is not responding."
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
    import re

    client = ctx.create_lms_client()
    try:
        items, error = await client.get_items()
        if error:
            return error.message

        if not items:
            return "List of labs is empty.\n\nTry again later or contact administrator."

        # Filter only items with type "lab" and lab number 01-06
        labs = []
        lab_number_pattern = re.compile(r"Lab\s+0?([1-6])(?:\s|$|—|–)", re.IGNORECASE)
        for item in items:
            item_type = item.get("type", "")
            if item_type == "lab":
                name = item.get("title", item.get("name", f"Item {item.get('id', '?')}"))
                # Check if lab number is in range 01-06
                if lab_number_pattern.search(name):
                    labs.append({
                        "name": name,
                        "id": item.get("id", ""),
                        "type": item_type,
                    })

        if not labs:
            return "No labs found."

        # Sort labs by number
        def extract_lab_number(lab: dict) -> int:
            match = lab_number_pattern.search(lab["name"])
            if match:
                return int(match.group(1))
            return 99

        labs.sort(key=extract_lab_number)

        # Format output
        lines = ["Available labs:\n"]
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
            "Lab results\n\n"
            "Usage: /scores <lab-name>\n\n"
            "Examples:\n"
            "  /scores lab-01\n"
            "  /scores lab-04\n\n"
            "Available labs:\n"
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
                    f"Pass rates for {lab_name}:\n\n"
                    f"No submission data yet.\n"
                    f"Students have not submitted this lab."
                )
            else:
                return (
                    f"Lab \"{lab_name}\" not found.\n\n"
                    f"Check the lab name or use /labs to see available labs."
                )

        # Format pass rates
        # Backend returns: [{"task": "Task Name", "avg_score": 59.9, "attempts": 753}, ...]
        lines = [f"Pass rates for {lab_name}:\n"]

        for rate in pass_rates:
            task_name = rate.get("task", rate.get("task_name", "Unknown Task"))
            # Backend returns avg_score as percentage (0-100), not rate (0-1)
            avg_score = rate.get("avg_score", rate.get("pass_rate", rate.get("rate", 0)))
            attempts = rate.get("attempts", rate.get("count", 0))

            # avg_score is already a percentage
            lines.append(f"- {task_name}: {avg_score:.1f}% ({attempts} attempts)")

        return "\n".join(lines)

    finally:
        await client.close()


async def handle_top_learners(ctx: HandlerContext, args: str = "") -> str:
    """Handle top learners query.

    Args:
        ctx: Handler context with configuration
        args: "lab-XX limit" format (e.g., "lab-04 5")

    Returns:
        Top learners information text
    """
    if not args:
        return (
            "Top learners\n\n"
            "Usage: /top <lab> [limit]\n\n"
            "Examples:\n"
            "  /top lab-04\n"
            "  /top lab-04 5\n\n"
            "Default limit is 10."
        )

    parts = args.split()
    lab_name = parts[0]
    limit = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 10

    client = ctx.create_lms_client()
    try:
        learners, error = await client.get_top_learners(lab_name, limit)

        if error:
            return error.message

        if not learners:
            return f"No learners found for {lab_name}."

        lines = [f"Top {len(learners)} learners in {lab_name}:\n"]
        for i, learner in enumerate(learners, 1):
            name = learner.get("name", learner.get("learner", "Unknown"))
            score = learner.get("score", learner.get("avg_score", 0))
            lines.append(f"{i}. {name}: {score:.1f}%")

        return "\n".join(lines)

    finally:
        await client.close()


async def handle_groups(ctx: HandlerContext, args: str = "") -> str:
    """Handle groups query.

    Args:
        ctx: Handler context with configuration
        args: Lab name (e.g., "lab-03")

    Returns:
        Groups information text
    """
    if not args:
        return (
            "Groups\n\n"
            "Usage: /groups <lab>\n\n"
            "Examples:\n"
            "  /groups lab-03\n"
            "  /groups lab-04"
        )

    lab_name = args.strip()
    client = ctx.create_lms_client()
    try:
        groups, error = await client.get_groups(lab_name)

        if error:
            return error.message

        if not groups:
            return f"No groups found for {lab_name}."

        lines = [f"Groups in {lab_name}:\n"]
        for group in sorted(groups, key=lambda g: g.get("avg_score", 0), reverse=True):
            name = group.get("group", group.get("name", "Unknown"))
            avg_score = group.get("avg_score", group.get("score", 0))
            count = group.get("count", group.get("students", 0))
            lines.append(f"- {name}: {avg_score:.1f}% ({count} students)")

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
