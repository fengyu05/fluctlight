from typing import Literal

from fluctlight.agents.expert.data_model import (
    IntakeHistoryMessage,
    IntakeMessage,
    TaskEntity,
    TaskNodeValidation,
)
from fluctlight.agents.expert.task_workflow_agent import TaskWorkflowAgent
from fluctlight.agents.expert.task_workflow_config import (
    INTERNAL_UPSTREAM_HISTORY_MESSAGES,
    INTERNAL_UPSTREAM_INPUT_MESSAGE,
    WorkflowConfig,
    WorkflowNodeConfig,
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
        validation_config=TaskNodeValidation(
            success_criteria="""Match user intention, if is buy shoe, return True, otherwise return False.
UserIntent: {{guide_to_buy_product.user_intent}}""",
            failed_message="{{guide_to_buy_product.assistant_response_msg}}",
            passed_message="""Thanks for being interested in buying shoe. Please take a look at the inventory below.
                {{inventory.all_product_desc}}
            """,
        ),
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
            INTERNAL_UPSTREAM_INPUT_MESSAGE: IntakeMessage,
            "guide_to_buy_product": UserIntent,
        },
        output_schema=ProductMatch,
        validation_config=TaskNodeValidation(
            success_criteria="""Determine whether the product selected is in the inventory.
            If it is yes, return True; otherwise, return False.
            Product Selective:
            {{product_interests.product}}
            Inventory:
            {{inventory.all_product_desc}}
            """,
            failed_message="""Please select from the following inventory:
            {{inventory.all_product_desc}}
            """,
            passed_message="""Based the product match, response to guide user to purchar the product.
            Product:
            {{product_interests.product}}
            """,
        ),
    )


def product_order_config() -> WorkflowNodeConfig:
    return WorkflowNodeConfig(
        instruction="""User are interested in {{product_interests.product.product_id_and_name}}.
The product has specs {{product_interests.product.all_spec_in_json}}. Take user input and place the order.

User query: {{__INPUT_MESSAGE.text}}
""",
        input_schema={
            INTERNAL_UPSTREAM_INPUT_MESSAGE: IntakeMessage,
            "product_interests": ProductMatch,
        },
        output_schema=Order,
        validation_config=TaskNodeValidation(
            success_criteria="""Determine whether the order is in the product spec described below.
            If it is consistent, return True; otherwise, return False.

            Order:
            {{product_order.spec}}

            Spec:
            {{product_interests.product.all_spec_in_json}}.
            """,
            failed_message="""You are interested in {{product_interests.product.product_id_and_name}}.
            The product has specs {{product_interests.product.all_spec_in_json}}.

            What do you like?
            """,
            passed_message="""Here is your order.
            {{product_order}}
            """,
        ),
    )


def create_shopping_assist_task_graph_agent() -> TaskWorkflowAgent:
    config = WorkflowConfig(
        nodes={
            "guide_to_buy_product": guide_to_buy_product_config(),
            "product_interests": product_interests_config(),
            "product_order": product_order_config(),
        },
        begin="guide_to_buy_product",
        end="product_order",
    )

    agent = TaskWorkflowAgent(
        name="Shopping assisist",
        description="This task assisist shopper to discover what product are avialiable, place order and follow the status of the order.",
        intent=create_intent(INTENT_KEY),
        context={"inventory": create_inventory()},
        config=config,
    )

    return agent
