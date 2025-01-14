from typing import Any, Optional

from fluctlight.agents.expert.data_model import (
    IntakeHistoryMessage,
    IntakeMessage,
)
from fluctlight.agents.expert.task_workflow_config import (
    INTERNAL_UPSTREAM_HISTORY_MESSAGES,
    INTERNAL_UPSTREAM_INPUT_MESSAGE,
    WorkflowInvocationState,
    is_internal_upstream,
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

    def _process_workflow_upstream_input(
        self, workflow_runner: WorkflowRunner, message_text: str
    ):
        upstreams = workflow_runner.get_current_upstreams()
        for upstream in upstreams:
            if not is_internal_upstream(upstream):
                continue
            if upstream == INTERNAL_UPSTREAM_INPUT_MESSAGE:
                workflow_runner.update_running_state(
                    {
                        INTERNAL_UPSTREAM_INPUT_MESSAGE: IntakeMessage(
                            text=message_text,
                        )
                    }
                )
            elif upstream == INTERNAL_UPSTREAM_HISTORY_MESSAGES:
                pass

    def process_message(
        self, message: IMessage, message_intent: MessageIntent
    ) -> list[str]:
        ic: WorkflowInvocationState = self.retrieve_context(message)
        responses: list[str] = []

        # build or restore worflow runner
        workflow_runner = WorkflowRunner(self._config, ic=ic)
        assistant_response = ""
        while not workflow_runner.is_ended():
            # handle workflow upstream input
            self._process_workflow_upstream_input(workflow_runner, message.text)

            # workflow process
            _, assistant_response = workflow_runner.run()

            # if current unhandled node have input message, break to obtain new input message
            # otherwise continue to handle next node
            if workflow_runner.has_input_message_in_current_upstreams():
                break

        # update ic context
        responses.append(str(assistant_response))
        workflow_runner.append_history_message(message.text, str(assistant_response))
        logger.info("Task agent process message", name=self._name, ic=ic)
        return responses

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description
