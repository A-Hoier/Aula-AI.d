from functools import lru_cache

from inspari.config import load_dotenv
from pydantic import SecretStr
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    # Azure OpenAI
    AZURE_OPENAI_API_KEY: SecretStr
    AZURE_OPENAI_ENDPOINT: str
    API_VERSION: str
    AZURE_OPENAI_MODEL: str

    ANTHROPIC_API_KEY: SecretStr

    GOOGLE_SEARCH_API_KEY: SecretStr
    GOOGLE_SEARCH_cx: SecretStr

    AULA_USER: str
    AULA_PWD: SecretStr


@lru_cache()
def app_settings() -> AppSettings:
    load_dotenv(dotenv_path=".env")
    return AppSettings()  # ignore
