"""Handlers package."""

from bot.handlers.commands import (
    COMMAND_HANDLERS,
    handle_help,
    handle_health,
    handle_labs,
    handle_scores,
    handle_start,
)

__all__ = [
    "handle_start",
    "handle_help",
    "handle_health",
    "handle_labs",
    "handle_scores",
    "COMMAND_HANDLERS",
]
