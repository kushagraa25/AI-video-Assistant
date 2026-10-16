"""
The pipeline: runs the four steps in order and returns everything the UI shows.

  1. audio_processor -> YouTube URL / file  =>  WAV chunks
  2. transcriber     -> WAV chunks          =>  transcript
  3. summarizer      -> transcript          =>  title, summary, action items, decisions, questions
  4. rag_engine      -> transcript          =>  chat chain for Q&A
"""

from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from backend.audio_processor import prepare_audio
from backend.rag_engine import build_rag_chain
from backend.summarizer import (
    extract_action_items,
    extract_key_decisions,
    extract_open_questions,
    generate_title,
    summarize,
)
from backend.transcriber import transcribe_all


def run_pipeline(
    source: str,
    language: str = "english",
    whisper_model: str = "base",
    on_step: Callable[[str, str], None] = lambda step, status: None,
) -> dict:
    """
    source:   YouTube URL or local file path
    language: "english" (Whisper) or "hinglish" (Sarvam AI)
    on_step:  optional callback(step, status) so the UI can show progress
    """
    # 1. Audio
    on_step("audio", "active")
    chunks = prepare_audio(source)
    on_step("audio", "done")

    # 2. Speech-to-text
    on_step("transcript", "active")
    transcript = transcribe_all(chunks, language=language, model_name=whisper_model)
    if not transcript:
        raise ValueError("No speech could be transcribed from this audio.")
    on_step("transcript", "done")

    # 3 + 4. All LLM tasks and the RAG index are independent, so run them in parallel
    for step in ("title", "summary", "extract", "rag"):
        on_step(step, "active")

    with ThreadPoolExecutor(max_workers=6) as pool:
        title = pool.submit(generate_title, transcript)
        summary = pool.submit(summarize, transcript)
        actions = pool.submit(extract_action_items, transcript)
        decisions = pool.submit(extract_key_decisions, transcript)
        questions = pool.submit(extract_open_questions, transcript)
        rag_chain = pool.submit(build_rag_chain, transcript)

        result = {
            "title": title.result(),
            "transcript": transcript,
            "summary": summary.result(),
            "action_items": actions.result(),
            "key_decisions": decisions.result(),
            "open_questions": questions.result(),
            "rag_chain": rag_chain.result(),
        }

    for step in ("title", "summary", "extract", "rag"):
        on_step(step, "done")
    return result
