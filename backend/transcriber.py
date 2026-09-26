import os
import requests
import torch
from dotenv import load_dotenv
from pydub import AudioSegment
import whisper
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

# Prevent PyTorch from pegging 100% CPU on all cores
try:
    torch.set_num_threads(min(4, os.cpu_count() or 1))
except Exception:
    pass

SARVAM_PIECE_SECONDS = 25
SARVAM_STT_TRANSLATE_URL = "https://api.sarvam.ai/speech-to-text-translate"

_models = {}

def load_model(model_name: str | None = None):
    """Loads and caches the local Whisper model."""
    target_model = model_name or os.getenv("WHISPER_MODEL", "base")
    if target_model not in _models:
        print(f"Loading Whisper model: {target_model} ...")
        _models[target_model] = whisper.load_model(target_model)
        print("Whisper model loaded.")
    return _models[target_model]

def transcribe_chunk_whisper(chunk_path: str, model_name: str | None = None, language: str = "english") -> str:
    """Transcribes an audio chunk using local OpenAI Whisper."""
    if not os.path.exists(chunk_path):
        return ""

    try:
        audio_seg = AudioSegment.from_file(chunk_path)
        # Avoid processing chunks that are too short (< 800ms) or completely silent
        if len(audio_seg) < 800 or audio_seg.dBFS < -65:
            return ""
    except Exception:
        pass

    model = load_model(model_name)
    use_cuda = torch.cuda.is_available()

    transcribe_kwargs = {
        "task": "transcribe",
        "fp16": use_cuda,
    }
    if language.lower() == "english":
        transcribe_kwargs["language"] = "en"

    try:
        result = model.transcribe(chunk_path, **transcribe_kwargs)
        return result.get("text", "").strip()
    except RuntimeError as e:
        err_msg = str(e)
        if "cannot reshape tensor of 0 elements" in err_msg or "0 elements" in err_msg:
            print(f"Skipping silent/empty audio segment in {chunk_path}")
            return ""
        raise e
    except Exception as e:
        print(f"Warning: Whisper error on {chunk_path}: {e}")
        return ""

def _send_to_sarvam(piece_path: str) -> str:
    """Send one <= 25s WAV file to Sarvam AI and return English transcript."""
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        raise RuntimeError("SARVAM_API_KEY is not set in environment or .env file.")

    sarvam_model = os.getenv("SARVAM_STT_MODEL", "saaras:v2.5")
    headers = {"api-subscription-key": api_key}

    with open(piece_path, "rb") as f:
        files = {"file": (os.path.basename(piece_path), f, "audio/wav")}
        data = {"model": sarvam_model, "with_diarization": "false"}
        response = requests.post(
            SARVAM_STT_TRANSLATE_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=120,
        )

    if not response.ok:
        print(f"Sarvam returned {response.status_code}: {response.text}")
        response.raise_for_status()

    return response.json().get("transcript", "")

def transcribe_chunk_sarvam(chunk_path: str) -> str:
    """
    Splits chunk into <=25-second pieces to respect Sarvam API limits,
    transcribes concurrently via thread pool, and combines results.
    """
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        raise RuntimeError("SARVAM_API_KEY is not set in environment or .env file.")

    audio = AudioSegment.from_file(chunk_path)
    if len(audio) < 800:
        return ""

    piece_ms = SARVAM_PIECE_SECONDS * 1000
    piece_files = []

    for i, start in enumerate(range(0, len(audio), piece_ms)):
        piece = audio[start: start + piece_ms]
        if len(piece) < 500:
            continue
        piece_path = f"{chunk_path}_sv_{i}.wav"
        piece.export(piece_path, format="wav")
        piece_files.append((i, piece_path))

    transcripts = {}

    def process_piece(idx, p_path):
        try:
            return idx, _send_to_sarvam(p_path)
        finally:
            if os.path.exists(p_path):
                try:
                    os.remove(p_path)
                except OSError:
                    pass

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(process_piece, idx, p_path) for idx, p_path in piece_files]
        for f in as_completed(futures):
            try:
                idx, txt = f.result()
                transcripts[idx] = txt
            except Exception as e:
                print(f"Sarvam piece error: {e}")

    ordered = [transcripts[i] for i in sorted(transcripts.keys()) if transcripts.get(i)]
    return " ".join(ordered).strip()

def transcribe_chunk(chunk_path: str, language: str = "english", model_name: str | None = None) -> str:
    """
    Routes an audio chunk to Whisper or Sarvam depending on language choice:
    - english  -> Whisper (local model)
    - hinglish -> Sarvam AI (transcribes & translates to English)
    """
    if language.lower() == "hinglish":
        return transcribe_chunk_sarvam(chunk_path)
    return transcribe_chunk_whisper(chunk_path, model_name=model_name, language=language)

def transcribe_all(chunks: list[str], language: str = "english", model_name: str | None = None) -> str:
    """Transcribes an array of audio chunks and concatenates the transcript."""
    full_transcript = ""
    selected_model = model_name or os.getenv("WHISPER_MODEL", "base")
    engine = "Sarvam AI" if language.lower() == "hinglish" else f"Whisper ({selected_model})"
    print(f"Using {engine} for transcription.")

    for i, chunk in enumerate(chunks):
        print(f"Transcribing chunk {i + 1}/{len(chunks)}...")
        text = transcribe_chunk(chunk, language=language, model_name=selected_model)
        if text:
            full_transcript += text + " "

    print("Transcription complete.")
    return full_transcript.strip()
