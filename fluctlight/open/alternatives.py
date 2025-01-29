import openai
import os
from pydantic import BaseModel
from fluctlight.open.client import make_openai_client
from fluctlight.settings import TEST_MODE


class Alternative(BaseModel):
    base_url: str
    api_key: str


def get_alternative_platforms() -> dict[str, Alternative]:
    alternatives = {}
    alternates = os.getenv("OPENAI_ALTERNATES", "").split(",")

    for alt in alternates:
        alt = alt.strip().upper()
        api_key = os.getenv(f"{alt}_API_KEY")
        base_url = os.getenv(f"{alt}_BASE_URL")
        if api_key and base_url:
            alternatives[alt] = Alternative(api_key=api_key, base_url=base_url)

    return alternatives


_ALT_PLATFORMS = get_alternative_platforms()
_CLIENT_CACHE = {}


def get_alt_client(alt: str) -> openai.OpenAI:
    alt = alt.strip().upper()
    if alt not in _ALT_PLATFORMS:
        raise ValueError(f"Unknown alternative platform: {alt}")

    if alt not in _CLIENT_CACHE:
        alternative = _ALT_PLATFORMS[alt]
        _CLIENT_CACHE[alt] = make_openai_client(
            api_key=alternative.api_key,
            base_url=alternative.base_url,
            use_langsmith_wrapper=(not TEST_MODE),
        )

    return _CLIENT_CACHE[alt]


def get_alt_client_from_model_key(model_key: str) -> openai.OpenAI:
    return get_alt_client(model_key.split(":")[0])
