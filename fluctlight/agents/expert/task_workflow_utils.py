from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from fluctlight.agents.expert.task_workflow_config import (
    INTERNAL_UPSTREAM_HISTORY_MESSAGES,
    INTERNAL_UPSTREAM_INPUT_MESSAGE,
    WorkflowConfig,
    WorkflowRunningState,
    is_internal_upstream,
)


def show_graph_mermaid(config: WorkflowConfig, graph: CompiledStateGraph):
    from io import BytesIO

    import matplotlib.pyplot as plt
    from PIL import Image

    # logical graph
    def fn(state):
        return state

    def edge_fn(state) -> str:
        return ""

    wf = StateGraph(WorkflowRunningState)
    for k, v in config.nodes.items():
        wf.add_node(k, fn)
    for n in ["INPUT_MESSAGE", "HISTORY_MESSAGES"]:
        wf.add_node(n, fn)
        wf.add_edge(START, n)
    wf.add_edge(START, config.begin)
    wf.add_edge(config.end, END)
    for k, v in config.nodes.items():
        for upstream, _ in v.input_schema.items():
            if is_internal_upstream(upstream):
                if upstream == INTERNAL_UPSTREAM_INPUT_MESSAGE:
                    wf.add_edge("INPUT_MESSAGE", k)
                elif upstream == INTERNAL_UPSTREAM_HISTORY_MESSAGES:
                    wf.add_edge("HISTORY_MESSAGES", k)
                continue
            if config.nodes[upstream].success_criteria:
                wf.add_conditional_edges(
                    upstream, edge_fn, {"YES": k, "NO: Loop Message": upstream}
                )
            else:
                wf.add_edge(upstream, k)

    logical_graph = wf.compile()
    image1 = Image.open(BytesIO(logical_graph.get_graph().draw_mermaid_png()))

    # executable graph
    graph_bytes = graph.get_graph().draw_mermaid_png()
    image2 = Image.open(BytesIO(graph_bytes))

    total_height = image1.height + image2.height
    max_width = max(image1.width, image2.width)

    combined_image = Image.new("RGB", (max_width, total_height), (255, 255, 255))
    combined_image.paste(image1, ((max_width - image1.width) // 2, 0))
    combined_image.paste(image2, ((max_width - image2.width) // 2, image1.height))

    plt.imshow(combined_image)

    plt.axis("off")
    plt.title("Graph Visualization from PNG Bytes")
    plt.show()
