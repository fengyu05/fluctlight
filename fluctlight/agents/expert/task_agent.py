import time
from dataclasses import dataclass
from typing import Any, Optional

import structlog
from jinja2 import Environment, meta

from fluctlight.agents.expert.data_model import (
    IntakeHistoryMessage,
    IntakeMessage,
    TaskConfig,
)
from fluctlight.agents.expert.task_node import TaskNode
from fluctlight.agents.expert.task_workflow_config import (
    INTERNAL_UPSTREAM_HISTORY_MESSAGES,
    INTERNAL_UPSTREAM_INPUT_MESSAGE,
    WorkflowRunnerConfig,
    WorkflowRunningState,
    is_internal_upstream,
)
from fluctlight.agents.expert.task_workflow_runner import WorkflowRunner
from fluctlight.agents.message_intent_agent import MessageIntentAgent
from fluctlight.data_model.interface import IMessage
from fluctlight.intent.message_intent import MessageIntent

logger = structlog.getLogger(__name__)

EMPTY_LOOP_MESSAGE = "Cannot proceed with the request, please try again :bow:"


@dataclass
class TaskInvocationContext:
    context: dict[str, Any]
    current_task_index: int = 0


class TaskAgent(MessageIntentAgent):
    def __init__(
        self,
        name: str,
        description: str,
        intent: MessageIntent,
        task_graph: list[TaskConfig],
        context: Optional[dict[str, Any]] = None,
        workflow_runner_config: Optional[WorkflowRunnerConfig] = None,
    ) -> None:
        super().__init__(intent=intent)
        self._name = name
        self._description = description
        self._intent = intent
        self._context = context or {}
        self._tasks = []
        self._workflow_runner_config: Optional[WorkflowRunnerConfig] = None
        if workflow_runner_config:
            self._workflow_runner_config = workflow_runner_config
        else:
            self._tasks = self.build_task_graph(task_graph)
        self._invocation_contexts = {}

    def build_task_graph(self, task_graph: list[TaskConfig]) -> list[TaskNode]:
        """
        1. check graph
        2. build nodes
        3. toposort
        """

        def topological_sort_util(
            v: str,
            adj: dict[str, TaskNode],
            visited: dict[str, bool],
            rec_stack: dict[str, bool],
            stack: list[TaskNode],
        ):
            if rec_stack[v]:
                raise ValueError("Graph contains a cycle.")

            if visited[v]:
                return True
            rec_stack[v] = True

            # Recur for all adjacent vertices
            for upstream_key, _ in adj[v].config.input_schema.items():
                if upstream_key not in visited:
                    continue
                topological_sort_util(upstream_key, adj, visited, rec_stack, stack)

            # Remove the vertex from recursion stack
            rec_stack[v] = False
            # Mark the current node as visited
            visited[v] = True
            # Push current vertex to stack stores the result
            stack.append(adj[v])

        def topological_sort(adj: dict[str, TaskNode]) -> list[TaskNode]:
            # Stack to store the result
            stack: list[TaskNode] = []

            # Mark all the vertices as not visited
            visited: dict[str, bool] = {key: False for key, _ in adj.items()}
            rec_stack = visited.copy()

            # Call the recursive helper function to store
            # Topological Sort starting from all vertices one by one
            for v, _ in adj.items():
                topological_sort_util(v, adj, visited, rec_stack, stack)

            return stack

        self.check_config(task_graph)
        node_graph: dict[str, TaskNode] = {}
        for config in task_graph:
            node_graph[config.task_key] = TaskNode(config)
        sorted_node = topological_sort(node_graph)
        return sorted_node

    def check_instruction(self, config: TaskConfig) -> None:
        """
        Check whether config.instruction is a valid Jinja2 template that can be filled
        with config.input_schema map.

        Raises:
            ValueError: if the template is invalid or any required variable is missing.
        """
        try:
            env = Environment()
            parsed_content = env.parse(config.instruction)
            # Find undeclared variables in the template
            undeclared_variables = meta.find_undeclared_variables(parsed_content)
            # Check if all required variables are in the input_schema
            missing_vars = undeclared_variables - config.input_schema.keys()
            if missing_vars:
                raise ValueError(
                    f"Missing required variables in input schema: {missing_vars}"
                )
        except Exception as e:
            raise ValueError(
                f"Invalid template or error in template processing: {e}"
            ) from e

    def check_config(self, config_list: list[TaskConfig]):
        has_root = False
        for config in config_list:
            if not has_root and config.is_root:
                has_root = True
            self.check_instruction(config)

        if not has_root:
            raise ValueError(f"No root found. {config_list}")

    def retrieve_context(self, message: IMessage) -> TaskInvocationContext:
        if message.message_id not in self._invocation_contexts:
            self._invocation_contexts[message.message_id] = TaskInvocationContext(
                context=self._context.copy()
            )
        return self._invocation_contexts[message.message_id]

    def process_message(
        self, message: IMessage, message_intent: MessageIntent
    ) -> list[str]:
        ic = self.retrieve_context(message)
        assert message.text, "message text is missing"
        return self.run_task_with_ic(message.text, ic=ic)

    def _process_workflow_upstream_input(
        self, workflow_runner: WorkflowRunner, message_text: str
    ):
        upstreams = workflow_runner.get_current_upstreams()
        for upstream in upstreams:
            if not is_internal_upstream(upstream):
                continue
            if upstream == INTERNAL_UPSTREAM_INPUT_MESSAGE:
                workflow_runner.update_running_state(
                    {
                        INTERNAL_UPSTREAM_INPUT_MESSAGE: IntakeMessage(
                            text=message_text,
                        )
                    }
                )
            elif upstream == INTERNAL_UPSTREAM_HISTORY_MESSAGES:
                pass

    def run_task_with_workflow_session(
        self,
        message_text: str,
        ic: TaskInvocationContext,
        workflow_runner_config: WorkflowRunnerConfig,
        workflow_session: WorkflowRunningState,
    ) -> list[str]:
        responses: list[str] = []

        # build or restore worflow runner
        workflow_runner = WorkflowRunner(
            workflow_runner_config,
            workflow_session=workflow_session,
        )

        cur_node = workflow_runner.get_current_node()
        print("=======", cur_node, "=======")
        assistant_response = ""
        while cur_node != "END":
            # handle workflow upstream input
            self._process_workflow_upstream_input(workflow_runner, message_text)

            # workflow process
            task_name, assistant_response = workflow_runner.process_message()

            # if current unhandled node have input message, break to obtain new input message
            # otherwise continue to handle next node
            cur_node = workflow_runner.get_current_node()
            if workflow_runner.current_has_internal_upstreams():
                break

        # update ic context
        responses.append(str(assistant_response))
        workflow_runner.append_history_message(message_text, str(assistant_response))
        ic.context.update({"workflow_session": workflow_runner.get_session_state()})

        return responses

    def run_task_with_ic(
        self, message_text: str, ic: TaskInvocationContext
    ) -> list[str]:
        responses = []

        if self._workflow_runner_config:
            if "workflow_session" in ic.context:
                workflow_session: WorkflowRunningState = ic.context["workflow_session"]
            else:
                workflow_session: WorkflowRunningState = WorkflowRunningState(
                    session_id=str(int(time.time())),
                    current_node=self._workflow_runner_config.config.begin,
                    running_state=ic.context.copy(),
                    output_state={},
                )
                workflow_session["running_state"][
                    INTERNAL_UPSTREAM_HISTORY_MESSAGES
                ] = IntakeHistoryMessage(messages=[])

            responses = self.run_task_with_workflow_session(
                message_text, ic, self._workflow_runner_config, workflow_session
            )
        else:
            ic.context.update({"message": IntakeMessage(text=message_text)})
            for index, task in enumerate(self._tasks):
                if index != ic.current_task_index:
                    continue

                output = task(**ic.context)
                ic.context[task.config.task_key] = output

                responses.append(str(task.config))
                responses.append(str(output))
                if self.stuck_in_loop(task=task, output=output):
                    responses.append(task.config.loop_message or EMPTY_LOOP_MESSAGE)
                    break

                # Task success update ic status
                ic.current_task_index += 1

        logger.info(
            "Task agent process message", name=self._name, all_output=ic.context
        )
        return responses

    def stuck_in_loop(self, task: TaskNode, output: Any) -> bool:
        if task.config.success_criteria is None:
            return False

        return not task.config.success_criteria(output)

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def tasks(self) -> list[TaskNode]:
        return self._tasks
