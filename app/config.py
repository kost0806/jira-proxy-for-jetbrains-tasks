from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Jira configuration
    jira_base_url: str = "https://your-jira-instance.atlassian.net"  # Default fallback

    # Service account credentials for API authentication
    jira_service_username: str = ""
    jira_service_api_token: str = ""

    # Proxy server configuration
    proxy_host: str = "0.0.0.0"
    proxy_port: int = 8000
    debug: bool = False

    # Application configuration
    app_title: str = "Jira API Proxy"
    app_description: str = "Proxy server for Jira API with JetBrains IDE compatibility - supports dual authentication with user impersonation"
    app_version: str = "1.0.0"

    # Security
    allow_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()