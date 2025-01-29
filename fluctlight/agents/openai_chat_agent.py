from collections import OrderedDict
from typing import Any, Callable

import fluctlight.agents.prompt_bank as prompt_bank
from fluctlight.agents.message_intent_agent import MessageIntentAgent
from fluctlight.audio.speech_to_text import get_speech_to_text
from fluctlight.data_model.interface import IAttachment, IMessage
from fluctlight.intent.message_intent import MessageIntent, create_intent
from fluctlight.logger import get_logger
from fluctlight.open.chat import get_message_from_completion
from fluctlight.open.common import AUDIO_INPUT_SUPPORT_TYPE, VISION_INPUT_SUPPORT_TYPE
from fluctlight.settings import (
    GPT_CHAT_MODEL,
    GPT_REASON_MODEL,
    SLACK_APP_OAUTH_TOKENS_FOR_WS,
    is_slack_bot,
)
from fluctlight.constants import GPT_4O
from fluctlight.utt.files import base64_encode_media, download_media
from fluctlight.open.chat import chat_complete

logger = get_logger(__name__)


_AGENT_DESCRIPTION = """ Use this agent to make a natural converastion between the assistant bot and user."""
INTENT_KEY = "CHAT"


class OpenAiChatAgent(MessageIntentAgent):
    """
    A Chat Agent using Open chat.completion API.
    Conversation is kept with message_buffer keyed by thread_id, with a max buffer limit of 100
    converation(respect to LRU).
    """

    def __init__(
        self,
        transcribe_slack_audio: Callable[[str, str], str] = None,
        buffer_limit: int = 20,
        chatbot_model_id: str = GPT_CHAT_MODEL,
        intent_key: str = INTENT_KEY,
    ) -> None:
        super().__init__(intent=create_intent(intent_key))
        self.message_buffer = OrderedDict()
        self.buffer_limit = buffer_limit
        self.transcribe_slack_audio = transcribe_slack_audio
        self.speech_to_text = get_speech_to_text()
        self.bearer_token = SLACK_APP_OAUTH_TOKENS_FOR_WS if is_slack_bot() else None
        self.chatbot_model_id = chatbot_model_id

    @property
    def name(self) -> str:
        return "OpenAIChatAgent"

    @property
    def description(self) -> str:
        return _AGENT_DESCRIPTION

    def get_system_role(self, model_id: str) -> str:
        if model_id.startswith("o1") or model_id.startswith("o3"):
            return "developer"
        else:
            # deepseek model, etc
            return "system"

    def process_message(
        self, message: IMessage, message_intent: MessageIntent
    ) -> list[str]:
        """
        Processes a message event and generates a response using an AI model.

        This method handles incoming message events, processes any attached files,
        and generates a response from the AI. It maintains a conversation history
        for each unique thread identified by `thread_id`.
        """
        thread_id = message.thread_message_id

        # Move the accessed thread_id to the end to mark it as recently used
        if thread_id in self.message_buffer:
            self.message_buffer.move_to_end(thread_id)
        else:
            self.message_buffer[thread_id] = []
            if not self.chatbot_model_id.startswith("o1"):
                self.message_buffer[thread_id].append(
                    {
                        "role": self.get_system_role(self.chatbot_model_id),
                        "content": prompt_bank.CONVERSATION_BOT_1,
                    }
                )
        # If the buffer exceeds limit items, remove the oldest one
        if len(self.message_buffer) > self.buffer_limit:
            self.message_buffer.popitem(last=False)

        content = [{"type": "text", "text": message.text}]
        if message.has_attachments:
            content_from_files = self.process_files(message)
            content.extend(content_from_files)

        self.message_buffer[thread_id].append(
            {
                "role": "user",
                "content": content,
            }
        )
        model_id = self.chatbot_model_id
        for message in self.message_buffer[thread_id]:
            if message["role"] == "user" and self.has_image_in_content(
                message["content"]
            ):
                model_id = GPT_4O
                break

        response = chat_complete(
            messages=self.message_buffer[thread_id], model_key=model_id
        )
        logger.info("response", response=response)
        output_text = get_message_from_completion(response)
        self.message_buffer[thread_id].append(
            {
                "role": "assistant",
                "content": output_text,
            }
        )
        return [output_text]

    def has_image_in_content(self, content: list[dict[str, Any]]) -> bool:
        for item in content:
            if item["type"] == "image_url":
                return True
        return False

    def process_files(self, message: IMessage) -> list[dict]:
        """
        Process data by examining each file and determining its type.
        """
        data = []
        assert message.attachments, "message_event.files can not be None"
        for attachment in message.attachments:
            if self._accept_vision_content_type(attachment):
                base64_image = base64_encode_media(
                    attachment.url, bearer_token=self.bearer_token
                )
                data.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "low",
                        },
                    }
                )
            elif self._accept_slack_audio(attachment):
                data.append(
                    {
                        "type": "text",
                        "text": self.transcribe_slack_audio(
                            channel=message.channel.id, timestamp=message.ts
                        ),
                    }
                )
            elif self._accept_audio_content_type(attachment):
                data.append(
                    {
                        "type": "text",
                        "text": self._transcribe_audio(attachment),
                    }
                )
        return data

    def _accept_vision_content_type(self, attachment: IAttachment) -> bool:
        return attachment.content_type in VISION_INPUT_SUPPORT_TYPE

    def _accept_audio_content_type(self, attachment: IAttachment) -> bool:
        return attachment.content_type in AUDIO_INPUT_SUPPORT_TYPE

    def _accept_slack_audio(self, attachment: IAttachment) -> bool:
        if attachment.subtype == "slack_audio":
            if self.transcribe_slack_audio is None:
                logger.warn(
                    "transcribe_slack_audio didn't setup for the agent, ignore the transcribe request"
                )
                return False
            return True
        return False

    def _transcribe_audio(self, attachment: IAttachment) -> str:
        logger.info("attachment for transcribe", attachment=attachment)
        media = download_media(attachment.url, bearer_token=self.bearer_token)
        logger.info("medata", media_type=type(media), lenn=len(media))
        return self.speech_to_text.transcribe(audio_bytes=media)

    def _format_buffer(self, buffer: list[dict[str, Any]]) -> list[str]:
        output = []
        for item in buffer:
            if isinstance(item["content"], str):
                output.append(f'[{item["role"]}]: {item["content"]}')
            elif isinstance(item["content"], list):
                for content_item in item["content"]:
                    if content_item["type"] == "text":
                        output.append(f']{item["role"]}]: {content_item["text"]}')
                    elif content_item["type"] == "image_url":
                        output.append(f'[{item["role"]}]: attach an image')
        return output


def create_reason_agent() -> OpenAiChatAgent:
    return OpenAiChatAgent(
        chatbot_model_id=GPT_REASON_MODEL,
        intent_key="REASON",
    )
