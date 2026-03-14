from functools import lru_cache
from openai import AsyncOpenAI
from backend.config import settings


@lru_cache(maxsize=1)
def get_openai_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=settings.openai_api_key)
