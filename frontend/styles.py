"""
Frontend custom styles and UI layout components for Streamlit.
"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Lora:ital,wght@0,400;0,600;1,400&display=swap');

:root {
    --bg: #faf8f5;
    --surface: #ffffff;
    --surface-2: #f4f1ec;
    --border: #e5dfd6;
    --border-strong: #c9bfb0;
    --accent: #c17f52;
    --accent-dark: #a0652e;
    --accent-light: #f5e8dc;
    --accent-2: #4a7c6f;
    --accent-2-light: #d4eae5;
    --text: #2d2520;
    --text-muted: #8a7d72;
    --text-light: #b5a99e;
    --success: #4a7c6f;
    --shadow-sm: 0 1px 3px rgba(45,37,32,0.07), 0 1px 2px rgba(45,37,32,0.04);
    --shadow-md: 0 4px 16px rgba(45,37,32,0.09), 0 2px 6px rgba(45,37,32,0.05);
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
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
        radial-gradient(ellipse at 10% 10%, rgba(193,127,82,0.06) 0%, transparent 55%),
        radial-gradient(ellipse at 90% 90%, rgba(74,124,111,0.05) 0%, transparent 55%);
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
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 1.75rem 1.5rem;
    box-shadow: var(--shadow-md);
    height: fit-content;
}

.panel-logo {
    font-family: 'Lora', serif;
    font-size: 1.4rem;
    font-weight: 600;
    color: var(--text);
    line-height: 1.3;
    margin-bottom: 0.2rem;
}

.panel-logo .accent { color: var(--accent); }

.panel-sub {
    font-size: 0.78rem;
    color: var(--text-light);
    margin-bottom: 1.25rem;
}

.panel-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-light);
    margin-bottom: 0.5rem;
    display: block;
}

.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: var(--surface-2) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.875rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}

.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(193,127,82,0.15) !important;
}

.stButton > button {
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 0.65rem 1.5rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 10px rgba(193,127,82,0.32) !important;
    width: 100% !important;
}

.stButton > button:hover {
    background: var(--accent-dark) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(193,127,82,0.42) !important;
}

.card {
    background: var(--surface);
    border: 1px solid var(--border);
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
    font-size: 0.67rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--text-light);
    margin-bottom: 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

.card-content {
    font-size: 0.9rem;
    line-height: 1.8;
    color: var(--text);
}

.badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.22rem 0.75rem;
    border-radius: 100px;
    font-size: 0.7rem;
    font-weight: 600;
}

.badge-warm    { background: var(--accent-light);  color: var(--accent-dark); border: 1px solid rgba(193,127,82,0.35); }
.badge-green   { background: var(--accent-2-light); color: var(--accent-2);   border: 1px solid rgba(74,124,111,0.28); }
.badge-neutral { background: var(--surface-2);      color: var(--text-muted); border: 1px solid var(--border); }

.status-bar {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    padding: 0.55rem 0.85rem;
    background: var(--surface-2);
    border-radius: 9px;
    margin: 0.28rem 0;
    border: 1px solid var(--border);
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--text);
}

.status-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.dot-active  { background: var(--accent); box-shadow: 0 0 0 3px rgba(193,127,82,0.22); animation: pulse 1.5s infinite; }
.dot-done    { background: var(--success); }
.dot-pending { background: var(--border-strong); }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.35; }
}

.hero-title {
    font-family: 'Lora', serif;
    font-size: clamp(1.6rem, 3vw, 2.4rem);
    font-weight: 600;
    line-height: 1.25;
    color: var(--text);
    margin: 0;
}
.hero-title .accent { color: var(--accent); }
.hero-sub { font-size: 0.88rem; color: var(--text-muted); margin-top: 0.35rem; }

.chat-container {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    max-height: 420px;
    overflow-y: auto;
    margin-bottom: 1rem;
}

.chat-msg { margin-bottom: 1.1rem; display: flex; flex-direction: column; gap: 0.22rem; }

.chat-label {
    font-size: 0.66rem; font-weight: 700;
    letter-spacing: 0.1em; text-transform: uppercase;
    padding: 0 0.2rem;
}

.chat-bubble {
    display: inline-block;
    padding: 0.72rem 1rem;
    border-radius: 14px;
    font-size: 0.875rem;
    line-height: 1.65;
    max-width: 86%;
}

.user-label  { color: var(--accent); }
.bot-label   { color: var(--accent-2); }

.user-bubble {
    background: var(--accent); color: #fff;
    border-bottom-right-radius: 4px;
    align-self: flex-end;
    box-shadow: 0 2px 10px rgba(193,127,82,0.28);
}

.bot-bubble {
    background: var(--surface); color: var(--text);
    border: 1px solid var(--border);
    border-bottom-left-radius: 4px;
    align-self: flex-start;
    box-shadow: var(--shadow-sm);
}

.transcript-box {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.1rem;
    font-size: 0.84rem;
    line-height: 1.9;
    max-height: 280px;
    overflow-y: auto;
    color: var(--text-muted);
    white-space: pre-wrap;
    word-break: break-word;
}
</style>
"""
