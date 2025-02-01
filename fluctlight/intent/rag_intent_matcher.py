from functools import cached_property

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_fireworks import ChatFireworks
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from typing_extensions import TypedDict
from fluctlight.intent.intent_agent import IntentAgent
from fluctlight.intent.intent_candidate import (
    EXAMPLE_INTENT_CANDIDATE,
    IntentCandidate,
    parse_intent_candidate_json,
)
from fluctlight.intent.intent_matcher_base import IntentMatcher
from fluctlight.logger import get_logger
from fluctlight.utt.prompt_utils import construct_system_prompt
from fluctlight.settings import FIREWORKS_API_KEY

logger = get_logger(__name__)

FIREWORKS_MIXTRAL_22B = "accounts/fireworks/models/mixtral-8x22b-instruct"

_MATCH_PROMPT = """
The system will determine the most appropriate intents from a user message using the following steps:

1. Extract key phrases indicating the user's need or desired action.
2. Identify if the message relates to retail, photo, pharmacy departments, or is vague.
3. Compare these key phrases with intent descriptions.
4. Find which intents best align with extracted phrases.
5. Evaluate how well each intent matches the user's goals.
6. Rank and select the top two relevant intents from the list.

Intent list:
-------------
{{intent_list}}

Output: Generate a JSON in a single line format with the following fields.
    "understanding": "System's interpretation of the message.",
    "intent_key_primary": "Primary intent matching the user's need.",
    "intent_key_secondary": "Secondary intent somewhat matching the need."
-----------------------
Example output format:
{{json_example_payload}}
"""

_REFLECTION_PROMPT = """
Analyze the JSON payload to refine the intent candidate result.
Check if `intent_key_primary`/`intent_key_secondary` match the `Intent list`, fix it with fuzzy match if possible.

Intent list:
-------------
{{intent_choices}}

Output: Output the JSON in a single line format with the same schema as input.
Incoming user messages are the previous output to analye.
"""


class GraphState(TypedDict):
    messages: list[BaseMessage]
    intent_json_payload: str | None  # Json paylod
    intent_candidate: IntentCandidate | None  # LLM generation


class RagIntentMatcher(IntentMatcher):
    def __init__(
        self,
        agents: list[IntentAgent],
        model_id: str = FIREWORKS_MIXTRAL_22B,
        max_tokens: int = 32768,
    ) -> None:
        super().__init__(
            agents=agents,
        )
        self.llm = ChatFireworks(
            model=model_id, max_tokens=max_tokens, api_key=FIREWORKS_API_KEY
        )
        self.match_intent_chain = (
            construct_system_prompt(
                prompt=_MATCH_PROMPT,
                context={
                    "intent_list": self.construct_intent_list,
                    "json_example_payload": EXAMPLE_INTENT_CANDIDATE.perfered_json_serialization,
                },
            )
            | self.llm
        )
        self.refine_intent_chain = (
            construct_system_prompt(
                prompt=_REFLECTION_PROMPT,
                context={
                    "intent_choices": self.intent_keylist,
                    "json_example_payload": EXAMPLE_INTENT_CANDIDATE.perfered_json_serialization,
                },
            )
            | self.llm
        )

        # Build graph
        self.graph = self.build_graph()

    def match_intent_node(self, state: GraphState) -> GraphState:
        logger.debug("match_intent", state=state)
        messages = state["messages"]
        question = messages[0].content
        assert isinstance(question, str), "input question must be text"
        output = self.match_intent_chain.invoke(
            {"messages": [HumanMessage(content=question)]}
        )
        logger.info("match intent output", output=output)
        assert isinstance(output.content, str), "expect output.content to be text"
        intent_candidate = parse_intent_candidate_json(output.content)
        return GraphState(
            messages=messages,
            intent_json_payload=output.content,
            intent_candidate=intent_candidate,
        )

    def refine_intent_node(self, state: GraphState) -> GraphState:
        logger.debug("refine_intent", state=state)
        messages = state["messages"]
        intent_candidate = state["intent_candidate"]
        intent_json_payload = state["intent_json_payload"]
        assert intent_json_payload, "intent_json_payload must present"
        output = self.refine_intent_chain.invoke(
            {
                "messages": [
                    HumanMessage(content=intent_json_payload),
                ]
            }
        )
        logger.info("refine intent output", output=output)
        assert isinstance(output.content, str), "expect output.content to be text"
        intent_candidate = parse_intent_candidate_json(output.content)
        return GraphState(
            messages=messages,
            intent_json_payload=output.content,
            intent_candidate=intent_candidate,
        )

    def promote_candidate_node(self, state: GraphState) -> GraphState:
        intent_candidate = state["intent_candidate"]
        assert intent_candidate, "intent candidate must not be none."
        return GraphState(
            messages=state["messages"],
            intent_json_payload=state["intent_json_payload"],
            intent_candidate=intent_candidate,
            final_intent=intent_candidate.intent_primary,
        )

    def need_refine_edge(self, state: GraphState) -> str:
        intent_candidate = state["intent_candidate"]
        if intent_candidate and intent_candidate.intent_primary in self.intent_keylist:
            return "NO"
        return "YES"

    def build_graph(self) -> CompiledStateGraph:
        workflow = StateGraph(GraphState)
        # Define the nodes
        workflow.add_node("match_intent", self.match_intent_node)
        workflow.add_node("refine_intent", self.refine_intent_node)
        # Add edge
        workflow.add_edge(START, "match_intent")
        workflow.add_conditional_edges(
            "match_intent",
            self.need_refine_edge,
            {
                "NO": END,
                "YES": "refine_intent",
            },
        )
        workflow.add_edge("refine_intent", END)
        return workflow.compile()

    def parse_intent_key(self, text: str) -> str:
        last_state = self.graph.invoke(
            {
                "messages": [HumanMessage(content=text)],
            },
            {"recursion_limit": 10},
        )
        logger.info("parse intent got last state", last_state=last_state)
        return self.parse_final_state(GraphState(**last_state))

    @cached_property
    def construct_intent_list(self) -> str:
        return "\n---\n".join(
            [
                f"{agent.intent.key}: {agent.description}"
                for _, agent in enumerate(self.agents)
                if agent.llm_matchable
            ]
        )

    @cached_property
    def intent_keylist(self) -> list[str]:
        return [
            agent.intent.key
            for _, agent in enumerate(self.agents)
            if agent.llm_matchable
        ]

    def parse_final_state(self, state: GraphState) -> str:
        intent_candidate = state["intent_candidate"]
        assert intent_candidate, "intent candidate cannot be None"
        for intent_key in self.intent_keylist:
            if intent_key in intent_candidate.intent_primary:
                return intent_key
        ## secondary
        for intent_key in self.intent_keylist:
            if intent_key in intent_candidate.intent_secondary:
                return intent_key
        return "CHAT"
