from fluctlight.settings import TEST_MODE, OPENAI_API_KEY
from fluctlight.open.client import make_openai_client


OPENAI_CLIENT = make_openai_client(
    api_key=OPENAI_API_KEY, use_langsmith_wrapper=(not TEST_MODE)
)
