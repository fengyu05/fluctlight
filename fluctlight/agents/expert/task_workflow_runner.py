from typing import Any
from fluctlight.agents.expert.data_model import (
    IntakeHistoryMessage,
)
from fluctlight.agents.expert.task_workflow_config import (
    INTERNAL_UPSTREAM_HISTORY_MESSAGES,
    WorkflowNodeOutput,
    WorkflowInvocationState,
    has_internal_upstreams,
    WorkflowConfig,
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

    def current_has_internal_upstreams(self) -> bool:
        """Checks if the current node has internal upstreams."""
        return has_internal_upstreams(self.get_current_upstreams())

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

    def process_message(self, *args: Any, **kwargs: Any) -> tuple[str, Any]:
        cur_node = self.get_current_node()
        events = self._graph.stream(self._ic, stream_mode="values")
        for event in events:
            last_event = event

        # Cast the event(a dict) back to WorkflowInvocationState
        last_state = WorkflowInvocationState(
            current_node=last_event["current_node"],
            running_state=last_event["running_state"],
            output_state=last_event["output_state"],
        )
        output_value = last_state.running_state[cur_node]
        output_state: WorkflowNodeOutput = last_state.output_state[cur_node]
        result = (cur_node, output_value)

        # update state
        self._ic.running_state[cur_node] = output_value
        self._ic.output_state[cur_node] = output_state

        if (
            output_state.output_type == "SUCCESS"
            or output_state.output_type == "LOOP_MESSAGE_TRUE"
        ):
            # move to next step
            if cur_node == self._config.end:
                self._ic.current_node = _END
            else:
                downstreams = self.get_node_downstreams(cur_node)
                next_downstream = downstreams[0]
                self._ic.current_node = next_downstream
        elif output_state.output_type == "LOOP_MESSAGE_FALSE":
            # output loop message
            result = (cur_node, output_state.loop_message)
        else:
            raise ValueError(f"Unknow output type. {output_state}")

        return result
