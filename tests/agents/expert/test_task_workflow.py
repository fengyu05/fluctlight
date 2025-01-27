import unittest
from unittest.mock import patch, MagicMock
from fluctlight.agents.expert.task_workflow import (
    create_task_node,
    create_task_validation_node,
    workflow_node_router,
    create_conditional_edge_chain,
    build_workflow_graph,
    WorkflowInvocationState,
    WorkflowNodeConfig,
    ConditionalOutput,
)
from fluctlight.agents.expert.task_workflow_config import WorkflowConfig
from fluctlight.agents.expert.data_model import TaskEntity, TaskNodeValidation


class SomeEntity(TaskEntity):
    value: str


class AnotherEntity(TaskEntity):
    value: str


class TestTaskWorkflow(unittest.TestCase):
    @patch("fluctlight.agents.expert.task_workflow.structure_chat_completion")
    def test_create_workflow_node(self, mock_chat_completion: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.choices[0].message.parsed = SomeEntity(value="Test")
        mock_chat_completion.return_value = mock_response

        config = WorkflowNodeConfig(
            instruction="Test instruction",
            output_schema=SomeEntity,
            input_schema={},
        )
        state = WorkflowInvocationState(
            running_state={},
            output={},
            current_node="",
        )
        node_fn = create_task_node("test_node", config)
        new_state = node_fn(state)
        self.assertIn("test_node", new_state.running_state)

    def test_create_workflow_loop_output_node(self) -> None:
        config = WorkflowNodeConfig(
            instruction="Test instruction",
            output_schema=str,
            input_schema={},
            validation_config=TaskNodeValidation(success_criteria="Test criteria"),
        )
        state = WorkflowInvocationState(
            running_state={},
            output={},
            current_node="",
        )
        loop_fn = create_task_validation_node("test_node", config, True)
        new_state = loop_fn(state)
        self.assertEqual(
            new_state.output["test_node"].status, "LOOP_MESSAGE_CHECK_PASSED"
        )

    def test_workflow_node_router(self) -> None:
        state = WorkflowInvocationState(
            running_state={},
            output={},
            current_node="test_node",
        )
        result = workflow_node_router(state)
        self.assertEqual(result, "test_node")

    @patch("fluctlight.agents.expert.task_workflow.structure_chat_completion")
    def test_create_conditional_edge_chain(
        self, mock_chat_completion: MagicMock
    ) -> None:
        mock_response = MagicMock()
        mock_response.choices[0].message.parsed = ConditionalOutput(
            is_match_success_criteria=True
        )
        mock_chat_completion.return_value = mock_response

        config = WorkflowNodeConfig(
            instruction="Test instruction",
            output_schema=SomeEntity,
            input_schema={},
            validation_config=TaskNodeValidation(success_criteria="Test criteria"),
        )
        state = WorkflowInvocationState(
            running_state={},
            output={},
            current_node="",
        )
        edge_fn = create_conditional_edge_chain("test_node", config)
        result = edge_fn(state)
        self.assertEqual(result, "YES")

    def test_build_workflow_graph(self) -> None:
        config = WorkflowConfig(
            nodes={
                "node1": WorkflowNodeConfig(
                    instruction="Test instruction",
                    output_schema=SomeEntity,
                    validation_config=None,
                    input_schema={},
                ),
                "node2": WorkflowNodeConfig(
                    instruction="Test instruction",
                    output_schema=AnotherEntity,
                    validation_config=None,
                    input_schema={"node1": SomeEntity},
                ),
            },
            begin="node1",
            end="node2",
        )
        graph = build_workflow_graph(config)
        self.assertIsNotNone(graph)


if __name__ == "__main__":
    unittest.main()
