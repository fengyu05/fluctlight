from typing import Any, Type
from langsmith import traceable
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat import ParsedChatCompletion
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from fluctlight.settings import GPT_STRUCTURE_OUTPUT_MODEL, GPT_CHAT_MODEL

from . import OPENAI_CLIENT
from . import DEEPSEEK_CLIENT


def get_message_from_completion(completion: ChatCompletion, idx: int = 0) -> str:
    return completion.choices[idx].message.content


def get_parsed_choice_from_completion(completion: ChatCompletion, idx: int = 0) -> Any:
    return completion.choices[idx].message.parsed


@traceable(run_type="llm")
def chat_complete(
    messages: list[ChatCompletionMessageParam],
    model_id: str = GPT_CHAT_MODEL,
    temperature: float = 0.0,
) -> ChatCompletion:
    """Chat completion with messages."""
    if model_id.startswith("deepseek"):
        return DEEPSEEK_CLIENT.chat.completions.create(
            temperature=temperature,
            model=model_id,
            messages=messages,
        )
    else:
        return OPENAI_CLIENT.chat.completions.create(
            temperature=temperature,
            model=model_id,
            messages=messages,
        )


@traceable(run_type="llm")
def structure_chat_completion(
    output_schema: Type[Any],
    messages: list[ChatCompletionMessageParam],
    model_id: str = GPT_STRUCTURE_OUTPUT_MODEL,
) -> ParsedChatCompletion:
    """Structure chat completion with messages."""
    if model_id.startswith("deepseek"):
        raise ValueError("Deepseek does not support structured output yet.")
    else:
        completion = OPENAI_CLIENT.beta.chat.completions.parse(
            temperature=0,
            model=model_id,
            messages=messages,
            response_format=output_schema,
        )
        return completion


def simple_assistant(prompt: str, model_id: str = GPT_CHAT_MODEL) -> str:
    """Simple assistant with prompt."""
    response = chat_complete(
        model_id=model_id,
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": prompt},
        ],
    )
    return get_message_from_completion(completion=response)


def structure_simple_assistant(
    prompt: str,
    output_schema: Type[Any],
    model_id: str = GPT_STRUCTURE_OUTPUT_MODEL,
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
        model_id=model_id,
    )
    return get_parsed_choice_from_completion(completion=response)
