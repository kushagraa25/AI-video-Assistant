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

if __name__ == "__main__":
    test_imports()
    test_nlp_on_sample_text()
