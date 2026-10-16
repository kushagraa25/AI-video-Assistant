"""
Streamlit web UI. Run with:  streamlit run app.py

Left column:  choose a YouTube link or file, the language and the Whisper model.
Right column: title, summary, action items, decisions, open questions,
              transcript, and a chat that answers questions about the recording.
"""

import html
import os
import re

import streamlit as st
from dotenv import load_dotenv

# Read API keys from .env (next to this file) before the backend is imported
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from backend.audio_processor import AUDIO_DIR
from backend.pipeline import run_pipeline
from backend.rag_engine import ask_question
from styles import CUSTOM_CSS

# The PDF report is optional: if its packages are missing, only the download button is affected
try:
    from backend.report import build_pdf_report
    PDF_ERROR = None
except ImportError as e:
    build_pdf_report = None
    PDF_ERROR = f"PDF download unavailable ({e}). Run: pip install -r requirements.txt"

st.set_page_config(
    page_title="Meeting Assistant",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ── Options ────────────────────────────────────────────────────────────────────

LANGUAGES = {"English": "english", "Hinglish (Hindi + English)": "hinglish"}
WHISPER_MODELS = {"Base: balanced": "base", "Tiny: fastest": "tiny", "Small: most accurate": "small"}

# Pipeline steps, in the order they run (keys match backend/pipeline.py)
STEPS = [
    ("audio", "Prepare audio"),
    ("transcript", "Transcribe speech"),
    ("title", "Write a title"),
    ("summary", "Summarize"),
    ("extract", "Find action items and decisions"),
    ("rag", "Index transcript for chat"),
]
STATUS_MESSAGES = {
    "audio": "Downloading and preparing the audio...",
    "transcript": "Transcribing speech. Longer recordings take a few minutes.",
    "title": "Writing the summary, insights and chat index...",
}

for key, default in {"result": None, "meta": {}, "chat_history": [], "pipeline_steps": {},
                     "report_pdf": None}.items():
    st.session_state.setdefault(key, default)


# ── Helpers ────────────────────────────────────────────────────────────────────

def steps_html(states: dict) -> str:
    """Numbered progress list; each step is pending, active, done or error."""
    rows = []
    for number, (key, label) in enumerate(STEPS, start=1):
        state = states.get(key, "pending")
        marker = {"done": "✓", "error": "!"}.get(state, str(number))
        rows.append(
            f'<li class="step step-{state}"><span class="step-marker">{marker}</span>{label}</li>'
        )
    return f'<ol class="steps">{"".join(rows)}</ol>'


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "meeting"


# ── Header ─────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <div class="app-header">
        <p class="brand">Meeting <span>Assistant</span></p>
        <p class="tagline">Turn a recording or a YouTube link into a summary, action items
        and a transcript you can ask questions about.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([1, 2.4], gap="large")

# ── Left column: input ─────────────────────────────────────────────────────────

with left:
    st.markdown('<p class="section-label">Source</p>', unsafe_allow_html=True)
    source_mode = st.segmented_control(
        "Source",
        ["YouTube link", "Upload file"],
        default="YouTube link",
        label_visibility="collapsed",
    ) or "YouTube link"  # clicking the selected option again deselects it

    source = ""
    if source_mode == "YouTube link":
        source = st.text_input(
            "YouTube link",
            placeholder="https://youtube.com/watch?v=...",
            label_visibility="collapsed",
        ).strip()
    else:
        uploaded_file = st.file_uploader(
            "Audio or video file",
            type=None,
            label_visibility="collapsed",
        )
        if uploaded_file is not None:
            safe_name = os.path.basename(uploaded_file.name)
            save_path = os.path.join(AUDIO_DIR, safe_name)
            with open(save_path, "wb") as file_handle:
                file_handle.write(uploaded_file.getbuffer())
            source = save_path

    st.markdown('<p class="section-label" style="margin-top:1.1rem">Settings</p>', unsafe_allow_html=True)
    language_label = st.selectbox("Spoken language", list(LANGUAGES))
    language = LANGUAGES[language_label]

    model_label = st.selectbox(
        "Whisper model",
        list(WHISPER_MODELS),
        disabled=language == "hinglish",
        help="Used for English. Hinglish is transcribed by Sarvam AI instead.",
    )
    whisper_model = WHISPER_MODELS[model_label]

    run_clicked = st.button("Analyse", type="primary", width="stretch")

    steps_box = st.empty()
    if st.session_state.pipeline_steps:
        steps_box.markdown(steps_html(st.session_state.pipeline_steps), unsafe_allow_html=True)

# ── Right column: run, results and chat ────────────────────────────────────────

with right:
    status_box = st.empty()

    if run_clicked:
        if not source:
            status_box.warning(
                "Paste a YouTube link first." if source_mode == "YouTube link" else "Choose a file to upload first."
            )
        else:
            st.session_state.result = None
            st.session_state.report_pdf = None
            st.session_state.chat_history = []
            st.session_state.pipeline_steps = {}

            def on_step(step: str, state: str):
                # Called by the pipeline as each step starts/finishes: redraw the progress list
                st.session_state.pipeline_steps[step] = state
                steps_box.markdown(steps_html(st.session_state.pipeline_steps), unsafe_allow_html=True)
                if state == "active" and step in STATUS_MESSAGES:
                    status_box.info(STATUS_MESSAGES[step])

            try:
                result = run_pipeline(source, language=language, whisper_model=whisper_model, on_step=on_step)
                st.session_state.result = result
                st.session_state.meta = {
                    "source": "YouTube" if source_mode == "YouTube link" else os.path.basename(source),
                    "engine": "Sarvam AI" if language == "hinglish" else f"Whisper {whisper_model}",
                    "words": len(result["transcript"].split()),
                }
                st.rerun()
            except Exception as e:
                # Mark the step that was running as failed so it's clear where it stopped
                for step, state in st.session_state.pipeline_steps.items():
                    if state == "active":
                        st.session_state.pipeline_steps[step] = "error"
                steps_box.markdown(steps_html(st.session_state.pipeline_steps), unsafe_allow_html=True)
                status_box.error(f"Something went wrong: {e}")

    result = st.session_state.result
    if result:
        meta = st.session_state.meta

        title_col, download_col = st.columns([3, 1], vertical_alignment="bottom")
        with title_col:
            st.markdown(
                f'<p class="result-meta">{html.escape(meta.get("source", ""))} · '
                f'{html.escape(meta.get("engine", ""))} · {meta.get("words", 0):,} words</p>'
                f'<h1 class="result-title">{html.escape(result["title"])}</h1>',
                unsafe_allow_html=True,
            )
        with download_col:
            # Build the PDF once per analysis (not on every chat message rerun)
            if build_pdf_report is None:
                st.caption(PDF_ERROR)
            elif st.session_state.report_pdf is None:
                try:
                    st.session_state.report_pdf = build_pdf_report(result, meta)
                except Exception as e:
                    st.session_state.report_pdf = b""
                    print(f"PDF report failed: {e}")
            if build_pdf_report is None:
                pass  # the reason is already shown above
            elif st.session_state.report_pdf:
                st.download_button(
                    "Download PDF",
                    data=st.session_state.report_pdf,
                    file_name=f"{slugify(result['title'])}.pdf",
                    mime="application/pdf",
                    width="stretch",
                )
            else:
                st.caption("The PDF report couldn't be created for this result.")

        summary_tab, actions_tab, decisions_tab, questions_tab, transcript_tab = st.tabs(
            ["Summary", "Action items", "Decisions", "Open questions", "Transcript"]
        )
        with summary_tab:
            st.markdown(result["summary"])
        with actions_tab:
            st.markdown(result["action_items"])
        with decisions_tab:
            st.markdown(result["key_decisions"])
        with questions_tab:
            st.markdown(result["open_questions"])
        with transcript_tab:
            with st.container(height=420, border=True):
                st.text(result["transcript"])

        # ── Chat ───────────────────────────────────────────────────────────────
        st.markdown(
            '<h2 class="section-title">Ask about this recording</h2>'
            '<p class="section-hint">Answers come only from the transcript. If something '
            "wasn't said, the assistant will tell you.</p>",
            unsafe_allow_html=True,
        )

        messages = st.container()
        for message in st.session_state.chat_history:
            with messages.chat_message(message["role"]):
                st.markdown(message["content"])

        question = st.chat_input("e.g. What deadlines were agreed?")
        if question:
            st.session_state.chat_history.append({"role": "user", "content": question})
            with messages.chat_message("user"):
                st.markdown(question)
            with messages.chat_message("assistant"):
                with st.spinner("Searching the transcript..."):
                    answer = ask_question(result["rag_chain"], question)
                st.markdown(answer)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})

        if st.session_state.chat_history:
            if st.button("Clear conversation"):
                st.session_state.chat_history = []
                st.rerun()

    elif not run_clicked:
        st.markdown(
            """
            <div class="empty">
                <h2>Nothing analysed yet</h2>
                Pick a source on the left and press <strong>Analyse</strong>. You'll get:
                <ol>
                    <li><strong>A summary</strong> of what was discussed</li>
                    <li><strong>Action items, decisions and open questions</strong>, pulled out separately</li>
                    <li><strong>The full transcript</strong>, plus a chat to ask questions about it</li>
                </ol>
                <p class="note">English is transcribed on this server with Whisper. Hinglish goes to
                Sarvam AI and comes back translated to English.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
