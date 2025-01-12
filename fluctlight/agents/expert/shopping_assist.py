from typing import Literal

from fluctlight.agents.expert.data_model import (
    IntakeHistoryMessage,
    IntakeMessage,
    TaskConfig,
    TaskEntity,
)
from fluctlight.agents.expert.task_agent import TaskAgent
from fluctlight.agents.expert.workflow import (
    WorkflowConfig,
    WorkflowNodeConfig,
    build_workflow_graph,
)
from fluctlight.agents.expert.workflow_config import (
    INTERNAL_UPSTREAM_HISTORY_MESSAGES,
    INTERNAL_UPSTREAM_INPUT_MESSAGE,
    WorkflowNodeLLMResponse,
    WorkflowNodeLoopMessage,
    WorkflowRunnerConfig,
)
from fluctlight.intent.message_intent import create_intent

INTENT_KEY = "SHOPPING_ASSIST"


class ProductSpec(TaskEntity):
    name: str
    choices: list[str]

    @property
    def desc_short(self) -> str:
        return f'{self.name}:[{" ".join(self.choices)}]'


class Product(TaskEntity):
    id: str
    name: str
    description: str
    price: float
    specs: list[ProductSpec]

    @property
    def desc_short(self) -> str:
        return f"id: {self.name} name: {self.name}, desc: {self.description}, price: {self.price}"

    @property
    def all_spec(self) -> str:
        return " ".join([spec.desc_short for spec in self.specs])

    @property
    def product_id_and_name(self) -> str:
        return f"id: {self.id} name: {self.name}"

    @property
    def all_spec_in_json(self) -> str:
        return "[" + ", ".join([spec.model_dump_json() for spec in self.specs]) + "]"


class UserIntent(TaskEntity):
    user_intent: Literal["buy_shoe", "other"]
    user_query: str
    assistant_response_msg: str


class ProductMatch(TaskEntity):
    match: bool
    product: Product


class Order(TaskEntity):
    product_id: str
    quantity: str
    spec: ProductSpec


class Inventory(TaskEntity):
    products: dict[str, Product]

    @property
    def all_product_desc(self) -> str:
        return "\n".join(
            [k + ":\n" + p.model_dump_json() for k, p in self.products.items()]
        )


def create_inventory() -> Inventory:
    return Inventory(
        products={
            "shoe_001": Product(
                id="shoe_001",
                name="Asics running shoe GLIDERIDE MAX",
                description="The GLIDERIDE® MAX shoe is the long-run cruiser that makes your training feel smoother and more consistent.",
                price=240.0,
                specs=[
                    ProductSpec(
                        name="size", choices=["size_6", "size_7", "size_8", "size_9"]
                    )
                ],
            ),
            "shoe_002": Product(
                id="shoe_002",
                name="Mens HOKA Bondi 8 Running Shoe - Black / White",
                description="Mens HOKA Bondi 8 Running Shoe - Black / White, Size: 12.5, Wide | Footwear - Road Runner Sports.",
                price=141.0,
                specs=[ProductSpec(name="size", choices=["size_7", "size_8"])],
            ),
        }
    )


def guide_to_buy_product_config() -> WorkflowNodeConfig:
    return WorkflowNodeConfig(
        instruction="""Take user input message, identify the user's intent.
If the intent is not buy shoe, then respond by guiding the user to buy shoe based on the inventory.

History messages:
{{__HISTORY_MESSAGES.to_chat_history}}

User query: {{__INPUT_MESSAGE.text}}

Inventory:
{{inventory.all_product_desc}}
""",
        input_schema={
            INTERNAL_UPSTREAM_INPUT_MESSAGE: IntakeMessage,
            INTERNAL_UPSTREAM_HISTORY_MESSAGES: IntakeHistoryMessage,
        },
        output_schema=UserIntent,
        loop_message=WorkflowNodeLoopMessage(
            mode="text",
            message="{{guide_to_buy_product.assistant_response_msg}}",
        ),
        success_criteria="""Math user intention, if is buy shoe, return True, otherwise return False.
UserIntent: {{guide_to_buy_product.user_intent}}
""",
    )


def product_interests_config() -> WorkflowNodeConfig:
    return WorkflowNodeConfig(
        instruction="""Take users input, match with the below inventory.
If the user does not mention information related to the products in the inventory, it should return false.

User input:
{{guide_to_buy_product.user_query}}

Inventory:
{{inventory.all_product_desc}}
""",
        input_schema={
            # INTERNAL_UPSTREAM_INPUT_MESSAGE: IntakeMessage,
            "guide_to_buy_product": UserIntent,
        },
        output_schema=ProductMatch,
        loop_message=WorkflowNodeLoopMessage(
            mode="text",
            message="""Please select from the following inventory:
{{inventory.all_product_desc}}
""",
        ),
        success_criteria="""Determine whether the product information described below is consistent with the data defined by the inventory.
If it is consistent, return True; otherwise, return False.

Product:
{{product_interests.product}}

Inventory:
{{inventory.all_product_desc}}
""",
        llm_response=WorkflowNodeLLMResponse(
            instruction="""Based the product match, response to guide user to purchar the product.
Product:
{{product_interests.product}}
""",
        ),
    )


def product_specs_config() -> WorkflowNodeConfig:
    return WorkflowNodeConfig(
        instruction="""You seems to be interested in {{product_interests.product.product_id_and_name}}.
The product has specs {{product_interests.product.all_spec_in_json}}.

How do you want your order.
""",
        input_schema={
            INTERNAL_UPSTREAM_INPUT_MESSAGE: IntakeMessage,
            "product_interests": ProductMatch,
        },
        output_schema=Order,
    )


def create_shopping_assist_task_graph_agent() -> TaskAgent:
    config = WorkflowConfig(
        nodes={
            "guide_to_buy_product": guide_to_buy_product_config(),
            "product_interests": product_interests_config(),
            "product_specs": product_specs_config(),
        },
        begin="guide_to_buy_product",
        end="product_specs",
    )

    agent = TaskAgent(
        name="Shopping assisist",
        description="This task assisist shopper to discover what product are avialiable, place order and follow the status of the order.",
        intent=create_intent(INTENT_KEY),
        context={"inventory": create_inventory()},
        workflow_runner_config=WorkflowRunnerConfig(
            config=config,
            state_graph=build_workflow_graph(config),
        ),
        task_graph=[],
    )

    return agent


def create_shopping_assisist_task_agent() -> TaskAgent:
    return TaskAgent(
        name="Shopping assisist",
        description="This task assisist shopper to discover what product are avialiable, place order and follow the status of the order.",
        intent=create_intent(INTENT_KEY),
        context={"inventory": create_inventory()},
        task_graph=[
            TaskConfig(
                task_key="product_interests",
                instruction="Take users input, match with the below inventors. User input: {message.text} \n Inventory: {inventory.all_product_desc} ",
                input_schema={"message": IntakeMessage},
                output_schema=ProductMatch,
            ),
            TaskConfig(
                task_key="product_specs",
                instruction="You seems to be interested in {product_interests.product.desc_short}. \n The product has specs {product_interests.product.all_specs}. How do you want your order.",
                input_schema={
                    "message": IntakeMessage,
                    "product_interests": ProductMatch,
                },
                output_schema=Order,
            ),
        ],
    )
