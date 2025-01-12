import unittest
from unittest.mock import MagicMock
from fluctlight.agents.expert.workflow_runner import WorkflowRunner
from fluctlight.agents.expert.workflow_config import (
    WorkflowConfig,
    WorkflowNodeConfig,
    WorkflowRunningState,
    WorkflowNodeOutput,
    INTERNAL_UPSTREAM_HISTORY_MESSAGES,
)
from fluctlight.agents.expert.data_model import TaskEntity


class SomeEntityA(TaskEntity):
    value: str

class SomeEntityB(TaskEntity):
    value: str


class TestWorkflowRunner(unittest.TestCase):

    def setUp(self) -> None:
        self.config = WorkflowConfig(
            nodes={
                "start": WorkflowNodeConfig(
                    instruction="Start node",
                    output_schema=SomeEntityA,
                    success_criteria=None,
                    loop_message=None,
                    input_schema={}
                ),
                "end": WorkflowNodeConfig(
                    instruction="End node",
                    output_schema=SomeEntityB,
                    success_criteria=None,
                    loop_message=None,
                    input_schema={
                        "start": SomeEntityA
                    }
                )
            },
            begin="start",
            end="end"
        )
        self.workflow_session = WorkflowRunningState(
            running_state={},
            output_state={},
            current_node="start",
        )
        self.runner = WorkflowRunner(self.config, self.workflow_session)

    def test_get_session_state(self) -> None:
        state = self.runner.get_session_state()
        self.assertEqual(state, self.workflow_session)

    def test_get_current_node(self) -> None:
        current_node = self.runner.get_current_node()
        self.assertEqual(current_node, "start")

    def test_get_current_upstreams(self) -> None:
        upstreams = self.runner.get_current_upstreams()
        self.assertEqual(upstreams, [])

    def test_current_has_internal_upstreams(self) -> None:
        has_upstreams = self.runner.current_has_internal_upstreams()
        self.assertFalse(has_upstreams)

    def test_get_node_downstreams(self) -> None:
        downstreams = self.runner.get_node_downstreams("start")
        self.assertEqual(downstreams, ["end"])

    def test_update_running_state(self) -> None:
        context = {"key": "value"}
        self.runner.update_running_state(context)
        self.assertEqual(self.runner.get_session_state()["running_state"]["key"], "value")

    def test_append_history_message(self) -> None:
        self.runner.append_history_message("user message", "assistant message")
        history = self.runner.get_session_state()["running_state"][INTERNAL_UPSTREAM_HISTORY_MESSAGES]
        self.assertEqual(history.messages, ["user message", "assistant message"])

    def test_process_message(self) -> None:
        result = self.runner.process_message()
        self.assertEqual(result, ("start", "output_value"))
        self.assertEqual(self.runner.get_current_node(), "end")

if __name__ == '__main__':
    unittest.main()