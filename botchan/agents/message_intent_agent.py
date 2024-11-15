from abc import abstractmethod
from typing import Any

from botchan.data_model.interface import IMessage
from botchan.intent.intent_agent import IntentAgent
from botchan.intent.message_intent import MessageIntent
from botchan.logger import get_logger
from botchan.task import Task

logger = get_logger(__name__)


class MessageIntentAgent(Task, IntentAgent):
    """
    Provides an abstract framework for multi intent message processing agent.

    Methods:
        __init__(): Constructs a new instance of MessageIntentAgent.
        process(*args: Any, **kwds: Any) -> Any: Executes the main logic to handle a message event.
        process_message(message: CoreMessage) -> list[str]: An abstract method that must be overridden to define how a message event is processed.
        should_process(*args: Any, **kwds: Any) -> bool: Evaluates whether the specified intent requires processing based on the arguments provided.

    Properties:
        name (str): Provides the name identifier of the agent.
        intent (MessageIntent): An abstract property returning the agent's intent.
    """

    def __init__(self, intent: MessageIntent) -> None:
        super().__init__()
        self._intent = intent

    def process(self, *args: Any, **kwds: Any) -> Any:
        message: IMessage = self._require_input(
            kwargs=kwds, key="message", value_type=IMessage
        )
        msgs = self.process_message(message)
        logger.debug("agent process messult result", agent=self.name, msg=msgs)
        return msgs

    @abstractmethod
    def process_message(self, message: IMessage) -> list[str]:
        pass

    def should_process(self, *args: Any, **kwds: Any) -> bool:  # pylint: disable=unused-argument
        message_intent: MessageIntent = self._require_input(
            kwargs=kwds, key="message_intent", value_type=MessageIntent
        )
        return message_intent.equal_wo_metadata(self.intent)

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def intent(self) -> MessageIntent:
        return self._intent
