#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  AI Video Assistant - one-command VPS setup (Ubuntu / Debian)
#
#  Usage (from the project folder):
#      sudo bash setup_vps.sh
#
#  Optional settings (environment variables):
#      SERVICE_NAME=ai-video-assistant   systemd service to create/restart
#      APP_PORT=8501                     port for a newly created service
#      TEST_URL=<youtube url>            video used to test YouTube downloads
#
#  Safe to run again: every step checks first and only installs what's missing.
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$APP_DIR/.venv"
SERVICE_NAME="${SERVICE_NAME:-ai-video-assistant}"
APP_PORT="${APP_PORT:-8501}"
TEST_URL="${TEST_URL:-https://www.youtube.com/watch?v=jNQXAC9IVRw}"
POT_CONTAINER="bgutil-provider"
POT_PORT=4416
WARP_PORT=40000
WARP_PROXY="socks5://127.0.0.1:$WARP_PORT"

green()  { printf '\033[32m✔ %s\033[0m\n' "$*"; }
yellow() { printf '\033[33m➜ %s\033[0m\n' "$*"; }
red()    { printf '\033[31m✘ %s\033[0m\n' "$*"; }
step()   { printf '\n\033[1;36m══ %s ══\033[0m\n' "$*"; }
die()    { red "$*"; exit 1; }

[ "$(id -u)" -eq 0 ] || die "Please run as root:  sudo bash setup_vps.sh"
command -v apt-get >/dev/null || die "This script supports Ubuntu/Debian (apt-get) only."
cd "$APP_DIR" || die "Cannot enter $APP_DIR"
[ -f requirements.txt ] && [ -f app.py ] || die "Run this script from the project folder (app.py not found)."

# ── 1. System packages ───────────────────────────────────────────────────────
step "1/7 System packages"
PACKAGES=(python3 python3-venv python3-pip ffmpeg curl unzip gnupg ca-certificates lsb-release)
MISSING=()
for pkg in "${PACKAGES[@]}"; do
    dpkg -s "$pkg" >/dev/null 2>&1 || MISSING+=("$pkg")
done
if [ ${#MISSING[@]} -gt 0 ]; then
    yellow "Installing: ${MISSING[*]}"
    apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "${MISSING[@]}" \
        || die "apt-get install failed"
fi
green "System packages ready (ffmpeg: $(ffmpeg -version 2>/dev/null | head -1 | cut -d' ' -f3))"

# ── 2. Deno (JavaScript runtime YouTube needs) ───────────────────────────────
step "2/7 Deno (JavaScript runtime)"
if command -v deno >/dev/null 2>&1; then
    green "Deno already installed: $(deno --version | head -1)"
else
    case "$(uname -m)" in
        x86_64)  DENO_ARCH="x86_64-unknown-linux-gnu" ;;
        aarch64) DENO_ARCH="aarch64-unknown-linux-gnu" ;;
        *)       die "Unsupported CPU architecture: $(uname -m)" ;;
    esac
    yellow "Installing Deno to /usr/local/bin ..."
    TMP_ZIP="$(mktemp --suffix=.zip)"
    curl -fsSL "https://github.com/denoland/deno/releases/latest/download/deno-$DENO_ARCH.zip" -o "$TMP_ZIP" \
        && unzip -o -q "$TMP_ZIP" -d /usr/local/bin && chmod +x /usr/local/bin/deno \
        || die "Deno installation failed"
    rm -f "$TMP_ZIP"
    green "Deno installed: $(deno --version | head -1)"
fi

# ── 3. Python virtual environment + dependencies ─────────────────────────────
step "3/7 Python environment"
if [ ! -x "$VENV/bin/python" ]; then
    yellow "Creating virtual environment in $VENV"
    python3 -m venv "$VENV" || die "Could not create the virtual environment"
fi
yellow "Installing / updating Python packages (first run can take several minutes: torch, whisper)..."
"$VENV/bin/pip" install -q --upgrade pip \
    && "$VENV/bin/pip" install -q -r requirements.txt \
    && "$VENV/bin/pip" install -q -U "yt-dlp[default]" \
    || die "pip install failed"
green "Python packages ready (yt-dlp $("$VENV/bin/python" -m yt_dlp --version))"

# ── 4. .env file ─────────────────────────────────────────────────────────────
step "4/7 .env configuration"
if [ ! -f .env ]; then
    cp .env.example .env
    chmod 600 .env
    yellow "Created .env from .env.example"
fi
if grep -qE '^MISTRAL_API_KEY=(your_|$)' .env; then
    red "MISTRAL_API_KEY is not set in $APP_DIR/.env - add it, then run this script again."
    ENV_OK=0
else
    green "MISTRAL_API_KEY is set"
    ENV_OK=1
fi
grep -qE '^SARVAM_API_KEY=(your_|$)' .env && yellow "SARVAM_API_KEY is not set (only needed for Hinglish)."

# ── 5. PO-token server (Docker) ──────────────────────────────────────────────
step "5/7 PO-token server (passes YouTube's bot check)"
if ! command -v docker >/dev/null 2>&1; then
    yellow "Installing Docker..."
    curl -fsSL https://get.docker.com | sh || die "Docker installation failed"
fi
systemctl enable --now docker >/dev/null 2>&1

POT_VERSION="$(grep -oP 'bgutil-ytdlp-pot-provider==\K[0-9.]+' requirements.txt || true)"
POT_IMAGE="brainicism/bgutil-ytdlp-pot-provider:${POT_VERSION:-latest}"
CURRENT_IMAGE="$(docker inspect -f '{{.Config.Image}}' "$POT_CONTAINER" 2>/dev/null || true)"

if [ -n "$CURRENT_IMAGE" ] && [ "$CURRENT_IMAGE" != "$POT_IMAGE" ]; then
    yellow "Replacing $CURRENT_IMAGE with $POT_IMAGE (version must match the Python plugin)"
    docker rm -f "$POT_CONTAINER" >/dev/null
    CURRENT_IMAGE=""
fi
if [ -z "$CURRENT_IMAGE" ]; then
    yellow "Starting $POT_IMAGE (bound to 127.0.0.1 only)"
    if ! docker pull -q "$POT_IMAGE" >/dev/null 2>&1; then
        yellow "Image $POT_IMAGE not found, using the latest version instead"
        POT_IMAGE="brainicism/bgutil-ytdlp-pot-provider:latest"
    fi
    docker run --name "$POT_CONTAINER" -d --init --restart unless-stopped \
        -p "127.0.0.1:$POT_PORT:$POT_PORT" "$POT_IMAGE" >/dev/null || die "Could not start the PO-token server"
elif [ "$(docker inspect -f '{{.State.Running}}' "$POT_CONTAINER")" != "true" ]; then
    yellow "Starting existing $POT_CONTAINER container"
    docker start "$POT_CONTAINER" >/dev/null
fi

for _ in $(seq 1 30); do
    curl -fs "http://127.0.0.1:$POT_PORT/ping" >/dev/null 2>&1 && break
    sleep 1
done
if curl -fs "http://127.0.0.1:$POT_PORT/ping" >/dev/null 2>&1; then
    green "PO-token server is running on 127.0.0.1:$POT_PORT"
else
    red "PO-token server did not respond. Logs: docker logs $POT_CONTAINER"
fi

# ── 6. Test YouTube download (uses the app's own download code) ──────────────
step "6/7 Testing YouTube download"

# Returns 0 if the app can download TEST_URL. $1 = optional proxy.
test_youtube() {
    YOUTUBE_PROXY="${1:-}" TEST_URL="$TEST_URL" APP_DIR="$APP_DIR" "$VENV/bin/python" - <<'PY'
import os, shutil, sys, tempfile
sys.path.insert(0, os.environ["APP_DIR"])
from backend import audio_processor as ap
ap.VIDEOS_DIR = tempfile.mkdtemp()  # fresh folder, so the cache can't fake a success
try:
    path = ap.download_youtube_audio(os.environ["TEST_URL"])
    print(f"Downloaded {os.path.getsize(path)} bytes")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)
finally:
    shutil.rmtree(ap.VIDEOS_DIR, ignore_errors=True)
PY
}

# Writes (or replaces) YOUTUBE_PROXY in .env
set_env_proxy() {
    sed -i '/^#\? *YOUTUBE_PROXY=/d' .env
    [ -n "$1" ] && echo "YOUTUBE_PROXY=$1" >> .env
}

YOUTUBE_OK=0
if output="$(test_youtube "" 2>&1)"; then
    echo "$output" | tail -1
    green "YouTube downloads work directly from this server - no proxy needed."
    YOUTUBE_OK=1
else
    echo "$output" | tail -1
    yellow "YouTube is blocking this server's IP. Setting up Cloudflare WARP as a free proxy..."

    if ! command -v warp-cli >/dev/null 2>&1; then
        CODENAME="$(lsb_release -cs)"
        curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg \
            | gpg --yes --dearmor -o /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg
        echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ $CODENAME main" \
            > /etc/apt/sources.list.d/cloudflare-client.list
        apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq cloudflare-warp \
            || red "Could not install cloudflare-warp (is '$CODENAME' supported by Cloudflare?)"
    fi

    if command -v warp-cli >/dev/null 2>&1; then
        systemctl enable --now warp-svc >/dev/null 2>&1
        sleep 2
        warp-cli --accept-tos registration show >/dev/null 2>&1 \
            || warp-cli --accept-tos registration new >/dev/null
        # Proxy mode BEFORE connecting: only traffic sent to the proxy port uses WARP,
        # so SSH and the rest of the server keep their normal connection.
        warp-cli --accept-tos mode proxy >/dev/null
        warp-cli --accept-tos proxy port "$WARP_PORT" >/dev/null
        warp-cli --accept-tos connect >/dev/null
        for _ in $(seq 1 20); do
            curl -fs -x "socks5h://127.0.0.1:$WARP_PORT" https://www.cloudflare.com/cdn-cgi/trace 2>/dev/null \
                | grep -q "warp=on" && break
            sleep 1
        done

        if curl -fs -x "socks5h://127.0.0.1:$WARP_PORT" https://www.cloudflare.com/cdn-cgi/trace 2>/dev/null | grep -q "warp=on"; then
            green "WARP proxy is running on 127.0.0.1:$WARP_PORT"
            if output="$(test_youtube "$WARP_PROXY" 2>&1)"; then
                echo "$output" | tail -1
                set_env_proxy "$WARP_PROXY"
                green "YouTube works through WARP - saved YOUTUBE_PROXY=$WARP_PROXY in .env"
                YOUTUBE_OK=1
            else
                echo "$output" | tail -1
                red "YouTube also blocks the WARP IP."
            fi
        else
            red "WARP did not connect. Check: warp-cli status"
        fi
    fi
fi

# ── 7. systemd service ───────────────────────────────────────────────────────
step "7/7 App service"
# Reuse an existing service that already runs this project, otherwise create one
EXISTING_UNIT="$(grep -lsF "$APP_DIR" /etc/systemd/system/*.service | head -1)"
[ -z "$EXISTING_UNIT" ] && [ -f "/etc/systemd/system/$SERVICE_NAME.service" ] \
    && EXISTING_UNIT="/etc/systemd/system/$SERVICE_NAME.service"  # never overwrite an existing unit
if [ -n "$EXISTING_UNIT" ]; then
    SERVICE_NAME="$(basename "$EXISTING_UNIT" .service)"
    yellow "Found existing service: $SERVICE_NAME"
    grep -q "app.py" "$EXISTING_UNIT" || red "$EXISTING_UNIT does not run app.py - update its ExecStart to: $VENV/bin/streamlit run app.py"
else
    yellow "Creating /etc/systemd/system/$SERVICE_NAME.service (port $APP_PORT)"
    cat > "/etc/systemd/system/$SERVICE_NAME.service" <<UNIT
[Unit]
Description=AI Video Assistant (Streamlit)
After=network-online.target docker.service
Wants=network-online.target

[Service]
WorkingDirectory=$APP_DIR
Environment=PATH=$VENV/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$VENV/bin/streamlit run app.py --server.port $APP_PORT --server.headless true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME" >/dev/null 2>&1
fi
systemctl restart "$SERVICE_NAME"
sleep 3
if systemctl is-active --quiet "$SERVICE_NAME"; then
    green "Service '$SERVICE_NAME' is running"
else
    red "Service '$SERVICE_NAME' failed to start. Logs: journalctl -u $SERVICE_NAME -n 50"
fi

# ── Summary ──────────────────────────────────────────────────────────────────
step "Summary"
[ "$ENV_OK" -eq 1 ] && green "API keys configured" || red "Add MISTRAL_API_KEY to .env and run again"
if [ "$YOUTUBE_OK" -eq 1 ]; then
    green "YouTube downloads work"
else
    red "YouTube still blocks this server. Options: put a paid residential proxy in .env as"
    red "YOUTUBE_PROXY=http://user:pass@host:port, or use 'Upload file' in the app."
fi
echo "Service logs:  journalctl -u $SERVICE_NAME -f"
