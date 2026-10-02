import os
import re
import base64
import yt_dlp
from pydub import AudioSegment

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "data", "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def sanitize_filename(name: str) -> str:
    """Sanitize a string to be a safe filename across operating systems."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def get_cookie_file() -> str | None:
    """
    Locates or generates a cookies.txt file for authenticated yt-dlp requests.
    Supports:
    1. YOUTUBE_COOKIES_FILE env var (path to cookies file)
    2. YOUTUBE_COOKIES / YTDLP_COOKIES env var (raw Netscape or base64 text)
    3. cookies.txt file in project root or downloads directory
    """
    # 1. Custom path via env
    custom_path = os.getenv("YOUTUBE_COOKIES_FILE")
    if custom_path and os.path.exists(custom_path):
        return custom_path

    # 2. Raw content in env var (convenient for cloud hosts like Render)
    raw_cookies = os.getenv("YOUTUBE_COOKIES") or os.getenv("YTDLP_COOKIES")
    if raw_cookies and raw_cookies.strip():
        cookie_text = raw_cookies.strip()
        try:
            import base64
            decoded = base64.b64decode(cookie_text).decode("utf-8")
            if "# Netscape" in decoded or "\t" in decoded:
                cookie_text = decoded
        except Exception:
            pass

        cookie_path = os.path.join(DOWNLOAD_DIR, "yt_cookies.txt")
        with open(cookie_path, "w", encoding="utf-8") as f:
            f.write(cookie_text)
        return cookie_path

    # 3. Local file in project root or downloads directory
    candidates = [
        os.path.join(BASE_DIR, "cookies.txt"),
        os.path.join(DOWNLOAD_DIR, "cookies.txt"),
        os.path.join(BASE_DIR, "youtube_cookies.txt"),
    ]
    for candidate in candidates:
        if os.path.exists(candidate) and os.path.getsize(candidate) > 0:
            return candidate

    return None

def download_youtube_audio(url: str) -> str:
    """
    Downloads audio from a YouTube URL and converts it to a standard 16kHz mono WAV file.
    Uses video ID in the filename template to avoid invalid Windows path characters.
    Employs mobile player clients (android, ios, mweb) and cookie handling to bypass
    datacenter IP bot detection on cloud hosting platforms like Render.
    """
    output_template = os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s")
    cookie_file = get_cookie_file()

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "windowsfilenames": True,
        "restrictfilenames": True,
        "quiet": True,
        "no_warnings": False,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios", "tv", "mweb", "web"],
                "player_skip": ["configs", "webpage"],
            }
        },
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/128.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
    }

    if cookie_file:
        ydl_opts["cookiefile"] = cookie_file

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info.get("id", "audio")
            raw_wav_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.wav")
            if not os.path.exists(raw_wav_path):
                raw_wav_path = os.path.splitext(ydl.prepare_filename(info))[0] + ".wav"
    except Exception as e:
        err_msg = str(e)
        if any(term in err_msg.lower() for term in ["sign in to confirm", "bot", "429", "too many requests", "unavailable"]):
            raise RuntimeError(
                "YouTube has blocked audio download on this server IP (bot verification / rate limit).\n\n"
                "How to solve this on Render:\n"
                "1. Direct File Upload (Recommended): Use the 'Upload File' tab in the left sidebar to upload your audio/video file directly.\n"
                "2. YouTube Cookies: Export your cookies using a browser extension (e.g. 'Get cookies.txt LOCALLY') and add the content as a YOUTUBE_COOKIES environment variable in Render."
            ) from e
        raise e

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
