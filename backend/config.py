import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
DEFAULT_DATABASE_PATH = (BACKEND_DIR / "social.db").resolve()


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_csv(name: str, default: str = "") -> list[str]:
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


load_dotenv(PROJECT_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "").strip() or f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}"
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key")
JWT_PREVIOUS_SECRETS = env_csv("JWT_PREVIOUS_SECRETS")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", str(7 * 24 * 60)))
CARD_PEPPER = os.getenv("CARD_PEPPER", "dev-card-pepper")
CARD_PREVIOUS_PEPPERS = env_csv("CARD_PREVIOUS_PEPPERS")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.qq.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
UPLOAD_DIR = str((PROJECT_DIR / "data" / "storage").resolve())
ENABLE_DEV_PAYMENT = env_flag("ENABLE_DEV_PAYMENT", False)
ACCESS_TOKEN_COOKIE_NAMES = tuple(env_csv("ACCESS_TOKEN_COOKIE_NAMES", "admin_token,user_token"))
ALLOWED_CORS_ORIGINS = env_csv(
    "ALLOWED_CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,"
    "http://localhost:4173,http://127.0.0.1:4173,http://localhost:4174,http://127.0.0.1:4174",
)
