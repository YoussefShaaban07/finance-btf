from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    plaid_client_id: str = ""
    plaid_secret: str = ""
    plaid_env: str = "sandbox"

    finnhub_api_key: str = ""

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5-5"

    token_encryption_key: str = ""
    database_url: str = "sqlite:///./finance.db"

    @property
    def demo_mode(self) -> bool:
        """No Plaid keys -> serve fake-but-realistic data so the app works out of the box."""
        return not (self.plaid_client_id and self.plaid_secret)


@lru_cache
def get_settings() -> Settings:
    return Settings()
