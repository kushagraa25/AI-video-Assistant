"""
Step 1 - Audio: turn a YouTube URL or a local audio/video file into
16 kHz mono WAV chunks that the speech-to-text step can process.
"""

import importlib.util
import os
import re
import shutil

import yt_dlp
from pydub import AudioSegment

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEOS_DIR = os.path.join(BASE_DIR, "downloaded_videos")  # downloaded YouTube audio
AUDIO_DIR = os.path.join(BASE_DIR, "data", "downloads")    # uploads + converted WAV files
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

CHUNK_MINUTES = 10

# pydub needs ffmpeg; on servers it is often missing from the service's PATH
_ffmpeg = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
if os.path.isfile(_ffmpeg):
    os.environ["PATH"] = os.path.dirname(_ffmpeg) + os.pathsep + os.environ.get("PATH", "")
    AudioSegment.converter = _ffmpeg

# YouTube player clients to try in order. If YouTube challenges one client
# ("confirm you're not a bot" / HTTP 403), another one often still works.
# None = yt-dlp's default clients.
PLAYER_CLIENTS = [None, ["tv_simply", "tv"], ["android_vr"], ["web_safari", "mweb"], ["web_embedded"]]


# ── YouTube download ───────────────────────────────────────────────────────────

def extract_youtube_video_id(url: str) -> str | None:
    """Returns the 11-character video ID from any common YouTube URL format."""
    match = re.search(r"(?:v=|youtu\.be/|shorts/|embed/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None


def find_downloaded_file(video_id: str) -> str | None:
    """Returns a previously downloaded file for this video, so it isn't downloaded twice."""
    for name in os.listdir(VIDEOS_DIR):
        if f"[{video_id}]" in name and not name.endswith(".part"):
            return os.path.join(VIDEOS_DIR, name)
    return None


def _ytdlp_options() -> dict:
    options = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",  # audio is all we need
        "outtmpl": os.path.join(VIDEOS_DIR, "%(title).100B [%(id)s].%(ext)s"),
        "restrictfilenames": True,
        "windowsfilenames": True,
    }

    # YouTube requires a JavaScript runtime (Deno or Node.js) to unlock its media formats
    for runtime in ("deno", "node"):
        path = shutil.which(runtime) or shutil.which(runtime, path=os.path.expanduser("~/.deno/bin"))
        if path:
            options["js_runtimes"] = {runtime: {"path": path}}
            if importlib.util.find_spec("yt_dlp_ejs") is None:
                options["remote_components"] = ["ejs:github"]  # fetch the challenge solver
            break

    # Optional: route YouTube traffic through another IP if YouTube blocks the server
    if os.getenv("YOUTUBE_PROXY"):
        options["proxy"] = os.getenv("YOUTUBE_PROXY")

    return options


def download_youtube_audio(url: str) -> str:
    """Downloads the audio track of a YouTube video and returns the file path."""
    video_id = extract_youtube_video_id(url)
    if video_id and (existing := find_downloaded_file(video_id)):
        print(f"Using already downloaded file: {existing}")
        return existing

    last_error = None
    for clients in PLAYER_CLIENTS:
        options = _ytdlp_options()
        if clients:
            options["extractor_args"] = {"youtube": {"player_client": clients}}
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                return info["requested_downloads"][0]["filepath"]
        except yt_dlp.utils.DownloadError as e:
            last_error = e
            message = str(e).lower()
            if "private video" in message or "video unavailable" in message or "has been removed" in message:
                break  # retrying with another client won't help
            print(f"Download with {clients or 'default'} client failed, trying the next one...")

    raise RuntimeError(
        "YouTube blocked the download. On a VPS, make sure the PO-token server is running "
        "(see README) or set YOUTUBE_PROXY. You can also download the video yourself and "
        f"use 'Upload file'. Details: {last_error}"
    )


# ── Audio conversion ───────────────────────────────────────────────────────────

def convert_to_wav(input_path: str) -> str:
    """Converts any audio/video file to 16 kHz mono WAV (the format speech models expect)."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    name = re.sub(r'[\\/*?:"<>|]', "", os.path.splitext(os.path.basename(input_path))[0])
    wav_path = os.path.join(AUDIO_DIR, f"{name}_16k.wav")

    # Reuse an earlier conversion if it is newer than the source file
    if os.path.exists(wav_path) and os.path.getmtime(wav_path) >= os.path.getmtime(input_path):
        return wav_path

    audio = AudioSegment.from_file(input_path)
    audio.set_channels(1).set_frame_rate(16000).export(wav_path, format="wav").close()
    return wav_path


def split_into_chunks(wav_path: str, chunk_minutes: int = CHUNK_MINUTES) -> list[str]:
    """Splits long audio into fixed-length chunks so memory use stays low."""
    audio = AudioSegment.from_file(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000
    if len(audio) <= chunk_ms:
        return [wav_path]

    chunks = []
    base = os.path.splitext(wav_path)[0]
    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        piece = audio[start:start + chunk_ms]
        if len(piece) < 1000:  # skip a tiny leftover tail (< 1 second)
            continue
        chunk_path = f"{base}_chunk_{i}.wav"
        piece.export(chunk_path, format="wav").close()
        chunks.append(chunk_path)
    return chunks


def prepare_audio(source: str) -> list[str]:
    """YouTube URL or local file -> list of WAV chunk paths."""
    source = source.strip().strip("'\"")
    if source.startswith(("http://", "https://")):
        print("Downloading audio from YouTube...")
        source = download_youtube_audio(source)

    print("Converting to 16 kHz WAV...")
    wav_path = convert_to_wav(source)
    chunks = split_into_chunks(wav_path)
    print(f"Audio ready - {len(chunks)} chunk(s).")
    return chunks
