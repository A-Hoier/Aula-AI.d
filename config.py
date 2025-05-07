from functools import lru_cache

from inspari.config import load_dotenv
from pydantic import SecretStr
from pydantic_settings import BaseSettings

AVAILABLE_MODELS: list[str] = [
    "gpt-4o",
    "o4-mini",
    "anthropic:claude-3-5-sonnet-latest",
    "anthropic:claude-3-7-sonnet-latest",
    "anthropic:claude-3-5-haiku-latest",
]


AVAILABLE_AGENTS: list[str] = ["research_agent", "aula_agent"]


class AppSettings(BaseSettings):
    # Azure OpenAI
    AZURE_OPENAI_API_KEY: SecretStr | None = None
    AZURE_OPENAI_ENDPOINT: str | None = None
    API_VERSION: str

    ANTHROPIC_API_KEY: SecretStr | None = None

    GOOGLE_SEARCH_API_KEY: SecretStr | None = None
    GOOGLE_SEARCH_cx: SecretStr | None = None

    AULA_USER: str | None = None
    AULA_PWD: SecretStr | None = None

    BACKEND_URL: str


@lru_cache()
def app_settings() -> AppSettings:
    load_dotenv(dotenv_path=".env")
    return AppSettings()  # ignore
