"""
Frontend custom styles and UI layout components for Streamlit.
Optimized for high-contrast, crystal-clear readability with black text.
"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Lora:ital,wght@0,400;0,600;0,700;1,400&display=swap');

:root {
    --bg: #fbf9f6;
    --surface: #ffffff;
    --surface-2: #f2eee8;
    --border: #d0c8be;
    --border-strong: #8a7c6f;
    --accent: #b85b24;
    --accent-dark: #8e4215;
    --accent-light: #faece3;
    --accent-2: #2d6b5e;
    --accent-2-light: #d6ebe6;
    --text: #000000;
    --text-muted: #111111;
    --text-light: #222222;
    --success: #1f6655;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.05);
    --shadow-md: 0 4px 16px rgba(0,0,0,0.12), 0 2px 6px rgba(0,0,0,0.08);
}

/* Global Font & High-Contrast Pure Black Text */
html, body, [class*="css"], .stMarkdown, .stText, p, span, div, label, li, h1, h2, h3, h4, h5, h6 {
    font-family: 'Inter', sans-serif !important;
    color: #000000 !important;
}

.stApp {
    background: var(--bg) !important;
}

.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background-image:
        radial-gradient(ellipse at 10% 10%, rgba(184,91,36,0.05) 0%, transparent 55%),
        radial-gradient(ellipse at 90% 90%, rgba(45,107,94,0.05) 0%, transparent 55%);
    pointer-events: none;
    z-index: 0;
}

[data-testid="stToolbar"]      { display: none !important; }
[data-testid="stDecoration"]   { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
.stDeployButton                { display: none !important; }
#MainMenu                      { visibility: hidden !important; }
footer                         { display: none !important; }
[data-testid="stSidebar"]      { display: none !important; }
[data-testid="collapsedControl"]{ display: none !important; }
[data-testid="stSkillsNudgeAnchor"],
[data-testid="stSkillsNudge"],
.stSkillsNudge                 { display: none !important; }
[data-testid="InputInstructions"] { display: none !important; }

.block-container {
    padding-top: 1.5rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    max-width: 100% !important;
}

.left-panel {
    position: sticky;
    top: 1rem;
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: 20px;
    padding: 1.75rem 1.5rem;
    box-shadow: var(--shadow-md);
    height: fit-content;
}

.panel-logo {
    font-family: 'Lora', serif;
    font-size: 1.45rem;
    font-weight: 700;
    color: #000000 !important;
    line-height: 1.3;
    margin-bottom: 0.2rem;
}

.panel-logo .accent { color: var(--accent) !important; }

.panel-sub {
    font-size: 0.82rem;
    font-weight: 600 !important;
    color: #111111 !important;
    margin-bottom: 1.25rem;
}

.panel-label {
    font-size: 0.72rem;
    font-weight: 800 !important;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #000000 !important;
    margin-bottom: 0.5rem;
    display: block;
}

/* High Contrast Input Fields */
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: #ffffff !important;
    border: 1.5px solid var(--border-strong) !important;
    border-radius: 10px !important;
    color: #000000 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}

.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(184,91,36,0.18) !important;
}

/* Radio & Widget Labels in Black */
label,
.stRadio label,
.stSelectbox label,
.stTextInput label,
.stFileUploader label,
[data-testid="stWidgetLabel"] p,
.stRadio div[role="radiogroup"] label div p {
    color: #000000 !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
}

/* Captions and subtitles in high-contrast black/dark */
.stCaption, [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
    color: #111111 !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
}

.stButton > button {
    background: var(--accent) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    padding: 0.7rem 1.5rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 10px rgba(184,91,36,0.35) !important;
    width: 100% !important;
}

.stButton > button:hover {
    background: var(--accent-dark) !important;
    color: #ffffff !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(184,91,36,0.45) !important;
}

.card {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: 18px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    box-shadow: var(--shadow-sm);
    transition: box-shadow 0.25s ease, transform 0.25s ease;
}

.card:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
}

.card-title {
    font-size: 0.72rem;
    font-weight: 800 !important;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #000000 !important;
    margin-bottom: 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

.card-content,
.card-content p,
.card-content span,
.card-content div,
.card-content li {
    font-size: 0.92rem;
    line-height: 1.8;
    color: #000000 !important;
    font-weight: 500 !important;
}

.badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.25rem 0.8rem;
    border-radius: 100px;
    font-size: 0.74rem;
    font-weight: 700 !important;
}

.badge-warm    { background: var(--accent-light);  color: var(--accent-dark) !important; border: 1.5px solid rgba(184,91,36,0.4); }
.badge-green   { background: var(--accent-2-light); color: var(--accent-2) !important;   border: 1.5px solid rgba(45,107,94,0.35); }
.badge-neutral { background: var(--surface-2);      color: #000000 !important;            border: 1.5px solid var(--border); }

.status-bar {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    padding: 0.55rem 0.85rem;
    background: var(--surface-2);
    border-radius: 9px;
    margin: 0.28rem 0;
    border: 1.5px solid var(--border);
    font-size: 0.82rem;
    font-weight: 600 !important;
    color: #000000 !important;
}

.status-bar span {
    color: #000000 !important;
    font-weight: 600 !important;
}

.status-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.dot-active  { background: var(--accent); box-shadow: 0 0 0 3px rgba(184,91,36,0.3); animation: pulse 1.5s infinite; }
.dot-done    { background: var(--success); }
.dot-pending { background: var(--border-strong); }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.35; }
}

.hero-title {
    font-family: 'Lora', serif;
    font-size: clamp(1.6rem, 3vw, 2.4rem);
    font-weight: 700 !important;
    line-height: 1.25;
    color: #000000 !important;
    margin: 0;
}
.hero-title .accent { color: var(--accent) !important; }

.hero-sub {
    font-size: 0.92rem;
    font-weight: 600 !important;
    color: #111111 !important;
    margin-top: 0.35rem;
}

.chat-container {
    background: var(--surface-2);
    border: 1.5px solid var(--border);
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    max-height: 420px;
    overflow-y: auto;
    margin-bottom: 1rem;
}

.chat-msg { margin-bottom: 1.1rem; display: flex; flex-direction: column; gap: 0.22rem; }

.chat-label {
    font-size: 0.68rem;
    font-weight: 800 !important;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 0 0.2rem;
}

.chat-bubble {
    display: inline-block;
    padding: 0.75rem 1.1rem;
    border-radius: 14px;
    font-size: 0.9rem;
    line-height: 1.65;
    max-width: 86%;
}

.user-label  { color: var(--accent) !important; }
.bot-label   { color: var(--accent-2) !important; }

.user-bubble {
    background: var(--accent);
    color: #ffffff !important;
    border-bottom-right-radius: 4px;
    align-self: flex-end;
    box-shadow: 0 2px 10px rgba(184,91,36,0.3);
    font-weight: 500;
}

.bot-bubble {
    background: var(--surface);
    color: #000000 !important;
    border: 1.5px solid var(--border);
    border-bottom-left-radius: 4px;
    align-self: flex-start;
    box-shadow: var(--shadow-sm);
    font-weight: 500;
}

.transcript-box {
    background: #ffffff;
    border: 1.5px solid var(--border);
    border-radius: 10px;
    padding: 1.1rem;
    font-size: 0.88rem;
    line-height: 1.9;
    max-height: 280px;
    overflow-y: auto;
    color: #000000 !important;
    font-weight: 500 !important;
    white-space: pre-wrap;
    word-break: break-word;
}

/* Expanders */
.streamlit-expanderHeader,
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {
    color: #000000 !important;
    font-weight: 700 !important;
}

/* Markdown Containers All Black */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] div,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] strong,
[data-testid="stMarkdownContainer"] em {
    color: #000000 !important;
}
</style>
"""
