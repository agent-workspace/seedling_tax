from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://localhost/seedling_tax"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    CLAUDE_API_KEY: str = ""
    CLAUDE_FAST_MODEL: str = "claude-haiku-4-5-20251001"
    CLAUDE_SMART_MODEL: str = "claude-sonnet-4-6"
    RESEND_API_KEY: str = ""
    FILE_STORAGE_PATH: str = "/opt/seedling-tax-data/files"
    FRANKFURTER_API_URL: str = "https://api.frankfurter.dev/v2/rates"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
