from typing import Any

from fluctlight.agents.expert.workflow_config import (
    WorkflowConfig,
    WorkflowNodeConfig,
    WorkflowSchemaType,
    ContextValue,
)
from fluctlight.logger import get_logger

logger = get_logger(__name__)

class WorkflowContext:
    context: dict[str, WorkflowSchemaType] | None = None 

    @classmethod
    def _load_nodes(cls, config: dict[str, Any]) -> dict[str, WorkflowNodeConfig]:
        cfg = dict()
        for k, v in config.items():
            cfg[k] = WorkflowNodeConfig.load_from_config(v)
        return cfg
    
    @classmethod
    def load_from_config(cls, config: dict[str, Any]) -> "WorkflowConfig":
        logger.info(config)
        cfg = WorkflowConfig(
            nodes=cls._load_nodes(config["nodes"]),
            begin=config["begin"],
            end=config["end"],
            context=cls._load_context(config["context"]) if "context" in config else {},
        )
        return cfg
    
    @classmethod
    def _load_ctx_value(
        cls, input: dict[str, Any]
    ) -> ContextValue:
        input_type: str = input["type"]
        v: ContextValue = None
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
            fields: dict[str, Any] = input["valueOfObject"]
            v = Product(
                id=cls._load_ctx_value(fields["id"]),
                name=cls._load_ctx_value(fields["name"]),
                description=cls._load_ctx_value(fields["description"]),
                price=cls._load_ctx_value(fields["price"]),
                specs=cls._load_ctx_value(fields["specs"]),
            )
        elif input_type == "ProductSpec":
            from fluctlight.agents.expert.shopping_assist import ProductSpec
            fields: dict[str, Any] = input["valueOfObject"]
            v = ProductSpec(
                name=cls._load_ctx_value(fields["name"]),
                choices=cls._load_ctx_value(fields["choices"]),
            )
        elif input_type == "Inventory":
            from fluctlight.agents.expert.shopping_assist import Inventory
            fields: dict[str, Any] = input["valueOfObject"]
            v = Inventory(
                products=cls._load_ctx_value(fields["products"]),
            )
        return v

    @classmethod
    def _load_ctx_value_of_table(
        cls, inputs: list[dict[str, Any]]
    ) -> dict[str, WorkflowSchemaType]:
        result: dict[str, WorkflowSchemaType] = {}
        for input in inputs:
            v = cls._load_ctx_value(input)
            if v is None:
                continue
            result[input["name"]] = v
        return result

    @classmethod
    def _load_ctx_value_of_list(
        cls, inputs: list[dict[str, Any]]
    ) -> list[WorkflowSchemaType]:
        result: list[WorkflowSchemaType] = []
        for input in inputs:
            v = cls._load_ctx_value(input)
            if v is None:
                continue
            result.append(v)
        return result

    @classmethod
    def _load_context(
        cls, inputs: list[dict[str, Any]]
    ) -> dict[str, WorkflowSchemaType]:
        return cls._load_ctx_value_of_table(inputs)