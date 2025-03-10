# pylint: disable=protected-access
import unittest
from unittest.mock import patch, MagicMock
from fluctlight.agents.expert.task_workflow_config import (
    WorkflowNodeConfig,
    is_internal_upstream,
)
from fluctlight.agents.expert.data_model import TaskEntity


class SomeEntityA(TaskEntity):
    value: str


class SomeEntityB(TaskEntity):
    value: str


class TestWorkflowConfig(unittest.TestCase):
    def setUp(self):
        self.config_dict = {
            "instruction": "Test instruction",
            "input_schema": {
                "input1": "tests.agents.expert.test_task_workflow_config.SomeEntityA",
                "input2": "str",
            },
            "output_schema": "tests.agents.expert.test_task_workflow_config.SomeEntityB",
            "validation_config": {
                "success_criteria": "Test criteria",
            },
        }

    @patch(
        "fluctlight.agents.expert.task_workflow_config.WorkflowNodeConfig._import_type"
    )
    def test_load_input_schema(self, mock_import_type) -> None:
        mock_import_type.side_effect = lambda module_name, class_name: MagicMock()
        input_schema = WorkflowNodeConfig._load_input_schema(
            self.config_dict["input_schema"]
        )
        self.assertEqual(len(input_schema), 2)
        self.assertIn("input1", input_schema)
        self.assertIn("input2", input_schema)

    @patch(
        "fluctlight.agents.expert.task_workflow_config.WorkflowNodeConfig._import_type"
    )
    def test_load_type(self, mock_import_type):
        mock_import_type.side_effect = lambda module_name, class_name: MagicMock()
        type_instance = WorkflowNodeConfig._load_type("IntakeMessage")
        self.assertIsNotNone(type_instance)

    def test_load_from_config(self) -> None:
        config = WorkflowNodeConfig.load_from_config(self.config_dict)
        self.assertEqual(config.instruction, "Test instruction")
        self.assertEqual(config.validation_config.success_criteria, "Test criteria")
        self.assertEqual(config.validation_config.failed_message, None)
        self.assertEqual(config.validation_config.passed_message, None)
        self.assertIsNotNone(config.input_schema)
        self.assertIsNotNone(config.output_schema)

    def test_is_internal_upstream(self) -> None:
        self.assertTrue(is_internal_upstream("__INPUT_MESSAGE"))
        self.assertTrue(is_internal_upstream("__HISTORY_MESSAGES"))
        self.assertFalse(is_internal_upstream("other_message"))


if __name__ == "__main__":
    unittest.main()
