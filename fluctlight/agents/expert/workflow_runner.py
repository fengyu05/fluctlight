from typing import Any, Dict, List, Tuple

from fluctlight.agents.expert.data_model import IntakeHistoryMessage
from fluctlight.agents.expert.workflow_config import (
    INTERNAL_UPSTREAM_HISTORY_MESSAGES,
    WorkflowNodeOutput,
    WorkflowRunningState,
    WorkflowConfig,
    has_internal_upstreams,
)
from fluctlight.agents.expert.workflow import build_workflow_graph
from fluctlight.logger import get_logger

logger = get_logger(__name__)

class WorkflowRunner:
    def __init__(
        self,
        config: WorkflowConfig,
        workflow_session: WorkflowRunningState,
    ):
        self._config = config
        self._graph = build_workflow_graph(config)
        self._state = workflow_session.copy()

    def get_session_state(self) -> WorkflowRunningState:
        """Returns the current workflow session state."""
        return self._state

    def get_current_node(self) -> str:
        """Returns the current node in the workflow."""
        return self._state["current_node"]
    
    def is_finished(self) -> bool:
        return self.get_current_node() == 'END'

    def get_current_upstreams(self) -> List[str]:
        """Returns the upstream nodes for the current node."""
        cur_node = self.get_current_node()
        if cur_node == "END":
            return []

        if cur_node not in self._config.nodes:
            raise ValueError(f"{cur_node} does not exist in the configuration.")

        input_schema = self._config.nodes[cur_node].input_schema
        return list(input_schema.keys())

    def current_has_internal_upstreams(self) -> bool:
        """Checks if the current node has internal upstreams."""
        return has_internal_upstreams(self.get_current_upstreams())

    def get_node_downstreams(self, node: str) -> List[str]:
        """Returns the downstream nodes for a given node."""
        downstreams = {k for k, v in self._config.nodes.items() if node in v.input_schema}
        return list(downstreams)

    def update_running_state(self, context: Dict[str, Any]):
        """Updates the running state with the provided context."""
        self._state["running_state"].update(context)

    def append_history_message(self, user: str, assistant: str):
        """Appends user and assistant messages to the history."""
        history = self._state["running_state"].get(INTERNAL_UPSTREAM_HISTORY_MESSAGES, IntakeHistoryMessage(messages=[]))
        history.messages.extend([user, assistant])
        self._state["running_state"][INTERNAL_UPSTREAM_HISTORY_MESSAGES] = history

    def process_message(self, *args: Any, **kwargs: Any) -> Tuple[str, Any]:
        """Processes a message and updates the workflow state."""
        cur_node = self.get_current_node()
        if cur_node == "END":
            self._state["current_node"] = self._config.begin
            cur_node = self._config.begin

        events = iter(self._graph.stream(self._state, stream_mode="values"))
        last_state = next(events, None)

        if last_state is None:
            raise ValueError("No events found in the state graph stream.")

        output_value = last_state["running_state"][cur_node]
        output_state: WorkflowNodeOutput = last_state["output_state"][cur_node]
        result = (cur_node, output_value)
        logger.debug("process_node", cur_node=cur_node, output_value=output_value, result=result)

        # Update state
        self._state["running_state"][cur_node] = output_value
        self._state["output_state"][cur_node] = output_state

        if output_state.output_type in {"SUCCESS", "LOOP_MESSAGE_TRUE"}:
            # Move to next step
            if cur_node == self._config.end:
                self._state["current_node"] = "END"
            else:
                downstreams = self.get_node_downstreams(cur_node)
                next_downstream = downstreams[0] if downstreams else "END"
                self._state["current_node"] = next_downstream
                logger.debug("Next node is", next_downstream=next_downstream)
        elif output_state.output_type == "LOOP_MESSAGE_FALSE":
            # Output loop message
            result = (cur_node, output_state.loop_message)
            logger.debug("output loop message", cur_node=cur_node, loop_message=result)
        else:
            raise ValueError(f"Unknown output type: {output_state.output_type}")

        return result