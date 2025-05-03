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

    # Perplexity
    PERPLEXITY_API_KEY: SecretStr
    PERPLEXITY_ENDPOINT: str
    PERPLEXITY_MODEL: str

    # Storage Account
    STORAGE_ACCOUNT_CONNECTION_STRING: SecretStr

    # Prompts
    PROMPTS: dict = {}

    GOOGLE_SEARCH_API_KEY: SecretStr
    GOOGLE_SEARCH_cx: SecretStr

    def update_prompts(self, prompts: dict):
        self.PROMPTS = prompts


@lru_cache()
def app_settings() -> AppSettings:
    load_dotenv(dotenv_path=".env")
    return AppSettings()  # ignore
