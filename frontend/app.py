import os
import sys
import time
import torch
import streamlit as st

# Prevent PyTorch from overloading CPU cores
try:
    torch.set_num_threads(min(4, os.cpu_count() or 1))
except Exception:
    pass

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from frontend.styles import CUSTOM_CSS
from backend.pipeline import VideoAssistantPipeline
from backend.rag_engine import ask_question
from backend.audio_processor import (
    list_downloaded_videos,
    download_youtube_video,
    DOWNLOADED_VIDEOS_DIR,
    get_cookie_file,
    save_cookie_content,
)

# ─── Page Configuration ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Meeting Assistant",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Apply custom UI styling
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ─── Session State Initialization ──────────────────────────────────────────────
for key, default in {
    "result": None,
    "chat_history": [],
    "pipeline_done": False,
    "pipeline_steps": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

def get_step_css(key: str) -> str:
    status = st.session_state.pipeline_steps.get(key, "pending")
    if status == "active": return "dot-active"
    if status == "done":   return "dot-done"
    return "dot-pending"

def render_step_indicator(label: str, key: str, icon: str):
    css_class = get_step_css(key)
    st.markdown(f"""
    <div class="status-bar">
        <div class="status-dot {css_class}"></div>
        <span>{icon} {label}</span>
    </div>""", unsafe_allow_html=True)

# ─── Layout: Left Control Panel & Right Results Panel ──────────────────────────
left_col, right_col = st.columns([1, 3], gap="large")

# ══════════════════════════════════════════════════════
#  LEFT PANEL: Input & Pipeline Progress
# ══════════════════════════════════════════════════════
with left_col:
    st.markdown("""
    <div class="left-panel">
        <div class="panel-logo">🎬 AI Meeting<br><span class="accent">Assistant</span></div>
        <div class="panel-sub">Meeting Intelligence &amp; RAG</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    with st.container():
        st.markdown('<span class="panel-label">📎 Video / Audio Source</span>', unsafe_allow_html=True)
        source_mode = st.radio(
            "Source Mode",
            ["📁 Server Videos", "🔗 YouTube URL", "📤 Upload File"],
            horizontal=True,
            label_visibility="collapsed",
        )

        source = ""
        if source_mode == "📁 Server Videos":
            downloaded_files = list_downloaded_videos(DOWNLOADED_VIDEOS_DIR)
            if downloaded_files:
                video_names = [f"{item['name']} ({item['size_mb']} MB)" for item in downloaded_files]
                selected_idx = st.selectbox(
                    "Select Video from Server Folder",
                    options=range(len(downloaded_files)),
                    format_func=lambda i: video_names[i],
                    label_visibility="collapsed",
                )
                chosen = downloaded_files[selected_idx]
                source = chosen["path"]
                st.caption(f"📁 **Selected:** `{chosen['name']}` ({chosen['size_mb']} MB)")
                with st.expander("▶️ Preview Media", expanded=False):
                    if chosen["name"].lower().endswith((".mp4", ".webm", ".mov", ".mkv", ".m4v")):
                        st.video(chosen["path"])
                    else:
                        st.audio(chosen["path"])
            else:
                st.warning("⚠️ No videos in `downloaded_videos/` yet.")
                st.caption(f"Server folder: `{DOWNLOADED_VIDEOS_DIR}`")

            c_btn1, c_btn2 = st.columns([1, 1])
            with c_btn1:
                if st.button("🔄 Refresh", use_container_width=True):
                    st.rerun()
            with c_btn2:
                with st.popover("ℹ️ Folder Info"):
                    st.markdown(f"**Path on Server:**\n`{DOWNLOADED_VIDEOS_DIR}`")
                    st.markdown("Drop or download any video files (`.mp4`, `.webm`, `.mkv`, etc.) directly into this folder on your server.")

        elif source_mode == "🔗 YouTube URL":
            youtube_url = st.text_input(
                "source_input",
                placeholder="https://youtube.com/watch?v=...",
                label_visibility="collapsed",
            )
            source = youtube_url.strip() if youtube_url else ""
            st.caption("📥 YouTube videos are downloaded to `downloaded_videos/` on the server and reused.")

            if st.button("⬇️ Download Video to Server", use_container_width=True):
                if not source:
                    st.warning("Please enter a YouTube URL first.")
                else:
                    with st.spinner("Downloading video to server folder..."):
                        try:
                            saved_path = download_youtube_video(source)
                            st.success(f"✅ Saved on server: `{os.path.basename(saved_path)}`")
                            time.sleep(1)
                            st.rerun()
                        except Exception as dl_err:
                            st.error(f"Download failed: {dl_err}")

            # YouTube Cookies / Bot Bypass Tool
            active_cookie = get_cookie_file()
            with st.expander("🍪 YouTube Cookies (Bypass Server IP Block)", expanded=not bool(active_cookie)):
                if active_cookie:
                    st.success(f"✅ Cookies active (`{os.path.basename(active_cookie)}`)")
                else:
                    st.warning("⚠️ No cookies loaded. Cloud/VPS IPs are blocked by YouTube without cookies.")

                c_tab1, c_tab2 = st.tabs(["Upload cookies.txt", "Paste Cookies"])
                with c_tab1:
                    uploaded_c = st.file_uploader("Upload cookies.txt", type=["txt"], key="ui_cookie_file", label_visibility="collapsed")
                    if uploaded_c is not None:
                        save_cookie_content(uploaded_c.getvalue().decode("utf-8", errors="ignore"))
                        st.success("✅ cookies.txt saved to server!")
                        time.sleep(0.5)
                        st.rerun()

                with c_tab2:
                    pasted_c = st.text_area("Paste Netscape Cookie Content:", height=70, key="ui_cookie_paste", label_visibility="collapsed", placeholder="# Netscape HTTP Cookie File...")
                    if st.button("💾 Save Pasted Cookies", use_container_width=True, key="ui_save_cookie_btn"):
                        if pasted_c.strip():
                            save_cookie_content(pasted_c.strip())
                            st.success("✅ Cookies saved to server!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.warning("Please paste cookie text first.")

                st.caption("💡 **Tip:** Export cookies using Chrome/Firefox extension *'Get cookies.txt LOCALLY'* while logged into YouTube.")

        else:
            uploaded_file = st.file_uploader(
                "Upload audio/video",
                type=["mp3", "mp4", "wav", "m4a", "webm", "ogg", "flac", "aac", "mov", "mkv"],
                label_visibility="collapsed",
            )
            if uploaded_file is not None:
                os.makedirs(DOWNLOADED_VIDEOS_DIR, exist_ok=True)
                save_path = os.path.join(DOWNLOADED_VIDEOS_DIR, uploaded_file.name)
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                source = save_path
                st.caption(f"📁 Saved to `downloaded_videos/` & Ready: `{uploaded_file.name}`")

        st.markdown('<span class="panel-label" style="margin-top:0.75rem;display:block;">🌐 Language</span>', unsafe_allow_html=True)
        language = st.selectbox("lang", ["english", "hinglish"], index=0, label_visibility="collapsed")

        st.markdown('<span class="panel-label" style="margin-top:0.75rem;display:block;">⚡ Model Precision</span>', unsafe_allow_html=True)
        model_choice = st.selectbox(
            "speed",
            ["Fast (base) - Recommended", "Ultra-fast (tiny)", "Accurate (small)"],
            index=0,
            label_visibility="collapsed",
        )
        speed_map = {
            "Fast (base) - Recommended": "base",
            "Ultra-fast (tiny)": "tiny",
            "Accurate (small)": "small"
        }
        selected_whisper_model = speed_map[model_choice]

        st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
        run_btn = st.button("⚡ Analyse Meeting", use_container_width=True)

    # Pipeline live progress indicator
    if st.session_state.pipeline_done or st.session_state.pipeline_steps:
        st.markdown("<hr style='margin:1rem 0'>", unsafe_allow_html=True)
        st.markdown('<span class="badge badge-green">Pipeline Steps</span>', unsafe_allow_html=True)
        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
        steps_meta = [
            ("audio",      "🔊", "Audio Acquisition"),
            ("transcript", "📝", "ASR Transcription"),
            ("title",      "🏷️", "Title Generation"),
            ("summary",    "📋", "Map-Reduce Summary"),
            ("extract",    "🔍", "Insights Extraction"),
            ("rag",        "🧠", "RAG Vector Store"),
        ]
        for step_key, icon, label in steps_meta:
            render_step_indicator(label, step_key, icon)

# ══════════════════════════════════════════════════════
#  RIGHT PANEL: Results Dashboard & Interactive Chat
# ══════════════════════════════════════════════════════
with right_col:
    st.markdown("""
    <div style="padding:0.25rem 0 0.5rem 0;">
        <div class="hero-title">AI Meeting <span class="accent">Assistant</span></div>
        <div class="hero-sub">Transcribe · Summarise · Extract Action Items · Chat with RAG</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # ── Pipeline Execution ──────────────────────────────────────────────────
    if run_btn:
        if not source or not source.strip():
            if "YouTube" in source_mode:
                st.error("Please provide a valid YouTube URL.")
            elif "Server" in source_mode:
                st.error("Please select a video from the server folder or place video files in 'downloaded_videos/'.")
            else:
                st.error("Please upload an audio or video file.")
        else:
            st.session_state.pipeline_done = False
            st.session_state.result = None
            st.session_state.chat_history = []
            st.session_state.pipeline_steps = {}

            progress_placeholder = st.empty()

            def ui_callback(step_key: str, status: str):
                st.session_state.pipeline_steps[step_key] = status

            try:
                progress_placeholder.info("⚙️ Step 1/3: Ingesting and preparing audio...")
                pipeline = VideoAssistantPipeline(
                    language=language,
                    whisper_model=selected_whisper_model,
                )

                engine_name = "Sarvam AI" if language == "hinglish" else f"Whisper ({selected_whisper_model})"
                progress_placeholder.info(f"⚙️ Running pipeline with {engine_name}...")

                result = pipeline.run(source.strip(), progress_callback=ui_callback)

                st.session_state.result = result
                st.session_state.pipeline_done = True
                progress_placeholder.success("✅ Analysis complete!")
                time.sleep(0.5)
                progress_placeholder.empty()
                st.rerun()

            except Exception as e:
                for k in ["audio", "transcript", "title", "summary", "extract", "rag"]:
                    if st.session_state.pipeline_steps.get(k) == "active":
                        st.session_state.pipeline_steps[k] = "pending"
                progress_placeholder.error(f"❌ Error during processing: {e}")

    # ── Results Presentation ────────────────────────────────────────────────
    if st.session_state.result:
        r = st.session_state.result

        # Title Card
        st.markdown(f"""
        <div class="card" style="border-left: 4px solid var(--accent);">
            <div class="card-title">📌 Session Title</div>
            <div style="font-family:'Lora',serif;font-size:1.35rem;font-weight:600;color:var(--text);line-height:1.4;">
                {r['title']}
            </div>
        </div>""", unsafe_allow_html=True)

        # Summary & Transcript
        col1, col2 = st.columns([3, 2], gap="medium")
        with col1:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">📋 Executive Summary</div>
                <div class="card-content">{r['summary']}</div>
            </div>""", unsafe_allow_html=True)

        with col2:
            with st.expander("📝 Full Transcript", expanded=False):
                st.markdown(f'<div class="transcript-box">{r["transcript"]}</div>', unsafe_allow_html=True)

        # Action Items, Key Decisions & Open Questions
        c1, c2, c3 = st.columns(3, gap="medium")
        with c1:
            st.markdown(f"""
            <div class="card" style="border-top: 3px solid var(--accent);">
                <div class="card-title">✅ Action Items</div>
                <div class="card-content">{r['action_items']}</div>
            </div>""", unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="card" style="border-top: 3px solid var(--accent-2);">
                <div class="card-title">🔑 Key Decisions</div>
                <div class="card-content">{r['key_decisions']}</div>
            </div>""", unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div class="card" style="border-top: 3px solid var(--border-strong);">
                <div class="card-title">❓ Open Questions</div>
                <div class="card-content">{r['open_questions']}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("---")

        # ── Interactive RAG Chat ─────────────────────────────────────────────
        st.markdown("""
        <div style="font-family:'Lora',serif;font-size:1.2rem;font-weight:600;margin-bottom:0.4rem;color:var(--text);">
            💬 Chat with Meeting (RAG Powered)
        </div>
        <div style="font-size:0.84rem;color:var(--text-muted);margin-bottom:0.9rem;">
            Ask specific questions grounded in the indexed meeting transcript.
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.chat_history:
            chat_html = '<div class="chat-container">'
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    chat_html += f"""
                    <div class="chat-msg" style="align-items:flex-end">
                        <span class="chat-label user-label">You</span>
                        <div class="chat-bubble user-bubble">{msg['content']}</div>
                    </div>"""
                else:
                    chat_html += f"""
                    <div class="chat-msg" style="align-items:flex-start">
                        <span class="chat-label bot-label">🤖 Assistant</span>
                        <div class="chat-bubble bot-bubble">{msg['content']}</div>
                    </div>"""
            chat_html += '</div>'
            st.markdown(chat_html, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="card" style="text-align:center;padding:2rem;border-style:dashed;">
                <div style="font-size:2rem;margin-bottom:0.4rem;">💬</div>
                <div style="font-family:'Lora',serif;font-size:0.95rem;font-weight:600;color:var(--text);">
                    Ask anything about this meeting
                </div>
                <div style="color:var(--text-muted);font-size:0.82rem;">
                    Answers are strictly retrieved from the transcript embeddings.
                </div>
            </div>""", unsafe_allow_html=True)

        with st.form("chat_form", clear_on_submit=True):
            chat_col1, chat_col2 = st.columns([5, 1], gap="small")
            with chat_col1:
                user_input = st.text_input(
                    "question",
                    placeholder="e.g., What was decided regarding project deadlines?",
                    label_visibility="collapsed"
                )
            with chat_col2:
                send_btn = st.form_submit_button("Send →", use_container_width=True)

            if send_btn and user_input.strip():
                with st.spinner("Retrieving answer from transcript..."):
                    answer = ask_question(r["rag_chain"], user_input.strip())
                st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                st.rerun()

        if st.session_state.chat_history:
            if st.button("🗑️ Clear Chat History", type="secondary"):
                st.session_state.chat_history = []
                st.rerun()

    else:
        # Initial Empty State
        st.markdown("""
        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                    padding:5rem 2rem;text-align:center;">
            <div style="
                width:88px;height:88px;
                background:var(--accent-light);
                border-radius:50%;
                display:flex;align-items:center;justify-content:center;
                font-size:2.4rem;
                margin-bottom:1.4rem;
                box-shadow:0 4px 20px rgba(193,127,82,0.2);
            ">🎬</div>
            <div style="font-family:'Lora',serif;font-size:1.65rem;font-weight:600;
                        color:var(--text);margin-bottom:0.5rem;">
                Ready to Analyse
            </div>
            <div style="color:var(--text-muted);font-size:0.88rem;
                        max-width:380px;line-height:1.75;margin-bottom:1.75rem;">
                Paste a YouTube URL or upload a media file on the left,
                choose your language &amp; model, then click
                <strong style="color:var(--accent);">Analyse Meeting</strong>.
            </div>
        </div>""", unsafe_allow_html=True)
