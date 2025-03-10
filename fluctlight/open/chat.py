from typing import Any, Type
from langsmith import traceable
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat import ParsedChatCompletion
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from fluctlight.settings import GPT_STRUCTURE_OUTPUT_MODEL, GPT_CHAT_MODEL
from fluctlight.open.client import get_open_client


def get_provider_and_model_id(model_key: str) -> tuple[str, str]:
    """
    Get the provider and model_id from the model_key.
    Examples:
    - 'openai:gpt-3' -> ('openai', 'gpt-3')
    """
    provider, model_id = (
        model_key.split(":", 1) if ":" in model_key else ("openai", model_key)
    )
    provider = provider.lower()
    return provider, model_id


def get_message_from_completion(completion: ChatCompletion, idx: int = 0) -> str:
    return completion.choices[idx].message.content


def get_parsed_choice_from_completion(completion: ChatCompletion, idx: int = 0) -> Any:
    return completion.choices[idx].message.parsed


@traceable(run_type="llm")
def chat_complete(
    messages: list[ChatCompletionMessageParam],
    model_key: str = GPT_CHAT_MODEL,
) -> ChatCompletion:
    """
    Generate a chat completion based on the provided messages.

    Args:
        messages (list[ChatCompletionMessageParam]): The list of messages to be used for the chat completion.
        model_key (str): The model key in the format 'provider:model_id'. Defaults to 'openai:gpt-3'.
                         If the provider is not specified, it defaults to OpenAI.

    Returns:
        ChatCompletion: The chat completion result.

    The model_key should be in the format 'provider:model_id'. For example:
        - 'openai:gpt-3' for OpenAI's GPT-3 model.
        - 'deepseek:model' for a model from the DeepSeek provider.

    If the provider is 'openai', the OPENAI_CLIENT will be used.
    For other providers, the appropriate client will be fetched using get_alt_client_from_model_key.
    """
    provider, model_id = get_provider_and_model_id(model_key)
    client = get_open_client(provider)
    return client.chat.completions.create(
        model=model_id,
        messages=messages,
    )


@traceable(run_type="llm")
def structure_chat_completion(
    output_schema: Type[Any],
    messages: list[ChatCompletionMessageParam],
    model_key: str = GPT_STRUCTURE_OUTPUT_MODEL,
) -> ParsedChatCompletion:
    """
    Generate a structured chat completion based on the provided messages and output schema.

    Args:
        output_schema (Type[Any]): The schema to use for parsing the response.
        messages (list[ChatCompletionMessageParam]): The list of messages to be used for the chat completion.
        model_key (str): The model key in the format 'provider:model_id'. Defaults to 'openai:gpt-3'.
                         If the provider is not specified, it defaults to OpenAI.

    Returns:
        ParsedChatCompletion: The structured chat completion result.

    The model_key should be in the format 'provider:model_id'. For example:
        - 'openai:gpt-3' for OpenAI's GPT-3 model.
        - 'deepseek:model' for a model from the DeepSeek provider.

    If the provider is 'openai', the OPENAI_CLIENT will be used.
    For other providers, the appropriate client will be fetched using get_alt_client_from_model_key.
    """
    provider, model_id = get_provider_and_model_id(model_key)
    client = get_open_client(provider)

    completion = client.beta.chat.completions.parse(
        model=model_id,
        messages=messages,
        response_format=output_schema,
    )
    return completion


def simple_assistant(prompt: str, model_key: str = GPT_CHAT_MODEL) -> str:
    """Simple assistant with prompt."""
    response = chat_complete(
        model_key=model_key,
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": prompt},
        ],
    )
    return get_message_from_completion(completion=response)


def structure_simple_assistant(
    prompt: str,
    output_schema: Type[Any],
    model_key: str = GPT_STRUCTURE_OUTPUT_MODEL,
) -> Any:
    """Simple assistant with structured output from prompt."""
    response = structure_chat_completion(
        output_schema=output_schema,
        messages=[
            {
                "role": "system",
                "content": "Assist user with the task with structure output",
            },
            {"role": "user", "content": prompt},
        ],
        model_key=model_key,
    )
    return get_parsed_choice_from_completion(completion=response)
