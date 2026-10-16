"""
Step 2 - Speech-to-text:
  - English  -> OpenAI Whisper, running locally (free, private)
  - Hinglish -> Sarvam AI cloud API (transcribes and translates code-mixed speech to English)
"""

import os
import threading
from concurrent.futures import ThreadPoolExecutor

import requests
import torch
import whisper
from pydub import AudioSegment
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Limit PyTorch threads so transcription doesn't freeze the web UI
torch.set_num_threads(min(4, os.cpu_count() or 1))

SARVAM_URL = "https://api.sarvam.ai/speech-to-text-translate"
SARVAM_PIECE_SECONDS = 25  # Sarvam accepts at most ~30 s of audio per request
SARVAM_PARALLEL_REQUESTS = int(os.getenv("SARVAM_MAX_WORKERS", "8"))

_whisper_models = {}


# ── English: Whisper (local) ───────────────────────────────────────────────────

def load_whisper(model_name: str):
    """Loads a Whisper model once and keeps it in memory."""
    if model_name not in _whisper_models:
        print(f"Loading Whisper model '{model_name}'...")
        _whisper_models[model_name] = whisper.load_model(model_name)
    return _whisper_models[model_name]


def transcribe_with_whisper(chunk_path: str, model_name: str) -> str:
    model = load_whisper(model_name)
    try:
        result = model.transcribe(chunk_path, language="en", fp16=torch.cuda.is_available())
        return result["text"].strip()
    except RuntimeError as e:
        # Whisper fails on completely silent / empty audio - treat it as "no speech"
        print(f"Skipping chunk with no speech ({chunk_path}): {e}")
        return ""


# ── Hinglish: Sarvam AI (cloud) ────────────────────────────────────────────────

_thread_local = threading.local()


def _sarvam_session() -> requests.Session:
    """
    One HTTP session per worker thread: connections are reused, and failed requests
    (connection resets, rate limits, server errors) are retried automatically.
    """
    if not hasattr(_thread_local, "session"):
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504],
                      allowed_methods=None)
        session = requests.Session()
        session.mount("https://", HTTPAdapter(max_retries=retry))
        _thread_local.session = session
    return _thread_local.session


def _send_piece_to_sarvam(piece_path: str) -> str:
    with open(piece_path, "rb") as f:
        response = _sarvam_session().post(
            SARVAM_URL,
            headers={"api-subscription-key": os.getenv("SARVAM_API_KEY")},
            files={"file": (os.path.basename(piece_path), f, "audio/wav")},
            data={"model": os.getenv("SARVAM_STT_MODEL", "saaras:v2.5")},
            timeout=120,
        )
    response.raise_for_status()
    return response.json().get("transcript", "")


def _split_into_pieces(chunk_path: str) -> list[str]:
    """Cuts a chunk into 25-second WAV pieces (Sarvam's per-request limit)."""
    audio = AudioSegment.from_file(chunk_path)
    piece_ms = SARVAM_PIECE_SECONDS * 1000
    pieces = []
    for i, start in enumerate(range(0, len(audio), piece_ms)):
        piece = audio[start:start + piece_ms]
        if len(piece) < 500:  # skip a tiny leftover tail
            continue
        path = f"{chunk_path}_piece_{i}.wav"
        piece.export(path, format="wav").close()
        pieces.append(path)
    return pieces


def transcribe_with_sarvam(chunks: list[str]) -> str:
    """Sends all 25-second pieces to Sarvam in parallel and joins the results in order."""
    if not os.getenv("SARVAM_API_KEY"):
        raise RuntimeError("SARVAM_API_KEY is not set in the .env file.")

    pieces = [piece for chunk in chunks for piece in _split_into_pieces(chunk)]
    print(f"Sending {len(pieces)} pieces to Sarvam AI ({SARVAM_PARALLEL_REQUESTS} at a time)...")

    def transcribe_piece(path: str) -> str:
        try:
            return _send_piece_to_sarvam(path)
        except Exception as e:
            print(f"Sarvam failed for {path}: {e}")
            return ""
        finally:
            os.remove(path)

    with ThreadPoolExecutor(max_workers=SARVAM_PARALLEL_REQUESTS) as pool:
        texts = list(pool.map(transcribe_piece, pieces))  # map() keeps the original order

    return " ".join(text for text in texts if text).strip()


# ── Entry point ────────────────────────────────────────────────────────────────

def transcribe_all(chunks: list[str], language: str = "english", model_name: str = "base") -> str:
    """Transcribes all audio chunks and returns one transcript string."""
    if language.lower() == "hinglish":
        return transcribe_with_sarvam(chunks)

    texts = []
    for i, chunk in enumerate(chunks, start=1):
        print(f"Whisper ({model_name}): transcribing chunk {i}/{len(chunks)}...")
        texts.append(transcribe_with_whisper(chunk, model_name))
    return " ".join(text for text in texts if text).strip()
