"""
Custom CSS for the Streamlit UI.

Most colours come from the theme in .streamlit/config.toml; this file only adds
the fonts, spacing and the few custom elements (header, progress steps, empty state).
"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=Newsreader:opsz,wght@6..72,500;6..72,600&display=swap');

:root {
    --bg: #131211;
    --surface: #1d1c1a;
    --border: #34312d;
    --text: #ece8e1;
    --muted: #b0aaa1;
    --faint: #8f897f;
    --accent: #e58a4e;
    --ok: #86b894;
    --error: #ea7b72;
    --serif: 'Newsreader', Georgia, serif;
    --mono: 'IBM Plex Mono', ui-monospace, monospace;
}

/* ── Page frame ───────────────────────────────────────────── */
[data-testid="stHeader"] { background: transparent; }

.block-container {
    max-width: 1180px;
    padding-top: 2.5rem;
    padding-bottom: 4rem;
}

/* ── Header ───────────────────────────────────────────────── */
.app-header {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: 0.5rem 2rem;
    padding-bottom: 1.25rem;
    margin-bottom: 2rem;
    border-bottom: 1px solid var(--border);
}

[data-testid="stMarkdownContainer"] .app-header .brand {
    font-family: var(--serif);
    font-size: 1.85rem;
    font-weight: 600;
    letter-spacing: -0.01em;
    color: var(--text);
    margin: 0;
}

.app-header .brand span { color: var(--accent); }

[data-testid="stMarkdownContainer"] .app-header .tagline {
    color: var(--muted);
    font-size: 0.95rem;
    max-width: 46ch;
    margin: 0;
}

/* Hide Streamlit's "Press Enter to apply" hint: it overlaps the placeholder text.
   The link is still picked up when Analyse is clicked. */
[data-testid="InputInstructions"] { display: none; }

/* Small uppercase label above a group of controls.
   The [data-testid] prefix beats Streamlit's own paragraph font size. */
[data-testid="stMarkdownContainer"] .section-label {
    font-family: var(--mono);
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--faint);
    margin: 0 0 0.35rem;
}

/* ── Buttons ──────────────────────────────────────────────── */
/* Dark text on the orange button keeps it readable (white on orange is too faint) */
button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-primary"] p {
    color: #1a1310 !important;
    font-weight: 600;
}

button:focus-visible {
    outline: 2px solid var(--accent) !important;
    outline-offset: 2px;
}

/* ── Pipeline steps ───────────────────────────────────────── */
[data-testid="stMarkdownContainer"] .steps {
    list-style: none;
    margin: 1.5rem 0 0;
    padding: 1rem 0 0 !important;
    border-top: 1px solid var(--border);
}

[data-testid="stMarkdownContainer"] .steps li { margin: 0; }

.step {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    padding: 0.35rem 0;
    font-size: 0.9rem;
    color: var(--faint);
}

.step-marker {
    flex: none;
    width: 1.45rem;
    height: 1.45rem;
    display: grid;
    place-items: center;
    border: 1px solid var(--border);
    border-radius: 50%;
    font-family: var(--mono);
    font-size: 0.72rem;
}

.step-active { color: var(--text); }
.step-active .step-marker {
    border-color: var(--accent);
    color: var(--accent);
    animation: pulse 1.6s ease-in-out infinite;
}

.step-done { color: var(--muted); }
.step-done .step-marker {
    background: var(--ok);
    border-color: var(--ok);
    color: var(--bg);
}

.step-error { color: var(--error); }
.step-error .step-marker { border-color: var(--error); }

@keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(229, 138, 78, 0.45); }
    50%      { box-shadow: 0 0 0 5px rgba(229, 138, 78, 0); }
}

@media (prefers-reduced-motion: reduce) {
    .step-active .step-marker { animation: none; }
}

/* ── Results ──────────────────────────────────────────────── */
[data-testid="stMarkdownContainer"] .result-meta {
    font-family: var(--mono);
    font-size: 0.75rem;
    color: var(--faint);
    margin: 0;
}

[data-testid="stMarkdownContainer"] .result-title {
    font-family: var(--serif);
    font-size: 2rem !important;
    font-weight: 600;
    line-height: 1.2;
    color: var(--text);
    margin: 0.35rem 0 0 !important;
    padding: 0 !important;
}

/* Comfortable line length for the summary and insights */
[data-baseweb="tab-panel"] [data-testid="stMarkdownContainer"] {
    max-width: 72ch;
    line-height: 1.65;
}

[data-baseweb="tab-panel"] { padding-top: 0.75rem; }

[data-testid="stMarkdownContainer"] .section-title {
    font-family: var(--serif);
    font-size: 1.4rem !important;
    font-weight: 600;
    color: var(--text);
    margin: 2.25rem 0 0.25rem !important;
    padding: 1.75rem 0 0 !important;
    border-top: 1px solid var(--border);
}

[data-testid="stMarkdownContainer"] .section-hint {
    color: var(--muted);
    font-size: 0.9rem;
    margin: 0 0 0.75rem;
}

/* ── Chat ─────────────────────────────────────────────────── */
/* Quiet avatars in theme colours instead of Streamlit's bright defaults */
[data-testid="stChatMessageAvatarUser"],
[data-testid="stChatMessageAvatarAssistant"] {
    background: #2a2825 !important;
    color: var(--muted) !important;
    border: 1px solid var(--border);
}

[data-testid="stChatMessageAvatarAssistant"] {
    background: rgba(229, 138, 78, 0.14) !important;
    color: var(--accent) !important;
    border-color: rgba(229, 138, 78, 0.35);
}

[data-testid="stChatMessageAvatarUser"] *,
[data-testid="stChatMessageAvatarAssistant"] * {
    color: inherit !important;
    fill: currentColor;
}

/* ── Empty state ──────────────────────────────────────────── */
.empty {
    border: 1px dashed var(--border);
    border-radius: 12px;
    padding: 2rem 2.25rem;
    color: var(--muted);
    line-height: 1.65;
}

[data-testid="stMarkdownContainer"] .empty h2 {
    font-family: var(--serif);
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--text);
    margin: 0 0 0.4rem;
    padding: 0;
}

.empty ol { margin: 1rem 0 0; padding-left: 1.2rem; }
.empty li { margin: 0.3rem 0; }
.empty li strong { color: var(--text); font-weight: 500; }

[data-testid="stMarkdownContainer"] .empty .note {
    margin: 1.25rem 0 0;
    font-size: 0.85rem;
    color: var(--faint);
}
</style>
"""
