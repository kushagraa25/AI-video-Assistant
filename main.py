import os
import sys
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Load environment variables
load_dotenv()

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.pipeline import VideoAssistantPipeline
from backend.rag_engine import ask_question
from backend.audio_processor import list_downloaded_videos, DOWNLOADED_VIDEOS_DIR

def main():
    print("=" * 65)
    print("🎬 AI Video Assistant - Terminal CLI")
    print("=" * 65)

    downloaded = list_downloaded_videos(DOWNLOADED_VIDEOS_DIR)
    if downloaded:
        print(f"\n📁 Videos available on server (`{DOWNLOADED_VIDEOS_DIR}`):")
        for i, item in enumerate(downloaded, start=1):
            print(f"  [{i}] {item['name']} ({item['size_mb']} MB)")
        print()

    prompt = "Enter choice number [1-N], YouTube URL, or local file path: " if downloaded else "Enter YouTube URL or local file path: "
    user_input = input(prompt).strip().strip("'").strip('"')
    if not user_input:
        print("❌ No input provided. Exiting.")
        sys.exit(1)

    if user_input.isdigit() and downloaded:
        idx = int(user_input) - 1
        if 0 <= idx < len(downloaded):
            source = downloaded[idx]["path"]
            print(f"Selected: {downloaded[idx]['name']}")
        else:
            print("❌ Invalid selection number. Exiting.")
            sys.exit(1)
    else:
        source = user_input

    language = input("Language (english / hinglish) [default: english]: ").strip().lower() or "english"

    whisper_model = input("Whisper Model (tiny / base / small) [default: base]: ").strip().lower() or "base"

    print("\n🚀 Initializing AI Video Assistant Pipeline...")
    pipeline = VideoAssistantPipeline(language=language, whisper_model=whisper_model)

    try:
        result = pipeline.run(source)

        print("\n" + "=" * 65)
        print(f"📌 Meeting Title: {result['title']}")
        print("=" * 65)
        print(f"\n📋 Executive Summary:\n{result['summary']}")
        print(f"\n✅ Action Items:\n{result['action_items']}")
        print(f"\n🔑 Key Decisions:\n{result['key_decisions']}")
        print(f"\n❓ Open Questions:\n{result['open_questions']}")
        print("=" * 65)

        print("\n💬 Interactive Chat (Ask anything about the meeting, or type 'exit' to quit)\n")
        rag_chain = result["rag_chain"]

        while True:
            try:
                question = input("You: ").strip()
                if question.lower() in ["exit", "quit", "q"]:
                    print("👋 Goodbye!")
                    break
                if not question:
                    continue

                answer = ask_question(rag_chain, question)
                print(f"\n🤖 Assistant: {answer}\n")
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Exiting...")
                break

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
