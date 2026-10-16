"""
Offline unit tests (no API keys or internet needed).
Run with:  python -m unittest discover tests
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydub import AudioSegment

from backend import audio_processor, pipeline
from backend.summarizer import clean_title


class TestAudioProcessor(unittest.TestCase):

    def test_extract_youtube_video_id(self):
        for url in [
            "https://www.youtube.com/watch?v=jNQXAC9IVRw",
            "https://youtu.be/jNQXAC9IVRw?si=abc",
            "https://www.youtube.com/shorts/jNQXAC9IVRw",
            "https://www.youtube.com/embed/jNQXAC9IVRw",
        ]:
            self.assertEqual(audio_processor.extract_youtube_video_id(url), "jNQXAC9IVRw", url)
        self.assertIsNone(audio_processor.extract_youtube_video_id("https://example.com/video"))

    def test_convert_and_split_audio(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(audio_processor, "AUDIO_DIR", tmp):
            source = os.path.join(tmp, "meeting.mp3")
            AudioSegment.silent(duration=150_000, frame_rate=44100).export(source, format="mp3").close()

            wav_path = audio_processor.convert_to_wav(source)
            wav = AudioSegment.from_file(wav_path)
            self.assertEqual((wav.frame_rate, wav.channels), (16000, 1))

            # 2.5 minutes split into 1-minute chunks -> 3 chunks
            chunks = audio_processor.split_into_chunks(wav_path, chunk_minutes=1)
            self.assertEqual(len(chunks), 3)

            # Short audio stays a single chunk
            self.assertEqual(audio_processor.split_into_chunks(wav_path, chunk_minutes=10), [wav_path])

    def test_find_downloaded_file(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(audio_processor, "VIDEOS_DIR", tmp):
            open(os.path.join(tmp, "Me_at_the_zoo [jNQXAC9IVRw].m4a"), "w").close()
            open(os.path.join(tmp, "Other [aaaaaaaaaaa].m4a.part"), "w").close()
            self.assertTrue(audio_processor.find_downloaded_file("jNQXAC9IVRw").endswith(".m4a"))
            self.assertIsNone(audio_processor.find_downloaded_file("aaaaaaaaaaa"))


class TestSummarizer(unittest.TestCase):

    def test_clean_title(self):
        self.assertEqual(clean_title('**"Build Motivation Through Discipline"**'), "Build Motivation Through Discipline")
        self.assertEqual(clean_title("# Q3 Launch Plan\nextra line"), "Q3 Launch Plan")
        self.assertEqual(clean_title(""), "Untitled Meeting")


class TestReport(unittest.TestCase):

    def test_pdf_report_with_unicode_and_lists(self):
        from backend.report import build_pdf_report
        result = {
            "title": "Q3 “Launch” Review – ₹500 budget",
            "summary": "Here’s the plan:\n\n- **Launch** on Oct 15\n  - nested item\n- Second *point*",
            "action_items": "1. **Audit**\n   - Owner: Bob\n2. Docs",
            "key_decisions": "### Decided\n\nShip it.",
            "open_questions": "No open questions found.",
            "transcript": "Alice: hello. Bob: hi. " * 300,  # long enough for several pages
        }
        pdf = build_pdf_report(result, {"source": "YouTube", "engine": "Whisper base", "words": 900})
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 5000)

    def test_pdf_report_survives_odd_markdown(self):
        from backend.report import build_pdf_report
        result = {key: "<div>unclosed <b>html | table |\n|---|" for key in
                  ("title", "summary", "action_items", "key_decisions", "open_questions", "transcript")}
        self.assertTrue(build_pdf_report(result).startswith(b"%PDF"))


class TestPipeline(unittest.TestCase):

    def test_runs_all_steps_and_reports_progress(self):
        fakes = {
            "prepare_audio": lambda source: ["chunk.wav"],
            "transcribe_all": lambda chunks, language, model_name: "hello world",
            "generate_title": lambda t: "Title",
            "summarize": lambda t: "Summary",
            "extract_action_items": lambda t: "Actions",
            "extract_key_decisions": lambda t: "Decisions",
            "extract_open_questions": lambda t: "Questions",
            "build_rag_chain": lambda t: "rag-chain",
        }
        steps = []
        with patch.multiple(pipeline, **fakes):
            result = pipeline.run_pipeline("video.mp4", on_step=lambda s, status: steps.append((s, status)))

        self.assertEqual(result["title"], "Title")
        self.assertEqual(result["transcript"], "hello world")
        self.assertEqual(result["rag_chain"], "rag-chain")
        self.assertIn(("audio", "done"), steps)
        self.assertIn(("rag", "done"), steps)

    def test_empty_transcript_raises(self):
        with patch.multiple(pipeline, prepare_audio=lambda s: ["c.wav"],
                            transcribe_all=lambda c, language, model_name: ""):
            with self.assertRaises(ValueError):
                pipeline.run_pipeline("video.mp4")


if __name__ == "__main__":
    unittest.main()
