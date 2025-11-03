from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Jira configuration
    jira_base_url: str
    jira_username: str
    jira_password: str  # API token for Jira Cloud or password for Jira Server
    jira_auth_type: str = "basic"  # basic or token

    # Proxy server configuration
    proxy_host: str = "0.0.0.0"
    proxy_port: int = 8000
    debug: bool = False

    # Application configuration
    app_title: str = "Jira API Proxy"
    app_description: str = "Proxy server for Jira API with JetBrains IDE compatibility"
    app_version: str = "1.0.0"

    # Security
    allow_origins: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()