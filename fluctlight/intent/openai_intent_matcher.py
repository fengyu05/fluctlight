import re
from functools import cached_property

from fluctlight.constants import GPT_4O_MINI
from fluctlight.intent.intent_agent import IntentAgent
from fluctlight.intent.intent_matcher_base import IntentMatcher
from fluctlight.intent.message_intent import MessageIntent, create_intent
from fluctlight.logger import get_logger
from fluctlight.open.chat import (
    simple_assistant,
    structure_simple_assistant,
)

logger = get_logger(__name__)


class OpenAIIntentMatcher(IntentMatcher):
    def __init__(
        self,
        agents: list[IntentAgent],
        use_strcuture_output: bool = False,
    ) -> None:
        super().__init__(
            agents=agents,
        )
        self.use_structure_output = use_strcuture_output

    def parse_intent(self, text: str) -> MessageIntent:
        if self.use_structure_output:
            prompt = self.match_intent_prompt_structure(message=text)
            logger.debug("LLM intent matching", prompt=prompt)
            message_intent = structure_simple_assistant(
                model_id=GPT_4O_MINI, prompt=prompt, output_schema=MessageIntent
            )
        else:
            prompt = self.match_intent_prompt_non_structure(message=text)
            logger.debug("LLM intent matching", prompt=prompt)
            selected_text = simple_assistant(model_id=GPT_4O_MINI, prompt=prompt)
            logger.debug(
                "LLM intent matching selected_text", selected_text=selected_text
            )
            message_intent = self.get_message_intent_from_index_text(selected_text)
        return message_intent

    def get_message_intent_from_index_text(self, text: str) -> MessageIntent:
        try:
            # Remove non-numeric characters from the text
            numeric_text = re.sub(r"\D", "", text)

            # Attempt to convert the sanitized text to an integer
            idx = int(numeric_text)
            return self.agents[idx].intent
        except ValueError:
            return create_intent("UNKNOWN")

    def match_intent_prompt_structure(self, message: str) -> str:
        return f"""Select one of the below task based on the user message.
-----------
{self.joined_agents_description_for_structure}
You may only use the option from the below.
If you can not detect a good match, use defaut task: Type='CHAT', Key=None.
{self.joined_agents_selection}
-----------------------
user_message: {message}
output:"""

    @cached_property
    def joined_agents_description_for_structure(self) -> str:
        result = "".join(
            [
                f"key={agent.intent.key}: {agent.description} \n---\n"
                for agent in self.agents
                if agent.llm_matchable
            ]
        )
        return result

    @cached_property
    def joined_agents_selection(self) -> str:
        return "".join(
            [
                f"key={agent.intent.key} \n---\n"
                for agent in self.agents
                if agent.llm_matchable
            ]
        )

    def match_intent_prompt_non_structure(self, message: str) -> str:
        return f"""Select one of the below task based on the user message.
-----------
{self.joined_agents_description_list}
You may only use the option from the below. Output format should only include one number for the above tasks.
If you can not detect a good match, use defaut task: 0)
-----------------------
user_message: {message}
output:"""

    @cached_property
    def joined_agents_description_list(self) -> str:
        result = "".join(
            [f"{i}: {agent.description} \n---\n" for i, agent in enumerate(self.agents)]
        )
        return result
