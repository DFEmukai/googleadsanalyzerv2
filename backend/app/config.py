from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/googleads_analyzer"

    # Google Ads API
    google_ads_developer_token: str = ""
    google_ads_client_id: str = ""
    google_ads_client_secret: str = ""
    google_ads_refresh_token: str = ""
    google_ads_customer_id: str = ""
    google_ads_login_customer_id: str = ""

    # Claude API
    anthropic_api_key: str = ""

    # Chatwork API
    chatwork_api_token: str = ""
    chatwork_room_id: str = ""
    chatwork_assignee_id: str = ""
    chatwork_mention_id: str = ""

    # Dashboard URL (for Chatwork messages)
    dashboard_url: str = "http://localhost:3000"

    # Safeguard settings
    max_changes_per_approval: int = 10
    max_budget_change_pct: float = 20.0
    rollback_window_hours: int = 24

    # CORS
    frontend_url: str = "http://localhost:3000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
