"""Natural language intent router handler.

Uses LLM to understand user messages and route to appropriate tools.
All routing decisions are made by the LLM - no regex or keyword matching.
"""

from bot.handlers.commands import HandlerContext
from bot.services.llm_client import LLMClient
from bot.services.lms_api import LMSAPIClient


async def handle_natural_language(ctx: HandlerContext, message: str) -> str:
    """Handle natural language message via LLM intent routing.

    Args:
        ctx: Handler context with configuration
        message: User's message text

    Returns:
        Response text
    """
    # Check if LLM is configured
    if not ctx.llm_api_base_url or not ctx.llm_api_key:
        return (
            "I'm still learning to understand natural language. 🤔\n\n"
            "Try using commands:\n"
            "/start, /help, /health, /labs, /scores <lab>\n\n"
            "For example:\n"
            "  /labs — show list of labs\n"
            "  /scores lab-01 — show results for lab-01"
        )

    # Create clients
    lms_client = ctx.create_lms_client()
    llm_client = LLMClient(
        base_url=ctx.llm_api_base_url,
        api_key=ctx.llm_api_key,
        model=ctx.llm_api_model,
    )

    try:
        # Use LLM for intent routing - all decisions made by LLM
        response = await llm_client.chat_with_tools(
            user_message=message,
            lms_client=lms_client,
            max_iterations=3,
        )

        return response

    except Exception as e:
        # Fallback on error
        return (
            f"Sorry, an error occurred: {type(e).__name__}\n\n"
            "Try using commands:\n"
            "/start, /help, /health, /labs, /scores <lab>"
        )

    finally:
        await lms_client.close()
        await llm_client.close()
