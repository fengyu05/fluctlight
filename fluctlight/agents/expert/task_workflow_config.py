from typing import Any, Literal, Type

from pydantic import BaseModel
from fluctlight.logger import get_logger
from fluctlight.agents.expert.data_model import TaskEntity, TaskNodeValidation

logger = get_logger(__name__)

WorkflowSchemaType = TaskEntity | str
ContextValue = (
    None
    | str
    | float
    | WorkflowSchemaType
    | list[WorkflowSchemaType]
    | dict[str, WorkflowSchemaType]
)

INTERNAL_UPSTREAM_INPUT_MESSAGE = "__INPUT_MESSAGE"
INTERNAL_UPSTREAM_HISTORY_MESSAGES = "__HISTORY_MESSAGES"

# Global type map with full paths
type_aliases: dict[str, str] = {
    "IntakeMessage": "fluctlight.agents.expert.data_model.IntakeMessage",
    "IntakeHistoryMessage": "fluctlight.agents.expert.data_model.IntakeHistoryMessage",
    "ProductMatch": "fluctlight.agents.expert.shopping_assist.ProductMatch",
    "Order": "fluctlight.agents.expert.shopping_assist.Order",
}


class WorkflowNodeConfig(BaseModel):
    instruction: str
    input_schema: dict[str, Type[WorkflowSchemaType]]
    output_schema: Type[WorkflowSchemaType]
    validation_config: TaskNodeValidation | None = None

    @classmethod
    def _load_input_schema(
        cls, input_schema: dict[str, str]
    ) -> dict[str, Type[WorkflowSchemaType]]:
        """Load input schema types from string representation."""
        return {k: cls._load_type(v) for k, v in input_schema.items()}

    @classmethod
    def _load_type(cls, type_str: str) -> Type[WorkflowSchemaType]:
        """Load type via reflection. Check if it's an alias first."""
        if type_str == "str":
            return str

        full_path = type_aliases.get(type_str, type_str)
        module_name, class_name = full_path.rsplit(".", 1)
        return cls._import_type(module_name, class_name)

    @staticmethod
    def _import_type(module_name: str, class_name: str) -> Type[WorkflowSchemaType]:
        """Dynamically import a type from a module."""
        module = __import__(module_name, fromlist=[class_name])
        return getattr(module, class_name)

    @classmethod
    def load_from_config(cls, config: dict[str, Any]) -> "WorkflowNodeConfig":
        """Load WorkflowNodeConfig from a dictionary configuration."""

        validation_config = config.get("validation_config", {})
        return WorkflowNodeConfig(
            instruction=config["instruction"],
            input_schema=cls._load_input_schema(config["input_schema"]),
            output_schema=cls._load_type(config["output_schema"]),
            validation_config=TaskNodeValidation(**validation_config),
        )


class WorkflowConfig(BaseModel):
    nodes: dict[str, WorkflowNodeConfig]
    begin: str
    end: str


class WorkflowNodeOutput(BaseModel):
    node: str
    status: Literal["SUCCESS", "LOOP_MESSAGE_CHECK_PASSED", "LOOP_MESSAGE_CHECK_FAILED"]
    message: str | None = None


class WorkflowInvocationState(BaseModel):
    current_node: str
    running_state: dict[str, Any] = {}
    output: dict[str, WorkflowNodeOutput] = {}


def is_internal_upstream(upstream: str) -> bool:
    """Check if the given upstream is an internal upstream."""
    return upstream in [
        INTERNAL_UPSTREAM_INPUT_MESSAGE,
        INTERNAL_UPSTREAM_HISTORY_MESSAGES,
    ]
