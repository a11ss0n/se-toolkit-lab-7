"""Bot configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    """Telegram bot settings."""

    model_config = SettingsConfigDict(
        env_file=".env.bot.secret",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram
    bot_token: str = ""

    # LMS API
    lms_api_base_url: str = "http://localhost:8000"
    lms_api_key: str = ""

    # LLM API
    llm_api_model: str = "coder-model"
    llm_api_key: str = ""
    llm_api_base_url: str = ""

    @property
    def is_test_mode(self) -> bool:
        """Check if bot is running in test mode (no real token)."""
        return not self.bot_token or self.bot_token == "<bot-token>"


settings = BotSettings()
