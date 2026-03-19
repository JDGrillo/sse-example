"""
Application settings and configuration management.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Azure OpenAI via APIM Configuration
    azure_openai_endpoint: str
    azure_openai_deployment_name: str = "gpt-4o"
    azure_openai_api_version: str = "2025-03-01-preview"
    azure_openai_api_key: str

    # Application Settings
    environment: str = "development"
    log_level: str = "INFO"
    max_text_length: int = 5000
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()
