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

    # 模型路由（基础设施层）：mock=规则兜底；openai=OpenAI 兼容接口
    llm_provider: str = "mock"  # mock | openai
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    # 工具调用 Agent
    tool_sandbox_dir: str = "/tmp/jobclaw-tools"
    search_api_url: str = ""  # 留空则 search_web 返回未配置

    # IM 网关入站验签（留空=开发模式跳过验签）
    im_wechat_token: str = ""
    im_feishu_encrypt_key: str = ""
    im_dingtalk_secret: str = ""

    # 消息推送（IM 机器人 webhook，留空=跳过推送）
    feishu_webhook_url: str = ""
    feishu_webhook_secret: str = ""
    wecom_webhook_key: str = ""
    dingtalk_webhook_url: str = ""
    dingtalk_webhook_secret: str = ""

    @property
    def is_prod(self) -> bool:
        return self.app_env == "prod"


@lru_cache
def get_settings() -> Settings:
    return Settings()
