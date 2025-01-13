import time
from dataclasses import dataclass
from typing import Any, Optional


from fluctlight.agents.expert.data_model import (
    IntakeHistoryMessage,
    IntakeMessage,
)
from fluctlight.agents.expert.task_workflow_config import (
    INTERNAL_UPSTREAM_HISTORY_MESSAGES,
    INTERNAL_UPSTREAM_INPUT_MESSAGE,
    WorkflowRunningState,
    is_internal_upstream,
    WorkflowConfig,
)
from fluctlight.agents.expert.task_workflow_runner import WorkflowRunner
from fluctlight.agents.message_intent_agent import MessageIntentAgent
from fluctlight.data_model.interface import IMessage
from fluctlight.intent.message_intent import MessageIntent
from fluctlight.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TaskInvocationContext:
    context: dict[str, Any]
    current_task_index: int = 0


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

    def retrieve_context(self, message: IMessage) -> TaskInvocationContext:
        if message.message_id not in self._invocation_contexts:
            self._invocation_contexts[message.message_id] = TaskInvocationContext(
                context=self._context.copy()
            )
        return self._invocation_contexts[message.message_id]

    def process_message(
        self, message: IMessage, message_intent: MessageIntent
    ) -> list[str]:
        ic = self.retrieve_context(message)
        assert message.text, "message text is missing"
        return self.run_task_with_ic(message.text, ic=ic)

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

    def run_task_with_workflow_session(
        self,
        message_text: str,
        ic: TaskInvocationContext,
        workflow_session: WorkflowRunningState,
    ) -> list[str]:
        responses: list[str] = []

        # build or restore worflow runner
        workflow_runner = WorkflowRunner(
            self._config,
            workflow_session=workflow_session,
        )

        assistant_response = ""
        while not workflow_runner.is_ended():
            # handle workflow upstream input
            self._process_workflow_upstream_input(workflow_runner, message_text)

            # workflow process
            _, assistant_response = workflow_runner.process_message()

            # if current unhandled node have input message, break to obtain new input message
            # otherwise continue to handle next node
            if workflow_runner.current_has_internal_upstreams():
                break

        # update ic context
        responses.append(str(assistant_response))
        workflow_runner.append_history_message(message_text, str(assistant_response))
        ic.context.update({"workflow_session": workflow_runner.get_session_state()})

        return responses

    def run_task_with_ic(
        self, message_text: str, ic: TaskInvocationContext
    ) -> list[str]:
        responses = []

        if "workflow_session" in ic.context:
            workflow_session: WorkflowRunningState = ic.context["workflow_session"]
        else:
            workflow_session: WorkflowRunningState = WorkflowRunningState(
                session_id=str(int(time.time())),
                current_node=self._config.begin,
                running_state=ic.context.copy(),
                output_state={},
            )
            workflow_session["running_state"][INTERNAL_UPSTREAM_HISTORY_MESSAGES] = (
                IntakeHistoryMessage(messages=[])
            )

        responses = self.run_task_with_workflow_session(
            message_text, ic, workflow_session
        )
        logger.info(
            "Task agent process message", name=self._name, all_output=ic.context
        )
        return responses

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description
