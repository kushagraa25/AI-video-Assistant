"""
Step 3 - Understanding: use the Mistral LLM to produce a title, a summary,
action items, key decisions and open questions from the transcript.
"""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.llm_service import get_llm


def ask_llm(instructions: str, text: str, temperature: float = 0.2) -> str:
    """Runs one LLM call: system instructions + text -> answer (LangChain LCEL chain)."""
    prompt = ChatPromptTemplate.from_messages([("system", instructions), ("human", "{text}")])
    chain = prompt | get_llm(temperature) | StrOutputParser()
    return chain.invoke({"text": text})


def summarize(transcript: str) -> str:
    """
    Short transcript -> summarized in one call.
    Long transcript  -> Map-Reduce: summarize each part in parallel, then combine the parts.
    """
    parts = RecursiveCharacterTextSplitter(chunk_size=12000, chunk_overlap=500).split_text(transcript)
    instructions = "You are an expert meeting summarizer. Write a clear, professional summary in bullet points."

    if len(parts) == 1:
        return ask_llm(instructions, parts[0], temperature=0.3)

    # Map: summarize every part at the same time
    map_prompt = ChatPromptTemplate.from_messages([
        ("system", "Summarize this portion of a meeting transcript concisely."),
        ("human", "{text}"),
    ])
    map_chain = map_prompt | get_llm(0.3) | StrOutputParser()
    part_summaries = map_chain.batch([{"text": part} for part in parts], config={"max_concurrency": 4})

    # Reduce: merge the partial summaries into one
    return ask_llm(
        instructions + " Combine these partial summaries into one final summary.",
        "\n\n".join(part_summaries),
        temperature=0.3,
    )


def clean_title(raw_title: str) -> str:
    """LLMs often wrap titles in markdown/quotes, e.g. **"Title"** -> Title."""
    first_line = (raw_title.strip().splitlines() or [""])[0]
    return first_line.strip("*#_`'\" ").strip() or "Untitled Meeting"


def generate_title(transcript: str) -> str:
    raw = ask_llm(
        "Based on the meeting transcript, generate a short professional meeting title "
        "(max 8 words). Only return the title, nothing else.",
        transcript[:2000],
        temperature=0.3,
    )
    return clean_title(raw)


def extract_action_items(transcript: str) -> str:
    return ask_llm(
        "You are an expert meeting analyst. From the meeting transcript, extract all action items. "
        "For each provide:\n- Task description\n- Owner (who is responsible)\n"
        "- Deadline (if mentioned, else write 'Not specified')\n\n"
        "Format as a numbered list. If none found say 'No action items found.'",
        transcript,
    )


def extract_key_decisions(transcript: str) -> str:
    return ask_llm(
        "You are an expert meeting analyst. From the meeting transcript, extract all key decisions "
        "made. Format as a numbered list. If none found say 'No key decisions found.'",
        transcript,
    )


def extract_open_questions(transcript: str) -> str:
    return ask_llm(
        "From the meeting transcript, extract all unresolved questions or topics needing "
        "follow-up. Format as a numbered list. If none found say 'No open questions found.'",
        transcript,
    )
