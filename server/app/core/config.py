from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_env: str = "dev"  # dev | test | prod
    database_url: str = (
        "mysql+aiomysql://root:jobclaw@127.0.0.1:3306/jobclaw?charset=utf8mb4"
    )
    redis_url: str = "redis://127.0.0.1:6379/0"
    jwt_secret: str = "dev-secret-change-me-0123456789abcdef"
    jwt_access_ttl_minutes: int = 15
    enable_dev_login: bool = True
    seed_admin: bool = True
    log_json: bool = False

    @property
    def is_prod(self) -> bool:
        return self.app_env == "prod"


@lru_cache
def get_settings() -> Settings:
    return Settings()
