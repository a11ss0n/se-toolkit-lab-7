"""Handlers package."""

from bot.handlers.commands import (
    COMMAND_HANDLERS,
    handle_groups,
    handle_help,
    handle_health,
    handle_labs,
    handle_scores,
    handle_start,
    handle_top_learners,
)
from bot.handlers.natural_language import handle_natural_language

__all__ = [
    "handle_start",
    "handle_help",
    "handle_health",
    "handle_labs",
    "handle_scores",
    "handle_top_learners",
    "handle_groups",
    "handle_natural_language",
    "COMMAND_HANDLERS",
]
