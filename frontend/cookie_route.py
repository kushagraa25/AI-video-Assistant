"""
Hidden Route: Cookie Management Interface for Streamlit.
Allows updating, inspecting, and testing yt-dlp cookie files (cookies.txt / cookie.txt)
without exposing controls in the public UI.
"""

import os
import streamlit as st
from backend.cookie_manager import (
    get_cookie_status,
    save_cookie_content,
    delete_cookie_files,
    test_youtube_connectivity,
    get_cookie_target_path,
)


def is_cookie_route_requested() -> bool:
    """
    Checks if current URL query parameters request the hidden cookie management route.
    Supported patterns:
      ?route=cookies or ?route=cookie or ?route=cookie_update
      ?admin=cookies or ?admin=cookie
      ?manage_cookies=1 or ?manage_cookies=true
      ?cookies=1 or ?cookie=1 or ?cookie=true
    """
    try:
        params = st.query_params
    except Exception:
        return False

    route_val = str(params.get("route", "")).strip().lower()
    if route_val in ["cookie", "cookies", "coociee", "cookie_update", "cookie_manager", "admin_cookies"]:
        return True

    admin_val = str(params.get("admin", "")).strip().lower()
    if admin_val in ["cookie", "cookies", "coociee"]:
        return True

    for flag in ["manage_cookies", "cookies", "cookie", "coociee"]:
        val = str(params.get(flag, "")).strip().lower()
        if val in ["1", "true", "yes", "open"]:
            return True

    return False


def check_auth() -> bool:
    """
    Optional authentication if COOKIE_SECRET_KEY is configured in .env.
    If no key is configured, access is granted automatically.
    """
    secret_key = os.getenv("COOKIE_SECRET_KEY", "").strip()
    if not secret_key:
        return True

    # Check if already authenticated in session
    if st.session_state.get("cookie_route_auth_passed"):
        return True

    # Check if passed via query param ?key=...
    try:
        url_key = str(st.query_params.get("key", "")).strip()
        if url_key and url_key == secret_key:
            st.session_state["cookie_route_auth_passed"] = True
            return True
    except Exception:
        pass

    return False


def render_cookie_management_route():
    """
    Renders the hidden cookie management dashboard in Streamlit.
    """
    # ── Header Bar & Navigation ──────────────────────────────────────────────
    col_nav, col_badge = st.columns([4, 1])
    with col_nav:
        if st.button("← Return to AI Video Assistant", type="secondary"):
            st.query_params.clear()
            st.session_state.pop("cookie_route_auth_passed", None)
            st.rerun()

    with col_badge:
        st.markdown(
            '<div style="text-align:right;"><span class="badge badge-warm">🔒 Hidden Route</span></div>',
            unsafe_allow_html=True,
        )

    # ── Authentication Gate (if COOKIE_SECRET_KEY is configured) ─────────────
    if not check_auth():
        st.markdown("""
        <div class="card" style="max-width:550px;margin:2rem auto;padding:2rem;">
            <div class="card-title" style="color:#000000;font-size:1.25rem;">🔐 Protected Route</div>
            <p style="color:#222;font-size:0.9rem;margin-bottom:1rem;">
                A secret key is required to access the YouTube Cookie Manager.
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("auth_form", clear_on_submit=False):
            entered_key = st.text_input("Enter Secret Key", type="password")
            submit_auth = st.form_submit_button("Unlock", use_container_width=True)
            if submit_auth:
                expected_key = os.getenv("COOKIE_SECRET_KEY", "").strip()
                if entered_key.strip() == expected_key:
                    st.session_state["cookie_route_auth_passed"] = True
                    st.success("Access granted!")
                    st.rerun()
                else:
                    st.error("Invalid secret key. Please try again.")
        return

    # ── Dashboard Title ──────────────────────────────────────────────────────
    st.markdown("""
    <div style="margin-top:0.75rem;margin-bottom:1.5rem;">
        <div style="font-family:'Lora',serif;font-size:1.85rem;font-weight:700;color:#000000;line-height:1.2;">
            🍪 YouTube Cookie Manager
        </div>
        <div style="color:#222222;font-size:0.92rem;margin-top:0.35rem;line-height:1.5;">
            Update or refresh your Netscape cookie file (<code>cookies.txt</code> / <code>cookie.txt</code>) to resolve YouTube bot challenges and age-restricted video extraction without restarting the application.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Current Status Card ──────────────────────────────────────────────────
    status = get_cookie_status()
    target_path = status["target_path"]
    exists = status["exists"]

    card_border = "border-left: 5px solid #1f6655;" if exists else "border-left: 5px solid #b85b24;"
    status_icon = "🟢" if exists else "🟠"
    status_label = f"Active ({status['total_cookies']} cookies loaded)" if exists else "No active cookie file found"

    st.markdown(f"""
    <div class="card" style="{card_border}margin-bottom:1.5rem;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem;">
            <div class="card-title" style="color:#000000;font-size:1.1rem;margin:0;">
                {status_icon} Status: <strong>{status_label}</strong>
            </div>
            <span style="font-size:0.8rem;color:#444;background:#f2eee8;padding:0.25rem 0.6rem;border-radius:6px;font-family:monospace;">
                {os.path.basename(target_path)}
            </span>
        </div>
        <div style="font-size:0.88rem;color:#111;line-height:1.6;">
            <strong>Target File Path:</strong> <code style="background:#eee;padding:0.15rem 0.4rem;border-radius:4px;">{target_path}</code><br>
            <strong>File Size:</strong> {status['size_kb']} KB ({status['size_bytes']} bytes)<br>
            <strong>Last Updated:</strong> {status['modified_time'] or 'Never'}<br>
            <strong>YouTube / Google Cookies:</strong> {status['youtube_cookies']} detected
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Show key YouTube authentication tokens detected
    if exists and status["key_cookies_present"]:
        key_tags = " ".join([f"<span class='badge badge-green' style='margin-right:0.3rem;'>{k}</span>" for k in status["key_cookies_present"]])
        st.markdown(f"""
        <div style="margin-bottom:1rem;font-size:0.86rem;color:#111;">
            <strong>Detected Session Identifiers:</strong> {key_tags}
        </div>
        """, unsafe_allow_html=True)

    # Expander to preview cookies safely
    if exists and status["sample_cookies"]:
        with st.expander("🔍 Inspect Loaded Cookies (First 15 entries)", expanded=False):
            preview_data = [
                {
                    "Domain": c["domain"],
                    "Name": c["name"],
                    "Path": c["path"],
                    "Expires": c["expiry"],
                    "Value (Masked)": c["value_masked"],
                    "YouTube": "✅" if c["is_youtube"] else "—",
                }
                for c in status["sample_cookies"]
            ]
            st.dataframe(preview_data, use_container_width=True)

    st.markdown("---")

    # ── Update Cookies Form ──────────────────────────────────────────────────
    st.markdown("""
    <div style="font-family:'Lora',serif;font-size:1.25rem;font-weight:700;color:#000000;margin-bottom:0.75rem;">
        📝 Update Cookie File
    </div>
    """, unsafe_allow_html=True)

    tab_paste, tab_upload, tab_test = st.tabs(["📋 Paste Netscape Cookies", "📁 Upload File", "🧪 Test Connection"])

    # ── TAB 1: Paste Text ────────────────────────────────────────────────────
    with tab_paste:
        st.markdown("""
        <div style="font-size:0.86rem;color:#222;margin-bottom:0.6rem;">
            Export cookies from your browser session using an extension such as 
            <strong>'Get cookies.txt LOCALLY'</strong> (Chrome / Firefox / Edge) while visiting 
            <a href="https://www.youtube.com" target="_blank" style="color:var(--accent);">youtube.com</a>, 
            then paste the raw text below:
        </div>
        """, unsafe_allow_html=True)

        with st.form("paste_cookie_form"):
            default_content = status.get("content", "") if exists else ""
            pasted_text = st.text_area(
                "Netscape Cookies Content",
                value=default_content,
                height=260,
                placeholder="# Netscape HTTP Cookie File\n# http://curl.haxx.se/rfc/cookie_spec.html\n.youtube.com\tTRUE\t/\tTRUE\t1799999999\tVISITOR_INFO1_LIVE\t...",
                label_visibility="collapsed",
            )
            save_pasted_btn = st.form_submit_button("💾 Save & Apply Cookies", use_container_width=True)

            if save_pasted_btn:
                if not pasted_text.strip():
                    st.error("Please paste cookie text before saving.")
                else:
                    success, msg, count = save_cookie_content(pasted_text)
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    # ── TAB 2: Upload File ───────────────────────────────────────────────────
    with tab_upload:
        st.markdown("""
        <div style="font-size:0.86rem;color:#222;margin-bottom:0.6rem;">
            Upload an exported <code>cookies.txt</code> or <code>cookie.txt</code> file directly:
        </div>
        """, unsafe_allow_html=True)

        uploaded_cookie_file = st.file_uploader(
            "Choose cookie file",
            type=["txt"],
            label_visibility="collapsed",
            key="cookie_file_uploader",
        )
        if uploaded_cookie_file is not None:
            if st.button("💾 Apply Uploaded Cookie File", use_container_width=True):
                try:
                    file_text = uploaded_cookie_file.getvalue().decode("utf-8", errors="replace")
                    success, msg, count = save_cookie_content(file_text)
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
                except Exception as e:
                    st.error(f"❌ Failed to read uploaded file: {e}")

    # ── TAB 3: Test YouTube Connection ───────────────────────────────────────
    with tab_test:
        st.markdown("""
        <div style="font-size:0.86rem;color:#222;margin-bottom:0.6rem;">
            Verify whether YouTube accepts the currently saved cookies using yt-dlp:
        </div>
        """, unsafe_allow_html=True)

        test_url = st.text_input(
            "YouTube Test Video URL",
            value="https://www.youtube.com/watch?v=jNQXAC9IVRw",
            key="cookie_test_url",
        )
        if st.button("🧪 Run Test Verification", use_container_width=True):
            with st.spinner("Testing YouTube authentication with saved cookies..."):
                ok, test_msg = test_youtube_connectivity(test_url.strip())
                if ok:
                    st.success(test_msg)
                else:
                    st.error(test_msg)

    # ── Danger Zone ──────────────────────────────────────────────────────────
    if exists:
        st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)
        with st.expander("⚠️ Danger Zone: Remove Cookie File"):
            st.markdown("<span style='font-size:0.85rem;color:#666;'>If your cookies have expired or you wish to revert to unauthenticated requests:</span>", unsafe_allow_html=True)
            confirm_del = st.checkbox("I confirm I want to delete the active cookie file.", key="confirm_cookie_del")
            if st.button("🗑️ Delete Cookie File", disabled=not confirm_del, type="secondary"):
                ok, del_msg = delete_cookie_files()
                if ok:
                    st.success(del_msg)
                    st.rerun()
                else:
                    st.error(del_msg)
