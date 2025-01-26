from typing import Any, Optional

from fluctlight.agents.expert.data_model import (
    IntakeHistoryMessage,
)
from fluctlight.agents.expert.task_workflow_config import (
    INTERNAL_UPSTREAM_HISTORY_MESSAGES,
    WorkflowInvocationState,
    WorkflowConfig,
)
from fluctlight.agents.expert.task_workflow_runner import WorkflowRunner
from fluctlight.agents.message_intent_agent import MessageIntentAgent
from fluctlight.data_model.interface import IMessage
from fluctlight.intent.message_intent import MessageIntent
from fluctlight.logger import get_logger

logger = get_logger(__name__)


class TaskWorkflowAgent(MessageIntentAgent):
    def __init__(
        self,
        name: str,
        description: str,
        intent: MessageIntent,
        config: WorkflowConfig,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(intent=intent)
        self._name = name
        self._description = description
        self._intent = intent
        self._context = context or {}
        self._config = config
        self._invocation_contexts = {}

    def retrieve_context(self, message: IMessage) -> WorkflowInvocationState:
        if message.thread_message_id not in self._invocation_contexts:
            running_state = self._context.copy()
            running_state[INTERNAL_UPSTREAM_HISTORY_MESSAGES] = IntakeHistoryMessage(
                messages=[]
            )
            self._invocation_contexts[message.thread_message_id] = (
                WorkflowInvocationState(
                    running_state=running_state,
                    current_node=self._config.begin,
                )
            )
        return self._invocation_contexts[message.thread_message_id]

    def process_message(
        self, message: IMessage, message_intent: MessageIntent
    ) -> list[str]:
        ic: WorkflowInvocationState = self.retrieve_context(message)
        responses: list[str] = []
        # build or restore worflow runner
        workflow_runner = WorkflowRunner(self._config, ic=ic)
        while not workflow_runner.is_ended():
            node_output = workflow_runner.run(message_text=message.text)
            responses.append(node_output.message)
            logger.debug("Task agent process message", name=self._name, ic=ic)
            # if current unhandled node have input message, break to obtain new input message
            # otherwise continue to handle next node
            if workflow_runner.has_input_message_in_current_upstreams():
                break

        return responses

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description
