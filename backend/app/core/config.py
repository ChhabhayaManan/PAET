import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Load .env from backend/ directory (one level up from app/)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

class Settings(BaseSettings):
    # Secrets carry repr=False so a failing test or a log line never prints them.
    # Database
    DATABASE_URL: str = Field(repr=False)

    # JWT
    SECRET_KEY: str = Field(repr=False)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # App
    APP_NAME: str = "aiTA - AI Teaching Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    # Startup loads the book-search embedder in the background so the first chat
    # question does not wait for it. Tests and quick local runs can skip it.
    SKIP_EMBED_WARMUP: bool = False
    # Startup runs a loop that retries pending onboarding theory grades every 2 minutes.
    SKIP_ONBOARDING_SWEEP: bool = False
    # Cosine similarity a book passage needs before it is retrieved automatically for a
    # chat message. Live bge-small scores: on-topic passages ~0.72-0.80, loosely related
    # ones (hint requests, code reviews) just below.
    RAG_MIN_SCORE: float = 0.68
    # Set to an existing user's email to enable POST /auth/dev-login, which skips
    # the password and the OTP. Ignored unless DEBUG is also true.
    DEV_LOGIN_EMAIL: str = ""
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # ── LLM (NVIDIA NIM) ──────────────────────────────────────────────────
    NVIDIA_API_KEY: str = Field(default="", repr=False)
    # One provider. Most of the catalogue is already end of life and available_models
    # still lists the dead ones, so ping before switching any model below.
    # 3-super went 404 for this account on 2026-10-26. Ultra strips the line breaks
    # out of code inside structured output, so it handles prose only.
    NVIDIA_MODEL: str = "nvidia/nemotron-3-ultra-550b-a55b"
    # Code: keeps real newlines in structured output (checked 2026-10-26).
    NVIDIA_CODEGEN_MODEL: str = "nvidia/nemotron-3.5-lightning-30b-a3b"
    LLM_MAX_OUTPUT_TOKENS: int = 8192
    LLM_MAX_ATTEMPTS: int = 3
    NVIDIA_API_KEY_2: str = Field(default="", repr=False)
    # gpt-oss-20b stopped answering on 2026-10-26. Lightning passes tool calls and
    # real newlines in structured code, and runs on a separate NVIDIA function.
    NVIDIA_FALLBACK_MODEL: str = "nvidia/nemotron-3.5-lightning-30b-a3b"
    NVIDIA_RPM: int = 35
    LLM_QUEUE_DEADLINE_S: float = 20

    # ── Model selector ────────────────────────────────────────────────────
    # web: 30-day key cookie, cloud providers only. local: 1-year cookie, local models too.
    DEPLOY_MODE: str = "web"
    LLM_COOKIE_SECRET: str = Field(default="", repr=False)
    DEFAULT_LLM_PROVIDER: str = ""
    DEFAULT_LLM_MODEL: str = ""
    DEFAULT_LLM_API_KEY: str = Field(default="", repr=False)
    DEFAULT_LLM_BASE_URL: str = ""
    REDIS_URL: str = Field(default="", repr=False)

    # ── Code execution ────────────────────────────────────────────────────
    EXECUTION_PROVIDER: str = "sidecar"
    EXECUTOR_URL: str = "http://executor:8080"
    EXEC_WALL_SECONDS: float = 2.0
    EXEC_CPU_SECONDS: int = 2
    EXEC_MEMORY_MB: int = 256
    EXEC_MAX_PROCESSES: int = 64
    EXEC_OUTPUT_KB: int = 64
    EXEC_COMPILE_SECONDS: int = 10

    # ── Evaluation pipeline ───────────────────────────────────────────────
    TEST_CASES_MIN: int = 3
    TEST_CASES_TARGET: int = 8
    REFERENCE_MAX_ATTEMPTS: int = 3

    # ── Content (question banks, lessons, guides) ─────────────────────────
    CONTENT_DIR: Path = Path(__file__).resolve().parents[2] / "content"

    # ── Gamification ──────────────────────────────────────────────────────
    # off: nothing computed · silent: computed, shown only behind the Dashboard
    # reveal (the study setting) · live: also toasted on each graded answer.
    GAMIFICATION_MODE: str = "live"

    # ── Email (SMTP) for OTP delivery ─────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = Field(default="", repr=False)
    SMTP_FROM_NAME: str = "aiTA"
    
    # ── Gmail API (OAuth2 - works on Render via HTTPS) ────────────────────
    GMAIL_CLIENT_ID: str = ""
    GMAIL_CLIENT_SECRET: str = Field(default="", repr=False)
    GMAIL_REFRESH_TOKEN: str = Field(default="", repr=False)
    GMAIL_FROM_EMAIL: str = ""
    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
        extra = "ignore"
    

settings = Settings()