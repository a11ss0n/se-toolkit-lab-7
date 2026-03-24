"""Handlers package."""

from bot.handlers.commands import (
    handle_help,
    handle_health,
    handle_labs,
    handle_start,
)
from bot.handlers.scores import handle_scores

__all__ = [
    "handle_start",
    "handle_help",
    "handle_health",
    "handle_labs",
    "handle_scores",
]
