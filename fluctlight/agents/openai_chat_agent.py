from collections import OrderedDict
from typing import Any, Callable

import fluctlight.agents.prompt_bank as prompt_bank
from fluctlight.agents.message_intent_agent import MessageIntentAgent
from fluctlight.audio.speech_to_text import get_speech_to_text
from fluctlight.data_model.interface import IAttachment, IMessage
from fluctlight.intent.message_intent import MessageIntent, create_intent
from fluctlight.logger import get_logger
from fluctlight.open.chat import get_message_from_completion
from fluctlight.open.utils import (
    AUDIO_INPUT_SUPPORT_TYPE,
    VISION_INPUT_SUPPORT_TYPE,
    is_o_series_model,
    vision_support_model,
)
from fluctlight.settings import (
    GPT_CHAT_MODEL,
    GPT_REASON_MODEL,
    GPT_VISION_MODEL,
    SLACK_APP_OAUTH_TOKENS_FOR_WS,
    is_slack_bot,
)
from fluctlight.utt.files import base64_encode_media, download_media
from fluctlight.open.chat import chat_complete
from fluctlight.open.think_format_util import extract_think_message

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
        chat_model_id: str = GPT_CHAT_MODEL,
        reason_model_id: str = GPT_REASON_MODEL,
        vision_model_id: str = GPT_VISION_MODEL,
        intent_key: str = INTENT_KEY,
    ) -> None:
        super().__init__(intent=create_intent(intent_key))
        self.message_buffer = OrderedDict()
        self.buffer_limit = buffer_limit
        self.transcribe_slack_audio = transcribe_slack_audio
        self.speech_to_text = get_speech_to_text()
        self.bearer_token = SLACK_APP_OAUTH_TOKENS_FOR_WS if is_slack_bot() else None
        self.chat_model_id = chat_model_id
        self.reason_model_id = reason_model_id
        self.vision_model_id = vision_model_id

    @property
    def name(self) -> str:
        return "OpenAIChatAgent"

    @property
    def description(self) -> str:
        return _AGENT_DESCRIPTION

    def get_system_role(self, model_id: str) -> str:
        if is_o_series_model(model_id):
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
        model_id = self.reason_model_id if message_intent.reason else self.chat_model_id
        # Move the accessed thread_id to the end to mark it as recently used
        if thread_id in self.message_buffer:
            self.message_buffer.move_to_end(thread_id)
        else:
            self.message_buffer[thread_id] = []
            if not is_o_series_model(model_id):
                self.message_buffer[thread_id].append(
                    {
                        "role": self.get_system_role(model_id),
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

        if self.has_image_in_content(content) and not vision_support_model(model_id):
            model_id = self.vision_model_id

        response = chat_complete(
            messages=self.message_buffer[thread_id].copy(), model_key=model_id
        )
        logger.info("response", response=response)
        output_text = get_message_from_completion(response)
        self.message_buffer[thread_id].append(
            {
                "role": "assistant",
                "content": output_text,
            }
        )
        return extract_think_message(output_text)

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
