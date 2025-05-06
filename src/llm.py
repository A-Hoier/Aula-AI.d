from openai import AsyncAzureOpenAI, AzureOpenAI

from config import app_settings


def get_openai_client() -> AzureOpenAI:
    """Callable function that allows the llm client to be instatiated from other scripts."""
    return AzureOpenAI(
        api_version=app_settings().API_VERSION,
        api_key=app_settings().AZURE_OPENAI_API_KEY.get_secret_value(),
        azure_endpoint=app_settings().AZURE_OPENAI_ENDPOINT,
    )


def get_async_openai_client() -> AsyncAzureOpenAI:
    """Callable function that allows the llm client to be instatiated from other scripts."""
    return AsyncAzureOpenAI(
        api_version=app_settings().API_VERSION,
        api_key=app_settings().AZURE_OPENAI_API_KEY.get_secret_value(),
        azure_endpoint=app_settings().AZURE_OPENAI_ENDPOINT,
    )
