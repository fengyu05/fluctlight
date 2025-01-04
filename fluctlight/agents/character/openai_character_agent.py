from collections import defaultdict
from typing import Any, List, cast

from langchain.callbacks.base import AsyncCallbackHandler
from langchain.schema import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_community.chat_models import ChatOpenAI

from fluctlight.agent_catalog.catalog_manager import get_catalog_manager
from fluctlight.agents.character.base import CharacterAgent
from fluctlight.agents.expert.data_model import IntakeHistoryMessage
from fluctlight.agents.message_intent_agent import MessageIntentAgent
from fluctlight.data_model.interface import IMessage
from fluctlight.data_model.interface.character import Character
from fluctlight.embedding.chroma import get_chroma
from fluctlight.intent.message_intent import MessageIntent
from fluctlight.logger import get_logger
from fluctlight.utt.emoji import strip_leading_emoji
from fluctlight.agents.expert.task_agent import TaskAgent, TaskInvocationContext

logger = get_logger(__name__)

_CHAR_INTENT_KEY = "CHAR"


class OpenAICharacterAgent(CharacterAgent, MessageIntentAgent):
    history_buffer: dict[str, list[BaseMessage]]

    def __init__(
        self,
        model: str,
        temperature: float = 0.5,
        openai_api_base: str | None = None,
        openai_api_key: str | None = None,
    ):
        super().__init__(intent=MessageIntent(key=_CHAR_INTENT_KEY))
        self.chat_model = ChatOpenAI(
            model=model,
            temperature=temperature,
            streaming=True,
            openai_api_base=openai_api_base,
            openai_api_key=openai_api_key,
        )
        self.config = {
            "model": model,
            "temperature": temperature,
            "streaming": True,
            "openai_api_base": openai_api_base,
        }
        self.db = get_chroma()
        self.catalog_manager = get_catalog_manager()
        self.history_buffer = defaultdict(list)
        self._invocation_contexts: dict[str, TaskInvocationContext] = {}

    @property
    def name(self) -> str:
        return "OpenAICharacterAgent"

    @property
    def description(self) -> str:
        return ""

    @property
    def llm_matchable(self) -> bool:
        return False

    def process_message(
        self, message: IMessage, message_intent: MessageIntent
    ) -> list[str]:
        char_id = message_intent.get_metadata("char_id")
        character = self.catalog_manager.get_character(character_id=char_id)
        assert character, f"Character doesn't exisit, char_id={char_id}"
        output = []
        if character.task_config:
            # for DEBUG
            # output.append("I'm a task agent")
            # output.append(str(character.task_config))
            # 
            from fluctlight.agents.expert.task_workflow_config import TaskWorkflowConfig, WorkflowRunnerConfig
            from fluctlight.agents.expert.task_workflow import build_workflow_graph
            from fluctlight.intent.message_intent import create_intent
            
            workflow_config = TaskWorkflowConfig.load_from_config(character.task_config["workflow"])
            msgs: list[str] = []
            for msg in self.get_history(thread_id=message.thread_message_id, character=character):
                logger.info("=============================================== history: " + str(msg))
                msgs.append(str(msg))
            workflow_config.context["__HISTORY_MESSAGES"] = IntakeHistoryMessage(messages=msgs)

            agent = TaskAgent(
                name=character.task_config["name"],
                description=character.task_config["description"],
                intent=create_intent(character.task_config["intent_key"]),
                context=workflow_config.context,
                workflow_runner_config=WorkflowRunnerConfig(
                    config=workflow_config,
                    state_graph=build_workflow_graph(workflow_config),
                ),
                task_graph=[],
                contexts=self._invocation_contexts
            )
            response = self.task_agent_dispatch(task_agent=agent, message=message)
            
            from fluctlight.agents.expert.shopping_assist import ProductMatch, Order, create_inventory
            if isinstance(response, ProductMatch):
                if response.match:
                    response_text = self.chat(
                        history=self.get_history(
                            thread_id=message.thread_message_id, character=character
                        ),
                        user_input="""Based on the matched product information, ask the user if they would like to make a purchase.
ProductMatch: 
""" + cast(ProductMatch, response).model_dump_json(),
                        character=character,
                    )
                else:
                    response_text = self.chat(
                        history=self.get_history(
                            thread_id=message.thread_message_id, character=character
                        ),
                        user_input="""Based on the product list in stock, guide the user to purchase the items in the list.
Inventory:
""" + create_inventory().model_dump_json(),
                        character=character,
                    )
            elif isinstance(response, Order):
                response_text = self.chat(
                        history=self.get_history(
                            thread_id=message.thread_message_id, character=character
                        ),
                        user_input="""Based on the order information, inform the user that the order has been processed.
Order:
""" + cast(Order, response).model_dump_json(),
                        character=character,
                    )
            else:
                response_text = self.chat(
                    history=self.get_history(
                        thread_id=message.thread_message_id, character=character
                    ),
                    user_input=strip_leading_emoji(message.text),
                    character=character,
                )
            output.append(response_text)
        else:
            response_text = self.chat(
                history=self.get_history(
                    thread_id=message.thread_message_id, character=character
                ),
                user_input=strip_leading_emoji(message.text),
                character=character,
            )
            output.append(response_text)
        return output

    def task_agent_dispatch(
        self,
        task_agent: TaskAgent,  # pylint: disable=W0613:unused-argument
        message: IMessage,
    ) -> Any:
        response = task_agent.process_message2(message_event=message)
        return response

    def get_history(self, thread_id: str, character: Character) -> list[BaseMessage]:
        if thread_id not in self.history_buffer:
            self.history_buffer[thread_id].append(
                SystemMessage(
                    character.llm_system_prompt,
                )
            )
        return self.history_buffer[thread_id]

    def chat(
        self,
        history: list[BaseMessage],
        user_input: str,
        character: Character,
        callbacks: list[AsyncCallbackHandler] | None = None,
        metadata: dict | None = None,
    ) -> str:
        # 1. Generate context
        context = self._generate_context(user_input, character)

        # 2. Add user input to history
        history.append(
            HumanMessage(
                content=character.llm_user_prompt.format(
                    context=context, query=user_input
                )
            )
        )
        # 3. Generate response
        response = self.chat_model.generate(
            [history], callbacks=callbacks, metadata=metadata
        )
        logger.info(f"Response: {response}")
        text = response.generations[0][0].text
        history.append(AIMessage(content=text))
        return text

    def _generate_context(self, query, character: Character) -> str:
        docs = self.db.similarity_search(query)
        docs = [d for d in docs if d.metadata["character_name"] == character.name]
        logger.info(f"Found {len(docs)} documents")

        context = "\n".join([d.page_content for d in docs])
        return context
