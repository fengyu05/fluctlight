import unittest
from unittest.mock import patch, MagicMock
from fluctlight.agents.expert.task_workflow_runner import WorkflowRunner
from fluctlight.agents.expert.task_workflow_config import (
    WorkflowConfig,
    WorkflowNodeConfig,
    WorkflowInvocationState,
    INTERNAL_UPSTREAM_HISTORY_MESSAGES,
    WorkflowNodeOutput,
)
from fluctlight.agents.expert.task_workflow import (
    ConditionalOutput,
)
from fluctlight.agents.expert.data_model import (
    TaskEntity,
    TaskNodeValidation,
)


class SomeEntityA(TaskEntity):
    value: str


class SomeEntityB(TaskEntity):
    value: str


class TestWorkflowRunner(unittest.TestCase):
    def setUp(self) -> None:
        self.config = WorkflowConfig(
            nodes={
                "task_a": WorkflowNodeConfig(
                    instruction="Start node",
                    output_schema=SomeEntityA,
                    input_schema={},
                ),
                "task_b": WorkflowNodeConfig(
                    instruction="End node",
                    output_schema=SomeEntityB,
                    input_schema={"task_a": SomeEntityA},
                    validation_config=TaskNodeValidation(
                        success_criteria="Test criteria",
                        passed_message="Passed message",
                        failed_message="Failed message",
                    ),
                ),
            },
            begin="task_a",
            end="task_b",
        )
        self.ic = WorkflowInvocationState(
            current_node="task_a",
        )
        self.runner = WorkflowRunner(self.config, self.ic)

    def test_get_current_node(self) -> None:
        current_node = self.runner.get_current_node()
        self.assertEqual(current_node, "task_a")

    def test_get_current_upstreams(self) -> None:
        upstreams = self.runner.get_current_upstreams()
        self.assertEqual(upstreams, [])

    def test_current_has_internal_upstreams(self) -> None:
        has_upstreams = self.runner.has_input_message_in_current_upstreams()
        self.assertFalse(has_upstreams)

    def test_get_node_downstreams(self) -> None:
        downstreams = self.runner.get_node_downstreams("task_a")
        self.assertEqual(downstreams, ["task_b"])

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

    @patch("fluctlight.agents.expert.task_workflow.structure_chat_completion")
    def test_process_message_no_validation(
        self, mock_chat_completion: MagicMock
    ) -> None:
        mock_response = MagicMock()
        mock_response.choices[0].message.parsed = SomeEntityA(value="SomeEntityA value")
        mock_chat_completion.return_value = mock_response

        result = self.runner.run(
            message_text="This is a sample response for SomeEntityA."
        )
        self.assertEqual(
            result,
            WorkflowNodeOutput(
                node="task_a",
                status="SUCCESS",
                message=None,
            ),
        )
        self.assertEqual(self.runner.get_current_node(), "task_b")

    @patch("fluctlight.agents.expert.task_workflow.structure_chat_completion")
    def test_process_message_with_validation(
        self, mock_chat_completion: MagicMock
    ) -> None:
        mock_response_start = MagicMock()
        mock_response_start.choices[0].message.parsed = SomeEntityA(
            value="SomeEntityA value"
        )
        mock_response_end = MagicMock()
        mock_response_end.choices[0].message.parsed = SomeEntityB(
            value="SomeEntityB value"
        )

        mock_response_end_validation = MagicMock()
        mock_response_end_validation.choices[0].message.parsed = ConditionalOutput(
            is_match_success_criteria=True
        )

        mock_chat_completion.side_effect = [
            mock_response_start,
            mock_response_end,
            mock_response_end_validation,
        ]

        result = self.runner.run(
            message_text="This is a sample response for SomeEntityA."
        )
        self.assertEqual(
            result,
            WorkflowNodeOutput(
                node="task_a",
                status="SUCCESS",
                message=None,
            ),
        )
        self.assertEqual(self.runner.get_current_node(), "task_b")

        result = self.runner.run(
            message_text="This is a sample response for SomeEntityB."
        )
        self.assertEqual(
            result,
            WorkflowNodeOutput(
                node="task_b",
                status="LOOP_MESSAGE_CHECK_PASSED",
                message="Passed message",
            ),
        )
        self.assertEqual(self.runner.get_current_node(), "END")

    @patch("fluctlight.agents.expert.task_workflow.structure_chat_completion")
    def test_process_message_with_validation_fail(
        self, mock_chat_completion: MagicMock
    ) -> None:
        mock_response_start = MagicMock()
        mock_response_start.choices[0].message.parsed = SomeEntityA(
            value="SomeEntityA value"
        )
        mock_response_end = MagicMock()
        mock_response_end.choices[0].message.parsed = SomeEntityB(
            value="SomeEntityB value"
        )

        mock_response_end_validation_failed = MagicMock()
        mock_response_end_validation_failed.choices[
            0
        ].message.parsed = ConditionalOutput(is_match_success_criteria=False)

        mock_chat_completion.side_effect = [
            mock_response_start,
            mock_response_end,
            mock_response_end_validation_failed,
        ]

        result = self.runner.run(
            message_text="This is a sample response for SomeEntityA."
        )
        self.assertEqual(
            result,
            WorkflowNodeOutput(
                node="task_a",
                status="SUCCESS",
                message=None,
            ),
        )
        self.assertEqual(self.runner.get_current_node(), "task_b")

        result = self.runner.run(
            message_text="This is a sample response for SomeEntityB."
        )
        self.assertEqual(
            result,
            WorkflowNodeOutput(
                node="task_b",
                status="LOOP_MESSAGE_CHECK_FAILED",
                message="Failed message",
            ),
        )
        self.assertEqual(self.runner.get_current_node(), "task_b")


if __name__ == "__main__":
    unittest.main()
