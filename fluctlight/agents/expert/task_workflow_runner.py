from typing import Any
from fluctlight.agents.expert.data_model import (
    IntakeHistoryMessage,
    IntakeMessage,
)
from fluctlight.agents.expert.task_workflow_config import (
    INTERNAL_UPSTREAM_INPUT_MESSAGE,
    INTERNAL_UPSTREAM_HISTORY_MESSAGES,
    WorkflowNodeOutput,
    WorkflowInvocationState,
    WorkflowConfig,
    is_internal_upstream,
)

from fluctlight.agents.expert.task_workflow import build_workflow_graph
from fluctlight.logger import get_logger

logger = get_logger(__name__)

_END = "END"


class WorkflowRunner:
    def __init__(
        self,
        config: WorkflowConfig,
        ic: WorkflowInvocationState,
    ):
        self._config = config
        self._graph = build_workflow_graph(config)
        self._ic: WorkflowInvocationState = ic

    @property
    def ic(self) -> WorkflowInvocationState:
        return self._ic

    def get_current_node(self) -> str:
        return self._ic.current_node

    def is_ended(self) -> bool:
        return self.get_current_node() == _END

    def get_current_upstreams(self) -> list[str]:
        """Returns the upstream nodes for the current node."""
        cur_node = self.get_current_node()
        if cur_node == _END:
            return []

        if cur_node not in self._config.nodes:
            raise ValueError(f"{cur_node} does not exist in the configuration.")

        input_schema = self._config.nodes[cur_node].input_schema
        return list(input_schema.keys())

    def has_input_message_in_current_upstreams(self) -> bool:
        return INTERNAL_UPSTREAM_INPUT_MESSAGE in self.get_current_upstreams()

    def get_node_downstreams(self, node: str) -> list[str]:
        """Returns the downstream nodes for a given node."""
        downstreams = {
            k for k, v in self._config.nodes.items() if node in v.input_schema
        }
        return list(downstreams)

    def update_running_state(self, context: dict[str, Any]):
        """Updates the running state with the provided context."""
        self._ic.running_state.update(context)

    def append_history_message(self, user: str, assistant: str):
        """Appends user and assistant messages to the history."""
        if INTERNAL_UPSTREAM_HISTORY_MESSAGES not in self._ic.running_state:
            self._ic.running_state[INTERNAL_UPSTREAM_HISTORY_MESSAGES] = (
                IntakeHistoryMessage()
            )
        self._ic.running_state[INTERNAL_UPSTREAM_HISTORY_MESSAGES].messages.extend(
            [user, assistant]
        )

    def process_workflow_upstream_input(self, message_text: str):
        upstreams = self.get_current_upstreams()
        for upstream in upstreams:
            if not is_internal_upstream(upstream):
                continue
            if upstream == INTERNAL_UPSTREAM_INPUT_MESSAGE:
                self.update_running_state(
                    {
                        INTERNAL_UPSTREAM_INPUT_MESSAGE: IntakeMessage(
                            text=message_text,
                        )
                    }
                )
            elif upstream == INTERNAL_UPSTREAM_HISTORY_MESSAGES:
                pass

    def run(self, message_text: str) -> WorkflowNodeOutput:
        self.process_workflow_upstream_input(message_text)

        cur_node = self.get_current_node()
        events = self._graph.stream(self._ic, stream_mode="values")
        for event in events:
            last_event = event

        # Cast the event(a dict) back to WorkflowInvocationState
        last_state = WorkflowInvocationState(
            current_node=last_event["current_node"],
            running_state=last_event["running_state"],
            output=last_event["output"],
        )
        output_state = last_state.running_state[cur_node]
        node_output: WorkflowNodeOutput = last_state.output[cur_node]

        # update state
        self._ic.running_state[cur_node] = output_state
        self._ic.output[cur_node] = node_output
        if (
            node_output.status == "SUCCESS"
            or node_output.status == "LOOP_MESSAGE_CHECK_PASSED"
        ):
            # move to next step
            if cur_node == self._config.end:
                self._ic.current_node = _END
                logger.debug("move to END")
            else:
                downstreams = self.get_node_downstreams(cur_node)
                next_downstream = downstreams[0]
                self._ic.current_node = next_downstream
                logger.debug("move to next", next_downstream=next_downstream)

        self.append_history_message(message_text, node_output.message)
        return node_output
