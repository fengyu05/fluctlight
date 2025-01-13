import unittest
from unittest.mock import patch, MagicMock
from fluctlight.agents.expert.task_workflow import (
    create_workflow_node,
    create_workflow_loop_output_node,
    workflow_node_router,
    create_conditional_edge_chain,
    build_workflow_graph,
    WorkflowRunningState,
    WorkflowNodeConfig,
    ConditionalOutput,
)
from fluctlight.agents.expert.task_workflow_config import WorkflowConfig
from fluctlight.agents.expert.data_model import TaskEntity


class SomeEntity(TaskEntity):
    value: str


class AnotherEntity(TaskEntity):
    value: str


class TestTaskWorkflow(unittest.TestCase):
    def test_create_workflow_node(self) -> None:
        config = WorkflowNodeConfig(
            instruction="Test instruction",
            output_schema=SomeEntity,
            success_criteria=None,
            loop_message=None,
            input_schema={},
        )
        state = WorkflowRunningState(
            running_state={},
            output_state={},
            current_node="",
        )
        node_fn = create_workflow_node("test_node", config)
        new_state = node_fn(state)
        self.assertIn("test_node", new_state["running_state"])

    def test_create_workflow_loop_output_node(self) -> None:
        config = WorkflowNodeConfig(
            instruction="Test instruction",
            output_schema=str,
            success_criteria=None,
            loop_message=None,
            input_schema={},
        )
        state = WorkflowRunningState(
            running_state={},
            output_state={},
            current_node="",
        )
        loop_fn = create_workflow_loop_output_node("test_node", config, True)
        new_state = loop_fn(state)
        self.assertEqual(
            new_state["output_state"]["test_node"].output_type, "LOOP_MESSAGE_TRUE"
        )

    def test_workflow_node_router(self) -> None:
        state = WorkflowRunningState(
            running_state={},
            output_state={},
            current_node="test_node",
        )
        result = workflow_node_router(state)
        self.assertEqual(result, "test_node")

    @patch("fluctlight.agents.expert.task_workflow.chat_completion")
    def test_create_conditional_edge_chain(self, mock_chat_completion) -> None:
        mock_response = MagicMock()
        mock_response.choices[0].message.parsed = ConditionalOutput(
            is_match_success_criteria=True
        )
        mock_chat_completion.return_value = mock_response

        config = WorkflowNodeConfig(
            instruction="Test instruction",
            output_schema=SomeEntity,
            success_criteria="Test criteria",
            loop_message=None,
            input_schema={},
        )
        state = WorkflowRunningState(
            running_state={},
            output_state={},
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
                    success_criteria=None,
                    loop_message=None,
                    input_schema={},
                ),
                "node2": WorkflowNodeConfig(
                    instruction="Test instruction",
                    output_schema=AnotherEntity,
                    success_criteria=None,
                    loop_message=None,
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
