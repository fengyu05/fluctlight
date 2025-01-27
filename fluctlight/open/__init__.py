import openai
from langsmith.wrappers import wrap_openai
from fluctlight.settings import TEST_MODE
from fluctlight.settings import OPENAI_API_KEY, DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL


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
DEEPSEEK_CLIENT = make_openai_client(
    base_url=DEEPSEEK_BASE_URL,
    api_key=DEEPSEEK_API_KEY,
    use_langsmith_wrapper=(not TEST_MODE),
)
