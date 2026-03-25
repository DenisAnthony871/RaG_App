import uuid
import logging
import importlib.resources
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import MessagesState
from symspellpy import SymSpell, Verbosity
from better_profanity import profanity
from config import HARMFUL_KEYWORDS, JIO_KEYWORDS, KEYWORD_THRESHOLD, MAX_REWRITES, CUSTOM_CORRECTIONS
from chains import rewrite_chain, response_model

logger = logging.getLogger(__name__)


# ============= SYMSPELL SETUP =============
sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
dictionary_path = str(importlib.resources.files("symspellpy") / "frequency_dictionary_en_82_765.txt")
sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)


def correct_spelling(text: str) -> str:
    words = text.split()
    corrected = []
    for word in words:
        word_lower = word.lower()
        # Custom dictionary first — protects brand names and Jio-specific terms
        if word_lower in CUSTOM_CORRECTIONS:
            corrected.append(CUSTOM_CORRECTIONS[word_lower])
        else:
            suggestions = sym_spell.lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
            corrected.append(suggestions[0].term if suggestions else word)
    return " ".join(corrected)


# ============= NODE 1: VALIDATE INPUT =============
def validate_input(state: MessagesState):
    messages = state["messages"]
    user_msg = messages[-1].content if messages else ""
    cleaned = user_msg.strip()

    # Length check — raised to 8 to catch gibberish like "hjkl"
    if len(cleaned) < 8:
        return {"messages": [AIMessage(content="Please ask a more specific question about Jio services.")]}

    # Harmful keyword check
    if any(keyword in cleaned.lower() for keyword in HARMFUL_KEYWORDS):
        return {"messages": [AIMessage(content="I can't help with that. Please ask about Jio services instead.")]}

    # Profanity check
    if profanity.contains_profanity(cleaned):
        logger.warning(f"Profanity detected in input: '{cleaned[:50]}'")
        return {"messages": [AIMessage(content="Please keep your message respectful. How can I help you with Jio services?")]}

    # Spell correction
    corrected = correct_spelling(cleaned)
    if corrected != cleaned:
        logger.info(f"Spell corrected: '{cleaned}' -> '{corrected}'")

    # Replace last message with corrected version (preserve history)
    messages[-1] = HumanMessage(content=corrected)
    return {"messages": messages}

def after_validate(state: MessagesState) -> str:
    """Route to end if validate_input returned a blocked response, otherwise continue"""
    last_msg = state["messages"][-1]
    if last_msg.type == "ai":
        return "end"
    return "continue"

def is_fallback(state: MessagesState) -> str:
    """Check if rewrite_question returned a fallback message or a real rewrite"""
    last_msg = state["messages"][-1]

    # If last message is AIMessage it means max rewrites was hit
    if last_msg.type == "ai":
        logger.info("Fallback reached — exiting graph")
        return "end"

    # If last message is HumanMessage it's a real rewrite — continue
    return "continue"


# ============= NODE 2: ENRICH CONTEXT =============
def enrich_context(state: MessagesState):
    messages = state["messages"]
    question = next((msg.content for msg in messages if msg.type == "human"), "")

    intent = "general"
    if any(word in question.lower() for word in ["how", "fix", "issue", "problem", "solve", "wrong", "not working", "broken"]):
        intent = "troubleshooting"
    elif any(word in question.lower() for word in ["what", "tell", "explain", "describe"]):
        intent = "informational"
    elif any(word in question.lower() for word in ["cost", "price", "plan", "recharge"]):
        intent = "billing"

    logger.info(f"User Intent Detected: {intent}")
    return {"messages": messages}


# ============= NODE 3: GENERATE QUERY OR RESPOND =============
def generate_query_or_respond(state: MessagesState):
    messages = state["messages"]
    question = next(
        (msg.content for msg in reversed(messages) if msg.type == "human"), ""
    )

    tool_call_msg = AIMessage(
        content="",
        tool_calls=[{
            "name": "retriever_tool",
            "args": {"query": question},
            "id": str(uuid.uuid4()),
            "type": "tool_call"
        }]
    )

    logger.info(f"Forcing retrieval for: {question[:80]}")
    return {"messages": [tool_call_msg]}


# ============= NODE 4: REWRITE QUESTION =============
def rewrite_question(state: MessagesState):
    messages = state["messages"]

    rewrite_count = sum(1 for msg in messages if msg.type == "human") - 1

    if rewrite_count >= MAX_REWRITES:
        logger.warning("Max rewrites reached, returning fallback answer")
        return {"messages": [AIMessage(content="I'm sorry, I couldn't find relevant information. Please try rephrasing or contact Jio support directly.")]}

    question = next(
        (msg.content for msg in reversed(messages) if msg.type == "human"), ""
    )

    if not question:
        return {"messages": messages}

    better_question = rewrite_chain.invoke({"question": question})

    logger.info(f"Rewrite #{rewrite_count} | Original: {question[:80]}")
    logger.info(f"Rewritten: {better_question}")

    messages.append(HumanMessage(content=better_question))
    return {"messages": messages}


# ============= GRADE DOCUMENTS (ROUTER) =============
def grade_documents(state: MessagesState) -> str:
    messages = state["messages"]
    tool_result = next((msg.content for msg in reversed(messages) if msg.type == "tool"), "")

    logger.info(f"Grading documents — Retrieved: {len(tool_result)} chars")

    if not tool_result or "No results found" in tool_result:
        return "rewrite_question"

    keyword_hits = sum(1 for kw in JIO_KEYWORDS if kw in tool_result.lower())

    if keyword_hits >= KEYWORD_THRESHOLD:
        logger.info(f"RELEVANT: {keyword_hits} keywords found")
        return "generate_answer"

    logger.info(f"NOT RELEVANT: only {keyword_hits} keywords, rewriting...")
    return "rewrite_question"


# ============= NODE 5: GENERATE ANSWER =============
def generate_answer(state: MessagesState):
    messages = state["messages"]

    question = next(
        (msg.content for msg in reversed(messages) if msg.type == "human"),
        "No question found"
    )

    tool_messages = [msg.content for msg in messages if msg.type == "tool"]
    tool_message = "\n\n".join(tool_messages) if tool_messages else "No documents retrieved."

    plain_prompt = f"""You are a Jio customer support assistant.
Use the context below to answer the question.
Write your answer in plain English sentences only.
Do not write JSON, do not call functions, do not use tools.

CONTEXT:
{tool_message}

QUESTION:
{question}

ANSWER (plain English only):"""

    response = response_model.invoke(plain_prompt)
    answer = response.content

    # Check if LLM returned JSON (shouldn't happen with plain text prompt)
    import json
    if answer.strip():
        try:
            json.loads(answer)
            answer = "I don't have enough information to answer that question."
        except (json.JSONDecodeError, ValueError):
            pass

    logger.info(f"Generated answer: {answer[:100]}...")
    return {"messages": [AIMessage(content=answer)]}


# ============= NODE 6: FORMAT ANSWER =============

# Phrases that indicate a refusal or fallback — don't append sources to these
REFUSAL_PHRASES = [
    "i'm sorry",
    "i can't",
    "i cannot",
    "couldn't find",
    "don't have enough",
    "please keep your message",
    "i don't have",
    "not able to help",
]

def format_answer(state: MessagesState):
    messages = state["messages"]
    answer_msg = messages[-1].content if messages else ""

    # Don't append sources to refusals or fallbacks
    if any(phrase in answer_msg.lower() for phrase in REFUSAL_PHRASES):
        return {"messages": [AIMessage(content=answer_msg)]}

    tool_msg = next((msg.content for msg in reversed(messages) if msg.type == "tool"), "")

    formatted = f"{answer_msg}\n\n---\n**Sources:** Retrieved from Jio Knowledge Base"
    if tool_msg and "No results found" not in tool_msg:
        formatted += "\n✓ Information verified from retrieved documents"

    return {"messages": [AIMessage(content=formatted)]}


# ============= HALLUCINATION ROUTER =============
def hallucination_router(state: MessagesState) -> str:
    messages = state["messages"]
    answer = messages[-1].content if messages else ""
    context = next((msg.content for msg in reversed(messages) if msg.type == "tool"), "")

    if not context or "No results found" in context:
        return "end"

    # Keyword overlap check — fast, deterministic, no LLM call
    context_words = set(context.lower().split())
    answer_words = set(answer.lower().split())
    overlap = answer_words & context_words

    if len(overlap) < 5:
        logger.warning(f"Low overlap ({len(overlap)} words), answer may not be grounded")
        return "rewrite_question"

    logger.info(f"Answer grounded — {len(overlap)} overlapping words with context")
    return "end"