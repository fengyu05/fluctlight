import time
from typing import Any
from fluctlight.agents.expert.data_model import (
    IntakeHistoryMessage,
    IntakeMessage,
)

from fluctlight.agents.expert.workflow_config import (
    INTERNAL_UPSTREAM_HISTORY_MESSAGES,
    INTERNAL_UPSTREAM_INPUT_MESSAGE,
    WorkflowRunningState,
    WorkflowConfig,
    is_internal_upstream,
)
from fluctlight.agents.expert.workflow_runner import WorkflowRunner
from fluctlight.agents.message_intent_agent import MessageIntentAgent
from fluctlight.data_model.interface import IMessage
from fluctlight.intent.message_intent import MessageIntent
from fluctlight.logger import get_logger

logger = get_logger(__name__)
EMPTY_LOOP_MESSAGE = "Cannot proceed with the request, please try again :bow:"


class InvocationContext:
    context: dict[str, Any]


    def has_workflow_session(self) -> bool:
        return "workflow_session" in self.context


class WorkflowAgent(MessageIntentAgent):
    def __init__(
        self,
        name: str,
        description: str,
        intent: MessageIntent,
        workflow_config: WorkflowConfig | None = None,
    ) -> None:
        super().__init__(intent=intent)
        self._name = name
        self._description = description
        self._intent = intent
        self._workflow_config = workflow_config
        self._ic = InvocationContext()

    def retrieve_context(self, message: IMessage) -> InvocationContext:
        return self._ic

    def process_message(
        self, message: IMessage, message_intent: MessageIntent
    ) -> list[str]:
        ic = self.retrieve_context(message)
        assert message.text, "message text is missing"

        if ic.has_workflow_session():
            workflow_session: WorkflowRunningState = ic.context["workflow_session"]
            logger.info("recover session ", session=workflow_session)
        else: # First message enagement
            workflow_session: WorkflowRunningState = WorkflowRunningState(
                session_id=str(int(time.time())),
                current_node=self._workflow_config.begin,
                running_state=ic.context.copy(),
                output_state={},
            )

        # TODO: zf: cleanup
        # if INTERNAL_UPSTREAM_HISTORY_MESSAGES in self._context:
        #     workflow_session["running_state"][
        #         INTERNAL_UPSTREAM_HISTORY_MESSAGES
        #     ] = self._context[INTERNAL_UPSTREAM_HISTORY_MESSAGES]
        #     logger.info("load historys", history=str(self._context[INTERNAL_UPSTREAM_HISTORY_MESSAGES]))

        response = self.run_task_with_workflow_session(
            message.text, ic, self._workflow_config, workflow_session
        )
        logger.info("response", response=response)
        return response 

    def _process_workflow_upstream_input(
        self, workflow_runner: WorkflowRunner, message_text: str
    ) -> None:
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
        ic: InvocationContext,
        workflow_config: WorkflowConfig,
        workflow_session: WorkflowRunningState,
    ) -> Any:
        workflow_runner = WorkflowRunner(
            workflow_config,
            workflow_session=workflow_session,
        )

        assistant_response: Any = None
        while not workflow_runner.is_finished():
            # handle workflow upstream input
            self._process_workflow_upstream_input(workflow_runner, message_text)

            # workflow process
            task_name, assistant_response = workflow_runner.process_message()
            logger.info("workflow runner processed message", task_name=task_name, response=assistant_response)

            # if current unhandled node have input message, break to obtain new input message
            # otherwise continue to handle next node
            if workflow_runner.current_has_internal_upstreams():
                break

        # update ic context
        ic.context.update({"workflow_session": workflow_runner.get_session_state()})
        return assistant_response

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

