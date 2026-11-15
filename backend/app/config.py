from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    gemini_api_key: str
    jwt_secret: str
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    database_url: str = "sqlite+aiosqlite:///./chat_pdf.db"
    chroma_path: str = "./chroma_data"
    frontend_origin: str = "http://localhost:5173"
    cookie_secure: bool = False
    smtp_host: str = "smtp.mailtrap.io"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@chatpdf.local"
    admin_email: str = ""
    admin_password: str = ""
    max_file_mb: int = 20
    max_pages: int = 200

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
