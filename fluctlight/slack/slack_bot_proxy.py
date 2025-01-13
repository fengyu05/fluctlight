from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from fluctlight.agents.character import create_default_character_agent
from fluctlight.agents.message_intent_agent import MessageIntentAgent
from fluctlight.agents.openai_chat_agent import OpenAiChatAgent
from fluctlight.core.bot_proxy import BotProxy
from fluctlight.data_model.slack import MessageEvent
from fluctlight.intent.intent_matcher_base import IntentMatcher
from fluctlight.logger import get_logger
from fluctlight.slack.adaper import Adapter
from fluctlight.slack.chat import SlackChat
from fluctlight.slack.messages_fetcher import MessagesFetcher
from fluctlight.slack.reaction import SlackReaction
from fluctlight.utt.singleton import Singleton
from fluctlight.intent import get_default_intent_matcher

logger = get_logger(__name__)


class SlackBotProxy(BotProxy, MessagesFetcher, SlackChat, SlackReaction, Singleton):
    slack_client: WebClient
    intent_matcher: IntentMatcher
    bot_user_id: str
    agents: list[MessageIntentAgent]
    adapter: Adapter

    def __init__(self, slack_client: WebClient):
        self.slack_client = slack_client
        self.bot_user_id = self.get_bot_user_id()
        self.chat_agent = OpenAiChatAgent(transcribe_slack_audio=self.transcribe_audio)
        self.adapter = Adapter()

        from fluctlight.agents.expert.shopping_assist import (
            create_shopping_assist_task_graph_agent,
        )

        self.agents = [
            create_default_character_agent(),
            self.chat_agent,
            create_shopping_assist_task_graph_agent(),
        ]
        self.intent_matcher = get_default_intent_matcher(self.agents)

    def _should_reply(self, message_event: MessageEvent) -> bool:
        return message_event.channel_type == "im" or message_event.is_user_mentioned(
            self.bot_user_id
        )

    def on_message(self, message: MessageEvent) -> None:
        if not self._should_reply(message):
            return
        imessage = self.adapter.cast_message(message)
        logger.info("imessage", message=imessage)

        self.add_reaction(event=message, reaction_name="eyes")
        message_intent = self.intent_matcher.match_message_intent(message=imessage)
        if message_intent.unknown:
            self.chat_agent(message=imessage, message_intent=message_intent)
        else:
            for agent in self.agents:
                msgs = agent(message=imessage, message_intent=message_intent)
                if msgs is None:  ## agent didn't process this intent
                    continue
                for msg in msgs:
                    self.reply_to_message(event=message, text=msg)

    def get_bot_user_id(self) -> str:
        """
        This function returns the user ID of the bot currently connected to the Slack API.
        """
        try:
            # Call the auth.test method using the WebClient
            response = self.slack_client.auth_test()

            # Extract and return the bot user ID from the response
            return response["user_id"]

        except SlackApiError as e:
            logger.error("Error getting bot user ID", error=str(e))
