import unittest
from unittest.mock import MagicMock, patch

from fluctlight.agents.expert.data_model import IntakeMessage, TaskConfig, TaskEntity
from fluctlight.agents.expert.task_agent import TaskAgent
from fluctlight.agents.expert.task_node import TaskNode
from fluctlight.intent.message_intent import MessageIntent
from tests.data.imessages import MESSAGE_HELLO_WORLD


class Te1(TaskEntity):
    pass


class TestTaskAgent(unittest.TestCase):
    def setUp(self):
        self.name = "test_agent"
        self.description = "A test agent"
        self.intent = MessageIntent(key="test_task")
        self.task_graph = [
            TaskConfig(
                task_key="poem_translation",
                instruction="Take user input, if input is a peom name, output the information of the poem translate into the user request language. User input: {message}",
                input_schema={"message": IntakeMessage},
                output_schema=Te1,
            ),
            TaskConfig(
                task_key="peom_grader",
                instruction="Take a poem translation, grade the target translation 3 score of 1-5 integer of 3 crieteria. Rhetroic, Phonetics, Emotion. \n\n Peom: {poem_translation}",
                input_schema={"poem_translation": Te1},
                output_schema=str,
            ),
        ]
        self.message = MESSAGE_HELLO_WORLD
        self.intake_message = IntakeMessage(text=self.message.text)

    def test_process_message(self):
        task1 = TaskNode(self.task_graph[0])
        task2 = TaskNode(self.task_graph[1])

        # Mock the __call__ method of the tasks
        task1.process = MagicMock(return_value="output_task1")
        task2.process = MagicMock(return_value="output_task2")

        tasks = [task1, task2]
        with patch.object(TaskAgent, "build_task_graph", return_value=tasks):
            agent = TaskAgent(
                name=self.name,
                description=self.description,
                intent=self.intent,
                task_graph=self.task_graph,
            )

        agent.process_message(message=self.message, message_intent=self.intent)
        task1.process.assert_called_once_with(message=self.intake_message)
        task2.process.assert_called_once_with(
            message=self.intake_message, poem_translation="output_task1"
        )

    def test_process_message_stuck_in_loop(self):
        stuck_task_config = TaskConfig(
            task_key="stuck_test",
            instruction="This task will stuck",
            input_schema={"str": IntakeMessage},
            output_schema=str,
            success_criteria=lambda x: x == "pass",
        )
        stuck_task = TaskNode(stuck_task_config)

        task1 = TaskNode(self.task_graph[0])
        task2 = TaskNode(self.task_graph[1])

        # Mock the __call__ method of the tasks
        task1.process = MagicMock(return_value="output_task1")
        task2.process = MagicMock(return_value="output_task2")
        stuck_task.process = MagicMock(return_value="not pass")

        tasks = [task1, stuck_task, task2]
        with patch.object(TaskAgent, "build_task_graph", return_value=tasks):
            agent = TaskAgent(
                name=self.name,
                description=self.description,
                intent=self.intent,
                task_graph=self.task_graph,
            )

        agent.process_message(message=self.message, message_intent=self.intent)

        # First time, task1 called, stuck_task called and break
        task1.process.assert_called_once_with(message=self.intake_message)
        stuck_task.process.assert_called_once_with(
            message=self.intake_message, poem_translation="output_task1"
        )
        task2.process.assert_not_called()  # This should not be called

        # Second time, resume from stuck_task, then task2 called
        # Reconfig process mock
        task1.process = MagicMock(return_value="output_task1")
        task2.process = MagicMock(return_value="output_task2")
        stuck_task.process = MagicMock(return_value="pass")  # Change to pass

        agent.process_message(message=self.message, message_intent=self.intent)
        task1.process.assert_not_called()
        stuck_task.process.assert_called_once_with(
            message=self.intake_message,
            poem_translation="output_task1",
            stuck_test="not pass",
        )
        task2.process.assert_called_once_with(
            message=self.intake_message,
            poem_translation="output_task1",
            stuck_test="pass",
        )

    def test_process_message_with_context(self):
        task1 = TaskNode(self.task_graph[0])
        task2 = TaskNode(self.task_graph[1])

        # Mock the __call__ method of the tasks
        task1.process = MagicMock(return_value="output_task1")
        task2.process = MagicMock(return_value="output_task2")

        tasks = [task1, task2]
        with patch.object(TaskAgent, "build_task_graph", return_value=tasks):
            agent = TaskAgent(
                name=self.name,
                description=self.description,
                intent=self.intent,
                task_graph=self.task_graph,
                context={
                    "a": "a",
                    "b": 1,
                },
            )

        agent.process_message(message=self.message, message_intent=self.intent)
        task1.process.assert_called_once_with(
            message=self.intake_message,
            a="a",
            b=1,
        )
        task2.process.assert_called_once_with(
            message=self.intake_message,
            poem_translation="output_task1",
            a="a",
            b=1,
        )
