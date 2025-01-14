import unittest
from fluctlight.agents.expert.task_workflow_runner import WorkflowRunner
from fluctlight.agents.expert.task_workflow_config import (
    WorkflowConfig,
    WorkflowNodeConfig,
    WorkflowInvocationState,
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
                    input_schema={},
                ),
                "end": WorkflowNodeConfig(
                    instruction="End node",
                    output_schema=SomeEntityB,
                    success_criteria=None,
                    loop_message=None,
                    input_schema={"start": SomeEntityA},
                ),
            },
            begin="start",
            end="end",
        )
        self.ic = WorkflowInvocationState(
            current_node="start",
        )
        self.runner = WorkflowRunner(self.config, self.ic)

    def test_get_current_node(self) -> None:
        current_node = self.runner.get_current_node()
        self.assertEqual(current_node, "start")

    def test_get_current_upstreams(self) -> None:
        upstreams = self.runner.get_current_upstreams()
        self.assertEqual(upstreams, [])

    def test_current_has_internal_upstreams(self) -> None:
        has_upstreams = self.runner.has_input_message_in_current_upstreams()
        self.assertFalse(has_upstreams)

    def test_get_node_downstreams(self) -> None:
        downstreams = self.runner.get_node_downstreams("start")
        self.assertEqual(downstreams, ["end"])

    def test_update_running_state(self) -> None:
        context = {"key": "value"}
        self.runner.update_running_state(context)
        self.assertEqual(self.runner.ic.running_state["key"], "value")

    def test_append_history_message(self) -> None:
        self.runner.append_history_message("user message", "assistant message")
        self.assertEqual(
            self.runner.ic.running_state[INTERNAL_UPSTREAM_HISTORY_MESSAGES].messages,
            ["user message", "assistant message"],
        )

    def test_process_message(self) -> None:
        result = self.runner.run()
        self.assertEqual(
            result,
            ("start", SomeEntityA(value="This is a sample response for SomeEntityA.")),
        )
        self.assertEqual(self.runner.get_current_node(), "end")


if __name__ == "__main__":
    unittest.main()
