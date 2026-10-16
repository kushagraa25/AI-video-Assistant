"""
Cookie Manager module for AI Video Assistant.
Handles reading, writing, parsing, and validating yt-dlp Netscape cookie files.
"""

import os
import re
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

# Base directory is the project root (parent of backend/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_COOKIE_FILENAME = "cookies.txt"
ALTERNATIVE_COOKIE_FILENAMES = ["cookies.txt", "cookie.txt", "coociee.txt"]

NETSCAPE_HEADER = (
    "# Netscape HTTP Cookie File\n"
    "# https://curl.se/docs/http-cookies.html\n"
    "# This file was updated by the AI Video Assistant Cookie Manager.\n\n"
)


def get_cookie_target_path() -> str:
    """
    Returns the path where the cookie file should be written or read.
    Respects YOUTUBE_COOKIES_FILE from environment, otherwise defaults to cookies.txt in BASE_DIR.
    """
    env_path = os.getenv("YOUTUBE_COOKIES_FILE", "").strip()
    if env_path:
        if not os.path.isabs(env_path):
            return os.path.join(BASE_DIR, env_path)
        return env_path

    # Check if any standard cookie file already exists
    for fname in ALTERNATIVE_COOKIE_FILENAMES:
        p = os.path.join(BASE_DIR, fname)
        if os.path.isfile(p):
            return p

    return os.path.join(BASE_DIR, DEFAULT_COOKIE_FILENAME)


def get_active_cookie_file() -> Optional[str]:
    """
    Returns the readable cookie file path if one exists with non-zero size, else None.
    """
    env_path = os.getenv("YOUTUBE_COOKIES_FILE", "").strip()
    if env_path:
        if not os.path.isabs(env_path):
            env_path = os.path.join(BASE_DIR, env_path)
        if os.path.isfile(env_path) and os.path.getsize(env_path) > 0:
            return env_path
        return None

    for fname in ALTERNATIVE_COOKIE_FILENAMES:
        p = os.path.join(BASE_DIR, fname)
        if os.path.isfile(p) and os.path.getsize(p) > 0:
            return p

    return None


def parse_cookie_lines(raw_content: str) -> List[Dict[str, Any]]:
    """
    Parses Netscape-formatted cookie lines into structured dictionaries.
    Netscape format: domain, flag, path, secure, expiry, name, value
    """
    cookies = []
    lines = raw_content.splitlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Handle #HttpOnly_ prefix
        is_http_only = False
        if line.startswith("#HttpOnly_"):
            is_http_only = True
            line = line[len("#HttpOnly_"):]
        elif line.startswith("#"):
            continue

        parts = line.split("\t")
        if len(parts) >= 7:
            domain, flag, path, secure, expiry, name, value = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], parts[6]
            
            expiry_str = "Session / Unknown"
            try:
                exp_ts = int(expiry)
                if exp_ts > 0:
                    expiry_str = datetime.fromtimestamp(exp_ts).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass

            cookies.append({
                "domain": domain,
                "include_subdomains": flag.upper() == "TRUE",
                "path": path,
                "secure": secure.upper() == "TRUE",
                "expiry_timestamp": expiry,
                "expiry": expiry_str,
                "name": name,
                "value_masked": value[:4] + "..." + value[-4:] if len(value) > 10 else "***",
                "http_only": is_http_only,
                "is_youtube": "youtube.com" in domain.lower() or "google.com" in domain.lower(),
            })

    return cookies


def get_cookie_status() -> Dict[str, Any]:
    """
    Returns full status metadata about the current cookies file.
    """
    target_path = get_cookie_target_path()
    active_path = get_active_cookie_file()

    status = {
        "exists": False,
        "target_path": target_path,
        "active_path": active_path,
        "size_bytes": 0,
        "size_kb": 0.0,
        "modified_time": None,
        "total_cookies": 0,
        "youtube_cookies": 0,
        "sample_cookies": [],
        "content": "",
        "key_cookies_present": [],
    }

    if active_path and os.path.isfile(active_path):
        try:
            stat = os.stat(active_path)
            status["exists"] = True
            status["size_bytes"] = stat.st_size
            status["size_kb"] = round(stat.st_size / 1024, 2)
            status["modified_time"] = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

            with open(active_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            status["content"] = content
            parsed = parse_cookie_lines(content)
            status["total_cookies"] = len(parsed)
            status["youtube_cookies"] = sum(1 for c in parsed if c["is_youtube"])
            status["sample_cookies"] = parsed[:15]

            # Check for YouTube session cookies commonly needed to bypass bot checks
            key_names = ["VISITOR_INFO1_LIVE", "LOGIN_INFO", "SID", "HSID", "SSID", "__Secure-1PSID", "__Secure-3PSID", "PREF"]
            detected_keys = [c["name"] for c in parsed if c["name"] in key_names]
            status["key_cookies_present"] = list(set(detected_keys))
        except Exception as e:
            status["error"] = str(e)

    return status


def save_cookie_content(raw_content: str) -> Tuple[bool, str, int]:
    """
    Validates, normalizes, and writes cookie content to cookies.txt (and mirrors to cookie.txt).
    Returns (success, message, cookie_count).
    """
    if not raw_content or not raw_content.strip():
        return False, "Cookie content cannot be empty.", 0

    content = raw_content.strip()

    # Normalize line endings to LF
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    # Ensure Netscape header is present
    if not content.startswith("# Netscape HTTP Cookie File"):
        content = NETSCAPE_HEADER + content

    parsed = parse_cookie_lines(content)
    if not parsed:
        return False, "No valid Netscape cookie entries found in the provided text. Please ensure the cookies are in Netscape tab-separated format.", 0

    target_path = get_cookie_target_path()
    try:
        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
        with open(target_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
            f.write("\n")

        # Restrict permissions on Unix-like OS if supported
        try:
            if hasattr(os, "chmod"):
                os.chmod(target_path, 0o600)
        except Exception:
            pass

        # Also write / sync to cookie.txt and cookies.txt in BASE_DIR so both are always valid
        mirror_paths = [
            os.path.join(BASE_DIR, "cookies.txt"),
            os.path.join(BASE_DIR, "cookie.txt"),
        ]
        for m_path in mirror_paths:
            if os.path.abspath(m_path) != os.path.abspath(target_path):
                try:
                    with open(m_path, "w", encoding="utf-8", newline="\n") as mf:
                        mf.write(content)
                        mf.write("\n")
                    if hasattr(os, "chmod"):
                        os.chmod(m_path, 0o600)
                except Exception:
                    pass

        yt_count = sum(1 for c in parsed if c["is_youtube"])
        msg = f"Successfully saved {len(parsed)} cookies ({yt_count} YouTube/Google) to `{os.path.basename(target_path)}`!"
        return True, msg, len(parsed)

    except Exception as e:
        return False, f"Failed to save cookie file: {str(e)}", 0


def delete_cookie_files() -> Tuple[bool, str]:
    """
    Deletes the configured cookie file as well as cookies.txt and cookie.txt in BASE_DIR.
    """
    deleted = []
    candidates = set()

    target = get_cookie_target_path()
    candidates.add(target)
    for fname in ALTERNATIVE_COOKIE_FILENAMES:
        candidates.add(os.path.join(BASE_DIR, fname))

    for p in candidates:
        if os.path.isfile(p):
            try:
                os.remove(p)
                deleted.append(os.path.basename(p))
            except Exception as e:
                return False, f"Error deleting {p}: {str(e)}"

    if deleted:
        return True, f"Removed cookie files: {', '.join(deleted)}"
    return True, "No cookie files were found to delete."


def test_youtube_connectivity(test_url: str = "https://www.youtube.com/watch?v=jNQXAC9IVRw") -> Tuple[bool, str]:
    """
    Performs a lightweight yt-dlp metadata extraction using the active cookie file
    to verify that YouTube does not reject the session.
    """
    try:
        import yt_dlp
    except ImportError:
        return False, "yt-dlp is not installed in the environment."

    cookie_file = get_active_cookie_file()
    if not cookie_file:
        return False, "No active cookie file found to test with."

    ydl_opts = {
        "cookiefile": cookie_file,
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": "in_playlist",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
            title = info.get("title", "Video metadata extracted")
            uploader = info.get("uploader", "YouTube")
            return True, f"✅ Connection Verified! Title: '{title}' (by {uploader}). Cookies are working!"
    except Exception as e:
        err_msg = str(e)
        return False, f"❌ YouTube rejected the request: {err_msg}"
