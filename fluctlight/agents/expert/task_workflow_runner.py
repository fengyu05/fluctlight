from typing import Any, Dict, List, Set, Tuple

from fluctlight.agents.expert.data_model import IntakeHistoryMessage
from fluctlight.agents.expert.task_workflow_config import (
    INTERNAL_UPSTREAM_HISTORY_MESSAGES,
    WorkflowNodeOutput,
    WorkflowRunnerConfig,
    WorkflowRunningState,
    has_internal_upstreams,
)
from fluctlight.logger import get_logger

logger = get_logger(__name__)

class WorkflowRunner:
    def __init__(
        self,
        config: WorkflowRunnerConfig,
        workflow_session: WorkflowRunningState,
    ):
        self._config = config.config
        self._graph = config.state_graph
        self._state = workflow_session.copy()

    def get_session_state(self) -> WorkflowRunningState:
        return self._state

    def get_current_node(self) -> str:
        return self._state["current_node"]

    def get_current_upstreams(self) -> List[str]:
        cur_node = self.get_current_node()
        if cur_node == "END":
            return []

        if cur_node not in self._config.nodes:
            raise ValueError(f"{cur_node} not exist. {self._config}")

        input_schema = self._config.nodes[cur_node].input_schema
        return [k for k, _ in input_schema.items()]

    def current_has_internal_upstreams(self) -> bool:
        return has_internal_upstreams(self.get_current_upstreams())

    def get_node_downstreams(self, node: str) -> List[str]:
        downstreams: Set[str] = set()
        for k, v in self._config.nodes.items():
            for upstream, _ in v.input_schema.items():
                if upstream == node:
                    downstreams.add(k)
        return list(downstreams)

    def update_running_state(self, context: Dict[str, Any]):
        self._state["running_state"].update(context)

    def append_history_message(self, user: str, assistant: str):
        if INTERNAL_UPSTREAM_HISTORY_MESSAGES in self._state["running_state"]:
            history: IntakeHistoryMessage = self._state["running_state"][
                INTERNAL_UPSTREAM_HISTORY_MESSAGES
            ]
        else:
            history = IntakeHistoryMessage(messages=[])
            self._state["running_state"][INTERNAL_UPSTREAM_HISTORY_MESSAGES] = history
        history.messages.append(user)
        history.messages.append(assistant)

    def process_message(self, *args: Any, **kwargs: Any) -> Tuple[str, Any]:
        cur_node = self.get_current_node()
        if cur_node == "END":
            self._state["current_node"] = self._config.begin
            cur_node = self._config.begin

        events = self._graph.stream(self._state, stream_mode="values")
        for event in events:
            last_state = event

        output_value = last_state["running_state"][cur_node]
        output_state: WorkflowNodeOutput = last_state["output_state"][cur_node]
        result = (cur_node, output_value)
        logger.info("CUR_NODE: " + cur_node + " output_value: " + str(output_value) + " result: " + str(result))

        # update state
        self._state["running_state"][cur_node] = output_value
        self._state["output_state"][cur_node] = output_state

        if (
            output_state.output_type == "SUCCESS"
            or output_state.output_type == "LOOP_MESSAGE_TRUE"
        ):
            # move to next step
            logger.info("Move to next step, cur: " + cur_node)
            if cur_node == self._config.end:
                self._state["current_node"] = "END"
                logger.info("Next is END")
            else:
                downstreams = self.get_node_downstreams(cur_node)
                next_downstream = downstreams[0]
                self._state["current_node"] = next_downstream
                logger.info("Next is " + next_downstream)
        elif output_state.output_type == "LOOP_MESSAGE_FALSE":
            # output loop message
            # result = (cur_node, output_state.loop_message)
            logger.info("CUR_NODE: " + cur_node + " loop_message: " + str(result))
        else:
            raise ValueError(f"Unknow output type. {output_state}")

        return result
