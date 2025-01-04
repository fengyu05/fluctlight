from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Type, Union

from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from fluctlight.agents.expert.data_model import TaskEntity
from fluctlight.logger import get_logger

WorkflowSchemaType = Union[TaskEntity, str]


INTERNAL_UPSTREAM_INPUT_MESSAGE = "__INPUT_MESSAGE"
INTERNAL_UPSTREAM_HISTORY_MESSAGES = "__HISTORY_MESSAGES"

logger = get_logger(__name__)

class WorkflowNodeLoopMessage(BaseModel):
    mode: Literal["text"]
    message: str


class WorkflowNodeLLMResponse(BaseModel):
    instruction: str


class WorkflowNodeConfig(BaseModel):
    instruction: str
    input_schema: Dict[str, Type[WorkflowSchemaType]]
    output_schema: Type[WorkflowSchemaType]
    loop_message: Optional[WorkflowNodeLoopMessage] = None
    success_criteria: Optional[str] = None  # TODO: move into WorkflowNodeLoopMessage
    llm_response: Optional[WorkflowNodeLLMResponse] = None

    @classmethod
    def _load_input_schema(
        cls, input_schema: Dict[str, str]
    ) -> Dict[str, Type[WorkflowSchemaType]]:
        result: Dict[str, Type[WorkflowSchemaType]] = {}
        for k, v in input_schema.items():
            result[k] = cls._load_type(v)
        return result

    @classmethod
    def _load_type(cls, type_str: str) -> Type[WorkflowSchemaType]:
        t: Type[WorkflowSchemaType] = str
        if type_str == "IntakeMessage":
            from fluctlight.agents.expert.data_model import IntakeMessage

            t = IntakeMessage
        elif type_str == "IntakeHistoryMessage":
            from fluctlight.agents.expert.data_model import IntakeHistoryMessage

            t = IntakeHistoryMessage
        elif type_str == "ProductMatch":
            from fluctlight.agents.expert.shopping_assist import ProductMatch

            t = ProductMatch
        elif type_str == "Order":
            from fluctlight.agents.expert.shopping_assist import Order

            t = Order
        return t

    @classmethod
    def load_from_config(cls, config: Dict[str, Any]) -> "WorkflowNodeConfig":
        return WorkflowNodeConfig(
            instruction=config["instruction"],
            input_schema=cls._load_input_schema(config["input_schema"]),
            output_schema=cls._load_type(config["output_schema"]),
            loop_message=None,  # TODO
            success_criteria=config["success_criteria"]
            if "success_criteria" in config
            else None,
            llm_response=None,  # TODO
        )

class TaskWorkflowConfig(BaseModel):
    nodes: Dict[str, WorkflowNodeConfig]
    begin: str
    end: str
    context: Optional[Dict[str, WorkflowSchemaType]] = None

    @classmethod
    def _load_nodes(cls, config: dict[str, Any]) -> Dict[str, WorkflowNodeConfig]:
        cfg = dict()
        for k, v in config.items():
            cfg[k] = WorkflowNodeConfig.load_from_config(v)
        return cfg

    @classmethod
    def load_from_config(cls, config: dict[str, Any]) -> "TaskWorkflowConfig":
        logger.info(config)
        cfg = TaskWorkflowConfig(
            nodes=cls._load_nodes(config["nodes"]),
            begin=config["begin"],
            end=config["end"],
            context=cls._load_context(config["context"]) if "context" in config else {},
        )
        return cfg
    
    @classmethod
    def _load_ctx_value(
        cls, input: Dict[str, Any]
    ) -> Optional[
        Union[
            str,
            float,
            WorkflowSchemaType,
            List[WorkflowSchemaType],
            Dict[str, WorkflowSchemaType],
        ]
    ]:
        input_type: str = input["type"]
        v: Optional[
            Union[
                str,
                float,
                WorkflowSchemaType,
                List[WorkflowSchemaType],
                Dict[str, WorkflowSchemaType],
            ]
        ] = None
        if input_type == "str":
            v = str(input["value"])
        elif input_type == "float":
            v = float(input["value"])
        elif input_type == "Table":
            v = cls._load_ctx_value_of_table(input["valueOfTable"])
        elif input_type == "List":
            v = cls._load_ctx_value_of_list(input["valueOfList"])
        elif input_type == "Product":
            from fluctlight.agents.expert.shopping_assist import Product
            fields: Dict[str, Any] = input["valueOfObject"]
            v = Product(
                id=cls._load_ctx_value(fields["id"]),
                name=cls._load_ctx_value(fields["name"]),
                description=cls._load_ctx_value(fields["description"]),
                price=cls._load_ctx_value(fields["price"]),
                specs=cls._load_ctx_value(fields["specs"]),
            )
        elif input_type == "ProductSpec":
            from fluctlight.agents.expert.shopping_assist import ProductSpec
            fields: Dict[str, Any] = input["valueOfObject"]
            v = ProductSpec(
                name=cls._load_ctx_value(fields["name"]),
                choices=cls._load_ctx_value(fields["choices"]),
            )
        elif input_type == "Inventory":
            from fluctlight.agents.expert.shopping_assist import Inventory
            fields: Dict[str, Any] = input["valueOfObject"]
            v = Inventory(
                products=cls._load_ctx_value(fields["products"]),
            )
        return v

    @classmethod
    def _load_ctx_value_of_table(
        cls, inputs: List[Dict[str, Any]]
    ) -> Dict[str, WorkflowSchemaType]:
        result: Dict[str, WorkflowSchemaType] = {}
        for input in inputs:
            v = cls._load_ctx_value(input)
            if v is None:
                continue
            result[input["name"]] = v
        return result

    @classmethod
    def _load_ctx_value_of_list(
        cls, inputs: List[Dict[str, Any]]
    ) -> List[WorkflowSchemaType]:
        result: List[WorkflowSchemaType] = []
        for input in inputs:
            v = cls._load_ctx_value(input)
            if v is None:
                continue
            result.append(v)
        return result

    @classmethod
    def _load_context(
        cls, inputs: List[Dict[str, Any]]
    ) -> Dict[str, WorkflowSchemaType]:
        return cls._load_ctx_value_of_table(inputs)


class WorkflowNodeOutput(BaseModel):
    output_type: Literal["SUCCESS", "LOOP_MESSAGE_TRUE", "LOOP_MESSAGE_FALSE"]
    loop_message: Optional[str] = None


class WorkflowRunningState(TypedDict):
    session_id: str
    current_node: str
    running_state: Dict[str, Any]
    output_state: Dict[str, WorkflowNodeOutput]


@dataclass
class WorkflowRunnerConfig:
    config: TaskWorkflowConfig
    state_graph: CompiledStateGraph


def has_internal_upstreams(upstreams: List[str]) -> bool:
    return INTERNAL_UPSTREAM_INPUT_MESSAGE in upstreams


def is_internal_upstream(upstream: str) -> bool:
    if upstream in [
        INTERNAL_UPSTREAM_INPUT_MESSAGE,
        INTERNAL_UPSTREAM_HISTORY_MESSAGES,
    ]:
        return True
    return False
