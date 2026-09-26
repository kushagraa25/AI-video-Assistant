import os
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from backend.audio_processor import process_input, cleanup_chunks
from backend.transcriber import transcribe_all
from backend.summarizer import (
    summarize,
    generate_title,
    extract_action_items,
    extract_key_decisions,
    extract_questions,
)
from backend.rag_engine import build_rag_chain, ask_question

class VideoAssistantPipeline:
    """
    End-to-End Orchestrator for the AI Video Assistant.
    Coordinates audio extraction, ASR transcription, LLM summarization,
    insights extraction, and RAG vector store indexing.
    """

    def __init__(
        self,
        language: str = "english",
        whisper_model: str = "base",
        cleanup_temp_audio: bool = False,
    ):
        self.language = language
        self.whisper_model = whisper_model
        self.cleanup_temp_audio = cleanup_temp_audio

    def run(
        self,
        source: str,
        progress_callback: Callable[[str, str], None] | None = None,
    ) -> dict:
        """
        Executes the full pipeline for a given media source.

        Args:
            source: YouTube URL or local video/audio file path.
            progress_callback: Optional callable(step_name, status) for UI updates.

        Returns:
            Dictionary containing title, transcript, summary, action_items,
            key_decisions, open_questions, and rag_chain.
        """
        def update_step(step_name: str, status: str):
            if progress_callback:
                progress_callback(step_name, status)

        # 1. Audio Processing
        update_step("audio", "active")
        chunks = process_input(source)
        if not chunks:
            update_step("audio", "error")
            raise ValueError(f"No audio chunks could be generated from source: {source}")
        update_step("audio", "done")

        # 2. Speech-to-Text Transcription
        update_step("transcript", "active")
        transcript = transcribe_all(
            chunks=chunks,
            language=self.language,
            model_name=self.whisper_model,
        )
        if not transcript or not transcript.strip():
            update_step("transcript", "error")
            raise ValueError("No speech could be transcribed from the provided audio.")
        update_step("transcript", "done")

        # Cleanup intermediate chunk files if enabled
        if self.cleanup_temp_audio:
            cleanup_chunks(chunks)

        # 3. Concurrent NLP & RAG Indexing
        update_step("title", "active")
        update_step("summary", "active")
        update_step("extract", "active")
        update_step("rag", "active")

        with ThreadPoolExecutor(max_workers=5) as executor:
            f_title     = executor.submit(generate_title, transcript)
            f_summary   = executor.submit(summarize, transcript)
            f_actions   = executor.submit(extract_action_items, transcript)
            f_decisions = executor.submit(extract_key_decisions, transcript)
            f_questions = executor.submit(extract_questions, transcript)
            f_rag       = executor.submit(build_rag_chain, transcript)

            title = f_title.result()
            update_step("title", "done")

            summary = f_summary.result()
            update_step("summary", "done")

            actions = f_actions.result()
            decisions = f_decisions.result()
            questions = f_questions.result()
            update_step("extract", "done")

            rag_chain = f_rag.result()
            update_step("rag", "done")

        return {
            "title": title,
            "transcript": transcript,
            "summary": summary,
            "action_items": actions,
            "key_decisions": decisions,
            "open_questions": questions,
            "rag_chain": rag_chain,
        }

def run_pipeline(
    source: str,
    language: str = "english",
    whisper_model: str = "base",
) -> dict:
    """Convenience helper to run the full pipeline in a single call."""
    pipeline = VideoAssistantPipeline(language=language, whisper_model=whisper_model)
    return pipeline.run(source)
