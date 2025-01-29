import openai
from langsmith.wrappers import wrap_openai


def make_openai_client(
    api_key: str, base_url: str | None = None, use_langsmith_wrapper: bool = False
) -> openai.OpenAI:
    client = openai.OpenAI(base_url=base_url, api_key=api_key)

    if use_langsmith_wrapper:
        client = wrap_openai(client)

    return client
