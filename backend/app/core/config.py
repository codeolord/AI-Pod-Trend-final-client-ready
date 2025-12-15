from __future__ import annotations

from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _split_csv(value: str) -> List[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


class Settings(BaseSettings):
    """Runtime configuration.

    Keep secrets out of source control. Configure via environment variables.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_v1_prefix: str = "/api/v1"
    project_name: str = "POD Trend & Design Automation API"

    env: str = "development"  # development | staging | production

    # Database
    postgres_user: str = "pod_user"
    postgres_password: str = "pod_password"
    postgres_db: str = "pod_db"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    database_url: Optional[str] = None  # If set, overrides the composed postgres URL

    # Redis / Celery
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None

    # OpenAI
    openai_api_key: Optional[str] = None
    # Auth / Security
    jwt_secret: str = Field(default="change-me-in-production", validation_alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    access_token_exp_minutes: int = 60
    refresh_token_exp_days: int = 30

    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-5-mini"
    openai_reasoning: str = "low"  # low|medium|high (for reasoning models)
    openai_timeout_s: int = 60

    # Trend ingestion
    trend_rss_urls_csv: str = (
        "https://news.google.com/rss/search?q=print+on+demand+t+shirt+trend&hl=en-US&gl=US&ceid=US:en,"
        "https://news.google.com/rss/search?q=Etsy+shirt+trend&hl=en-US&gl=US&ceid=US:en,"
        "https://www.reddit.com/r/printondemand/.rss,"
        "https://www.reddit.com/r/EtsySellers/.rss"
    )

    @property
    def trend_rss_urls(self) -> List[str]:
        return _split_csv(self.trend_rss_urls_csv)

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def resolved_celery_broker_url(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def resolved_celery_result_backend(self) -> str:
        return self.celery_result_backend or self.redis_url


settings = Settings()
