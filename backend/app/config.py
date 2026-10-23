from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    plaid_client_id: str = ""
    plaid_secret: str = ""
    plaid_env: str = "sandbox"

    finnhub_api_key: str = ""

    # AI assistant: set EITHER key. Gemini has a free tier (aistudio.google.com).
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5-5"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"

    token_encryption_key: str = ""
    database_url: str = "sqlite:///./finance.db"

    @property
    def demo_mode(self) -> bool:
        """No Plaid keys -> serve fake-but-realistic data so the app works out of the box."""
        return not (self.plaid_client_id and self.plaid_secret)

    @property
    def ai_provider(self) -> str | None:
        if self.anthropic_api_key:
            return "anthropic"
        if self.gemini_api_key:
            return "gemini"
        return None


@lru_cache
def get_settings() -> Settings:
    return Settings()
