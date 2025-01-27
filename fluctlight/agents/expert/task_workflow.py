from typing import Callable, Hashable, cast

from jinja2 import Template

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from pydantic import BaseModel
from fluctlight.agents.expert.data_model import TaskEntity
from fluctlight.agents.expert.task_workflow_config import (
    WorkflowConfig,
    WorkflowNodeConfig,
    WorkflowNodeOutput,
    WorkflowInvocationState,
)
from fluctlight.open.chat import structure_chat_completion


_DEFAULT_PASSED_MSG = "You request has been processed successfully."
_DEFAULT_FAILED_MSG = "You request is invalid, please try again."


def create_task_node(
    name: str,
    config: WorkflowNodeConfig,
) -> Callable[[WorkflowInvocationState], WorkflowInvocationState]:
    """
    Create a workflow node function.

    The node function takes a workflow state as argument, and returns a new workflow state.
    The node function renders a Jinja template instruction string with the current workflow state,
    and then uses an LLM to generate a structured output.
    The structured output is then used to update the new workflow state.

    Args:
        name: The name of the node.
        config: The configuration of the node.

    Returns:
        A node function.
    """

    def node_fn(state: WorkflowInvocationState) -> WorkflowInvocationState:
        running_state = state.running_state

        # LLM instruction
        template = Template(config.instruction)
        text = template.render(running_state)

        messages = [
            {
                "role": "system",
                "content": text,
            },
        ]

        # LLM structured output
        response = structure_chat_completion(config.output_schema, messages)
        structured_content = response.choices[0].message.parsed

        new_state = state.model_copy()

        # Check output state
        if structured_content and isinstance(structured_content, config.output_schema):
            if isinstance(structured_content, TaskEntity) or isinstance(
                structured_content, str
            ):
                new_state.running_state[name] = structured_content
                new_state.output[name] = WorkflowNodeOutput(
                    node=name,
                    status="SUCCESS",
                    message=None,
                )
            else:
                raise ValueError(f"Output type not match, {structured_content}")

        return new_state

    return node_fn


def create_task_validation_node(
    name: str,
    config: WorkflowNodeConfig,
    success: bool,
) -> Callable[[WorkflowInvocationState], WorkflowInvocationState]:
    """Create a workflow node function for loop output valiation nodes."""

    def node_fn(state: WorkflowInvocationState) -> WorkflowInvocationState:
        passed_template = Template(
            config.validation_config.passed_message or _DEFAULT_PASSED_MSG
        )
        failed_template = Template(
            config.validation_config.failed_message or _DEFAULT_FAILED_MSG
        )

        new_state = state.model_copy()
        if success:
            new_state.output[name] = WorkflowNodeOutput(
                node=name,
                status="LOOP_MESSAGE_CHECK_PASSED",
                message=passed_template.render(state.running_state),
            )
        else:
            new_state.output[name] = WorkflowNodeOutput(
                node=name,
                status="LOOP_MESSAGE_CHECK_FAILED",
                message=failed_template.render(state.running_state),
            )
        return new_state

    return node_fn


def workflow_node_router(state: WorkflowInvocationState) -> str:
    cur_node = state.current_node
    if cur_node == "":
        raise ValueError(f"Workflow running state no node found. {state}")
    return cur_node


class ConditionalOutput(BaseModel):
    is_match_success_criteria: bool


def create_conditional_edge_chain(
    name: str,
    node_config: WorkflowNodeConfig,
) -> Callable[[WorkflowInvocationState], str]:
    success_criteria: str = node_config.validation_config.success_criteria or ""

    def node_conditional_edge(state: WorkflowInvocationState) -> str:
        context = state.running_state

        template = Template(success_criteria)
        text = template.render(context)

        messages = [
            {
                "role": "system",
                "content": text,
            },
        ]

        result = "NO"

        response = structure_chat_completion(ConditionalOutput, messages)
        structured_content = response.choices[0].message.parsed
        if isinstance(structured_content, ConditionalOutput):
            if cast(ConditionalOutput, structured_content).is_match_success_criteria:
                result = "YES"

        return result

    return node_conditional_edge


def build_workflow_graph(config: WorkflowConfig) -> CompiledStateGraph:
    """
    Builds a workflow graph based on the provided `TaskWorkflowConfig`.

    Example: START -> router -> nodes... -> END

    Creates a state graph with nodes and edges based on the configuration. The graph
    begins with a node router and constructs conditional edges between nodes based on
    their success criteria. If a node has success criteria, loop output nodes are
    created to handle both success and failure cases, directing the flow to the end
    of the workflow.

    Args:
        config: The configuration for the task workflow.

    Returns:
        A compiled state graph representing the constructed workflow.
    """
    workflow = StateGraph(WorkflowInvocationState)
    workflow_node_route_table: dict[Hashable, str] = {}

    # Build and add nodes
    for k, v in config.nodes.items():
        workflow_node_route_table[k] = k
        workflow.add_node(k, create_task_node(k, v))

    # Add START -> node router
    workflow.add_conditional_edges(
        START, workflow_node_router, workflow_node_route_table
    )

    # Add edges
    for k, v in config.nodes.items():
        if v.validation_config:
            # Add loop output nodes
            workflow.add_node(
                k + "_LOOP_OUTPUT_TRUE", create_task_validation_node(k, v, True)
            )
            workflow.add_node(
                k + "_LOOP_OUTPUT_FALSE", create_task_validation_node(k, v, False)
            )
            workflow.add_edge(k + "_LOOP_OUTPUT_TRUE", END)
            workflow.add_edge(k + "_LOOP_OUTPUT_FALSE", END)
            workflow.add_conditional_edges(
                k,
                create_conditional_edge_chain(k, v),
                {"YES": k + "_LOOP_OUTPUT_TRUE", "NO": k + "_LOOP_OUTPUT_FALSE"},
            )
        else:
            workflow.add_edge(k, END)

    return workflow.compile()
