import os
import re
import yt_dlp
from pydub import AudioSegment

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "data", "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def sanitize_filename(name: str) -> str:
    """Sanitize a string to be a safe filename across operating systems."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def download_youtube_audio(url: str) -> str:
    """
    Downloads audio from a YouTube URL and converts it to a standard 16kHz mono WAV file.
    Uses video ID in the filename template to avoid invalid Windows path characters.
    """
    output_template = os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "windowsfilenames": True,
        "restrictfilenames": True,
        "js_runtimes": {"node": {}},
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info.get("id", "audio")
        raw_wav_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.wav")
        if not os.path.exists(raw_wav_path):
            raw_wav_path = os.path.splitext(ydl.prepare_filename(info))[0] + ".wav"

    # Normalize audio to 16kHz mono for Whisper & Sarvam
    normalized_wav_path = os.path.join(DOWNLOAD_DIR, f"{video_id}_16k.wav")
    audio = AudioSegment.from_file(raw_wav_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(normalized_wav_path, format="wav")

    # Remove intermediate raw wav if separate
    if os.path.abspath(raw_wav_path) != os.path.abspath(normalized_wav_path) and os.path.exists(raw_wav_path):
        try:
            os.remove(raw_wav_path)
        except OSError:
            pass

    return normalized_wav_path

def convert_to_wav(input_path: str) -> str:
    """Convert any local audio/video file to 16kHz mono WAV format in the downloads directory."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    base_name = sanitize_filename(os.path.splitext(os.path.basename(input_path))[0])
    output_path = os.path.join(DOWNLOAD_DIR, f"{base_name}_16k.wav")

    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(output_path, format="wav")
    return output_path

def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list[str]:
    """
    Splits a WAV file into chunks of chunk_minutes (default 10 mins).
    Outputs chunk files in DOWNLOAD_DIR.
    Guarantees no empty or micro (<1s) chunks are generated.
    """
    audio = AudioSegment.from_file(wav_path)
    total_len = len(audio)

    if total_len == 0:
        return []

    chunk_ms = chunk_minutes * 60 * 1000
    base_name = os.path.splitext(os.path.basename(wav_path))[0]

    # If audio is shorter than chunk size, return the file itself as 1 chunk
    if total_len <= chunk_ms:
        return [wav_path]

    chunks = []
    starts = list(range(0, total_len, chunk_ms))

    for i, start in enumerate(starts):
        end = min(start + chunk_ms, total_len)

        # If remaining fragment at end is < 2 seconds, absorb it into current chunk
        if i == len(starts) - 2 and (total_len - end) < 2000:
            end = total_len

        chunk = audio[start:end]
        if len(chunk) < 800:  # skip any fragment shorter than 0.8s
            continue

        chunk_path = os.path.join(DOWNLOAD_DIR, f"{base_name}_chunk_{i}.wav")
        chunk.export(chunk_path, format="wav")
        chunks.append(chunk_path)

        if end == total_len:
            break

    return chunks if chunks else [wav_path]

def process_input(source: str) -> list[str]:
    """Processes either a YouTube URL or a local file path into audio chunks."""
    source_clean = source.strip().strip("'").strip('"')
    if source_clean.startswith("http://") or source_clean.startswith("https://"):
        print("Detected YouTube URL. Downloading audio...")
        wav_path = download_youtube_audio(source_clean)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source_clean)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks

def cleanup_chunks(chunks: list[str]):
    """Helper to remove temporary chunk files after processing to save disk space."""
    for chunk in chunks:
        if os.path.exists(chunk):
            try:
                os.remove(chunk)
            except OSError:
                pass
