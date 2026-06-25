from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    app_name: str = "星尘 Stardust AI"
    debug: bool = True
    
    # DeepSeek API
    deepseek_api_key: str = ""
    deepseek_api_url: str = "https://api.deepseek.com/v1/chat/completions"
    
    # 数据库
    database_url: str = "sqlite:///data/stardust.db"
    
    # 上下文配置
    max_context_messages: int = 10  # 最大上下文消息数

    # JWT 配置
    jwt_secret_key: str = "stardust-jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 7

    # 邮件配置（Resend）
    resend_api_key: str = ""
    resend_from: str = "星尘 AI <noreply@myxingchen.xyz>"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()