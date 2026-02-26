from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from database import vectorstore
from config import DB_PATH, COLLECTION_NAME
from tools import tools
from nodes import (
    validate_input,
    enrich_context,
    generate_query_or_respond,
    rewrite_question,
    grade_documents,
    generate_answer,
    format_answer,
    hallucination_router,
    is_fallback,  # new router
)

workflow = StateGraph(MessagesState)

workflow.add_node("validate_input", validate_input)
workflow.add_node("enrich_context", enrich_context)
workflow.add_node("generate_query_or_respond", generate_query_or_respond)
workflow.add_node("retrieve", ToolNode(tools))
workflow.add_node("rewrite_question", rewrite_question)
workflow.add_node("generate_answer", generate_answer)
workflow.add_node("format_answer", format_answer)

workflow.add_edge(START, "validate_input")
workflow.add_edge("validate_input", "enrich_context")
workflow.add_edge("enrich_context", "generate_query_or_respond")

workflow.add_conditional_edges(
    "generate_query_or_respond",
    tools_condition,
    {"tools": "retrieve", END: END},
)

workflow.add_conditional_edges(
    "retrieve",
    grade_documents,
    {
        "generate_answer": "generate_answer",
        "rewrite_question": "rewrite_question",
    },
)

workflow.add_edge("generate_answer", "format_answer")

workflow.add_conditional_edges(
    "format_answer",
    hallucination_router,
    {
        "end": END,
        "rewrite_question": "rewrite_question",
    },
)

# Key fix — rewrite can now exit to END if fallback was returned
workflow.add_conditional_edges(
    "rewrite_question",
    is_fallback,
    {
        "end": END,
        "continue": "generate_query_or_respond",
    },
)

graph = workflow.compile()