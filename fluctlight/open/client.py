import openai
from langsmith.wrappers import wrap_openai
import os
from pydantic import BaseModel
from fluctlight.settings import TEST_MODE, OPENAI_API_KEY

_OPENAI_PROVIDER = "openai"


def make_openai_client(
    api_key: str, base_url: str | None = None, use_langsmith_wrapper: bool = False
) -> openai.OpenAI:
    client = openai.OpenAI(base_url=base_url, api_key=api_key)

    if use_langsmith_wrapper:
        client = wrap_openai(client)

    return client


OPENAI_CLIENT = make_openai_client(
    api_key=OPENAI_API_KEY, use_langsmith_wrapper=(not TEST_MODE)
)


class Alternative(BaseModel):
    base_url: str
    api_key: str


def get_alternative_platforms() -> dict[str, Alternative]:
    alternatives = {}
    alternates = os.getenv("OPENAI_ALTERNATES", "").split(",")

    for alt in alternates:
        alt = alt.strip().lower()
        api_key = os.getenv(f"{alt.upper()}_API_KEY")
        base_url = os.getenv(f"{alt.upper()}_BASE_URL")
        if api_key and base_url:
            alternatives[alt] = Alternative(api_key=api_key, base_url=base_url)

    return alternatives


_ALT_PLATFORMS = get_alternative_platforms()
_CLIENT_CACHE = {}


def get_open_client(provider: str, disable_cache: bool = False) -> openai.OpenAI:
    provider = provider.strip().lower()
    if provider == _OPENAI_PROVIDER:
        return OPENAI_CLIENT

    if provider not in _ALT_PLATFORMS:
        raise ValueError(f"Unknown platform: {provider}")

    if provider not in _CLIENT_CACHE or disable_cache:
        alternative = _ALT_PLATFORMS[provider]
        _CLIENT_CACHE[provider] = make_openai_client(
            api_key=alternative.api_key,
            base_url=alternative.base_url,
            use_langsmith_wrapper=(not TEST_MODE),
        )
    return _CLIENT_CACHE[provider]
