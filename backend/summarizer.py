from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from backend.llm_service import get_llm

def split_transcript(transcript: str, chunk_size: int = 12000, chunk_overlap: int = 500) -> list[str]:
    """Splits transcript into large chunks suitable for Map-Reduce LLM summarization."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return splitter.split_text(transcript)

def build_extraction_chain(system_prompt: str):
    """Utility to build an LCEL extraction chain with Mistral AI."""
    llm = get_llm(temperature=0.2)
    return (
        RunnablePassthrough()
        | RunnableLambda(lambda x: {"text": x})
        | ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{text}"),
        ])
        | llm
        | StrOutputParser()
    )

def summarize(transcript: str) -> str:
    """
    Summarizes meeting transcripts using single-pass or Map-Reduce strategy
    depending on length.
    """
    if not transcript or not transcript.strip():
        return "No transcript content available to summarize."

    llm = get_llm(temperature=0.3)
    chunks = split_transcript(transcript)

    if not chunks:
        return "No transcript content available to summarize."

    # Single-pass for transcripts fitting into one chunk
    if len(chunks) == 1:
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are an expert meeting summarizer. Provide a clear, professional meeting summary in bullet points.",
            ),
            ("human", "{text}"),
        ])
        chain = prompt | llm | StrOutputParser()
        return chain.invoke({"text": chunks[0]})

    # Map-Reduce for long transcripts
    map_prompt = ChatPromptTemplate.from_messages([
        ("system", "Summarize this portion of a meeting transcript concisely."),
        ("human", "{text}"),
    ])
    map_chain = map_prompt | llm | StrOutputParser()

    chunk_summaries = [map_chain.invoke({"text": chunk}) for chunk in chunks]
    combined = "\n\n".join(chunk_summaries)

    combined_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are an expert meeting summarizer. Combine these partial summaries "
            "into one final professional meeting summary in bullet points.",
        ),
        ("human", "{text}"),
    ])

    combined_chain = (
        RunnablePassthrough()
        | RunnableLambda(lambda x: {"text": x})
        | combined_prompt
        | llm
        | StrOutputParser()
    )

    return combined_chain.invoke(combined)

def generate_title(transcript: str) -> str:
    """Generates a concise, professional title (max 8 words) for the meeting."""
    if not transcript or not transcript.strip():
        return "Untitled Meeting"

    llm = get_llm(temperature=0.3)
    title_chain = (
        RunnablePassthrough()
        | RunnableLambda(lambda x: {"text": x})
        | ChatPromptTemplate.from_messages([
            (
                "system",
                "Based on the meeting transcript, generate a short professional meeting title "
                "(max 8 words). Only return the title, nothing else.",
            ),
            ("human", "{text}"),
        ])
        | llm
        | StrOutputParser()
    )

    return title_chain.invoke(transcript[:2000]).strip().strip('"')

def extract_action_items(transcript: str) -> str:
    """Extracts task description, owner, and deadline from meeting transcript."""
    if not transcript or not transcript.strip():
        return "No action items found (empty transcript)."

    chain = build_extraction_chain(
        "You are an expert meeting analyst. From the meeting transcript, "
        "extract all action items. For each provide:\n"
        "- Task description\n"
        "- Owner (who is responsible)\n"
        "- Deadline (if mentioned, else write 'Not specified')\n\n"
        "Format as a numbered list. If none found say 'No action items found.'"
    )
    return chain.invoke(transcript)

def extract_key_decisions(transcript: str) -> str:
    """Extracts key decisions agreed upon during the meeting."""
    if not transcript or not transcript.strip():
        return "No key decisions found (empty transcript)."

    chain = build_extraction_chain(
        "You are an expert meeting analyst. From the meeting transcript, "
        "extract all key decisions made. Format as a numbered list. "
        "If none found say 'No key decisions found.'"
    )
    return chain.invoke(transcript)

def extract_questions(transcript: str) -> str:
    """Extracts open questions or topics requiring follow-up."""
    if not transcript or not transcript.strip():
        return "No open questions found (empty transcript)."

    chain = build_extraction_chain(
        "From the meeting transcript, extract all unresolved questions "
        "or topics needing follow-up. Format as a numbered list. "
        "If none found say 'No open questions found.'"
    )
    return chain.invoke(transcript)

def extract_meeting_insights(transcript: str) -> dict[str, str]:
    """Convenience helper to extract all insights concurrently or sequentially."""
    return {
        "action_items": extract_action_items(transcript),
        "key_decisions": extract_key_decisions(transcript),
        "open_questions": extract_questions(transcript),
    }
