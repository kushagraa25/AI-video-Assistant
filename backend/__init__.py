"""
AI Meeting & Video Assistant - Backend Package
Provides core AI modules for audio ingestion, transcription, summarization, and RAG.
"""

from backend.pipeline import VideoAssistantPipeline, run_pipeline
from backend.audio_processor import (
    process_input,
    cleanup_chunks,
    download_youtube_video,
    list_downloaded_videos,
    DOWNLOADED_VIDEOS_DIR,
    get_cookie_file,
    save_cookie_content,
)
from backend.transcriber import transcribe_all
from backend.summarizer import summarize, generate_title, extract_meeting_insights
from backend.rag_engine import build_rag_chain, ask_question

__all__ = [
    "VideoAssistantPipeline",
    "run_pipeline",
    "process_input",
    "cleanup_chunks",
    "download_youtube_video",
    "list_downloaded_videos",
    "DOWNLOADED_VIDEOS_DIR",
    "get_cookie_file",
    "save_cookie_content",
    "transcribe_all",
    "summarize",
    "generate_title",
    "extract_meeting_insights",
    "build_rag_chain",
    "ask_question",
]
