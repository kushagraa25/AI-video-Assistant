"""
Unit and integration test script for AI Video Assistant modules.
"""

import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from dotenv import load_dotenv
load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def test_imports():
    print("Testing imports...")
    from backend.audio_processor import process_input
    from backend.transcriber import transcribe_all
    from backend.summarizer import summarize, generate_title, extract_meeting_insights
    from backend.rag_engine import build_rag_chain, ask_question
    from backend.pipeline import VideoAssistantPipeline
    print("[OK] All backend modules imported successfully!")

def test_nlp_on_sample_text():
    print("\nTesting NLP summarization and extraction on sample transcript...")
    from backend.summarizer import summarize, generate_title, extract_meeting_insights

    sample_transcript = (
        "Alice: Welcome everyone. Today we are reviewing the Q3 launch plan. "
        "Bob: The backend API is ready and deployed to staging. We need to complete security testing. "
        "Alice: Bob, please finalize security audits by Friday. "
        "Charlie: I will prepare the user documentation by next Wednesday. "
        "Alice: Agreed. We decided to target launch date for October 15th. Any remaining questions? "
        "Bob: Who is handling the payment gateway integration sign-off?"
    )

    title = generate_title(sample_transcript)
    print(f"Title: {title}")

    summary = summarize(sample_transcript)
    print(f"Summary:\n{summary}")

    insights = extract_meeting_insights(sample_transcript)
    print(f"\nAction Items:\n{insights['action_items']}")
    print(f"\nKey Decisions:\n{insights['key_decisions']}")
    print(f"\nOpen Questions:\n{insights['open_questions']}")
    print("[OK] NLP test completed successfully!")

def test_downloaded_videos_folder():
    print("\nTesting downloaded videos folder connectivity...")
    from backend.audio_processor import (
        DOWNLOADED_VIDEOS_DIR,
        list_downloaded_videos,
        extract_youtube_video_id,
        find_existing_downloaded_video,
    )
    assert os.path.isdir(DOWNLOADED_VIDEOS_DIR), "DOWNLOADED_VIDEOS_DIR must exist"
    videos = list_downloaded_videos(DOWNLOADED_VIDEOS_DIR)
    print(f"Found {len(videos)} video(s) in {DOWNLOADED_VIDEOS_DIR}:")
    for v in videos:
        print(f"  - {v['name']} ({v['size_mb']} MB)")
    
    # Test video ID extraction
    sample_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    vid = extract_youtube_video_id(sample_url)
    assert vid == "jNQXAC9IVRw", f"Expected jNQXAC9IVRw but got {vid}"
    print(f"[OK] Extracted video ID: {vid}")

    existing = find_existing_downloaded_video(vid, DOWNLOADED_VIDEOS_DIR)
    if existing:
        print(f"[OK] Found existing downloaded video on server: {existing}")
    print("[OK] Downloaded videos folder connectivity verified!")

if __name__ == "__main__":
    test_imports()
    test_nlp_on_sample_text()
    test_downloaded_videos_folder()
