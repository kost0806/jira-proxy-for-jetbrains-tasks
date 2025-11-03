from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Jira configuration - only base URL needed for proxy
    jira_base_url: str = "https://your-jira-instance.atlassian.net"  # Default fallback

    # Proxy server configuration
    proxy_host: str = "0.0.0.0"
    proxy_port: int = 8000
    debug: bool = False

    # Application configuration
    app_title: str = "Jira API Proxy"
    app_description: str = "Proxy server for Jira API with JetBrains IDE compatibility - supports per-request authentication"
    app_version: str = "1.0.0"

    # Security
    allow_origins: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()