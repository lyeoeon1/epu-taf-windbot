#!/usr/bin/env bash
# Setup BotAI backend on VPS (run as root)
# Usage: sudo bash deploy/setup-vps.sh
set -euo pipefail

REPO_URL="https://github.com/lyeoeon1/botai.git"
APP_USER="botai"
APP_DIR="/home/${APP_USER}/botai-backend"
REPO_DIR="${APP_DIR}/repo"
VENV_DIR="${REPO_DIR}/backend/venv"
SERVICE_NAME="botai-backend"

echo "=== BotAI Backend VPS Setup ==="

# 1. Create dedicated user
if id "${APP_USER}" &>/dev/null; then
    echo "[OK] User '${APP_USER}' already exists"
else
    echo "[*] Creating user '${APP_USER}'..."
    useradd -m -s /bin/bash "${APP_USER}"
    echo "[OK] User '${APP_USER}' created"
fi

# 2. Clone repo
if [ -d "${REPO_DIR}/.git" ]; then
    echo "[OK] Repo already cloned at ${REPO_DIR}"
    echo "[*] Pulling latest changes..."
    sudo -u "${APP_USER}" git -C "${REPO_DIR}" pull
else
    echo "[*] Cloning repo..."
    sudo -u "${APP_USER}" mkdir -p "${APP_DIR}"
    sudo -u "${APP_USER}" git clone "${REPO_URL}" "${REPO_DIR}"
    echo "[OK] Repo cloned"
fi

# 3. Create venv & install dependencies
echo "[*] Setting up Python venv..."
if [ ! -d "${VENV_DIR}" ]; then
    sudo -u "${APP_USER}" python3 -m venv "${VENV_DIR}"
fi
sudo -u "${APP_USER}" "${VENV_DIR}/bin/pip" install --upgrade pip
sudo -u "${APP_USER}" "${VENV_DIR}/bin/pip" install -r "${REPO_DIR}/backend/requirements.txt"
echo "[OK] Dependencies installed"

# 4. Copy .env from old setup if exists and new one doesn't
ENV_FILE="${REPO_DIR}/backend/.env"
OLD_ENV="/root/botai/backend/.env"
if [ ! -f "${ENV_FILE}" ] && [ -f "${OLD_ENV}" ]; then
    echo "[*] Copying .env from old setup..."
    cp "${OLD_ENV}" "${ENV_FILE}"
    chown "${APP_USER}:${APP_USER}" "${ENV_FILE}"
    chmod 600 "${ENV_FILE}"
    echo "[OK] .env copied"
elif [ -f "${ENV_FILE}" ]; then
    echo "[OK] .env already exists"
else
    echo "[!!] No .env file found. Create one at: ${ENV_FILE}"
    echo "     Required vars: OPENAI_API_KEY, LLAMA_CLOUD_API_KEY, SUPABASE_URL,"
    echo "     SUPABASE_SERVICE_KEY, SUPABASE_CONNECTION_STRING, FRONTEND_URL"
fi

# 5. Install systemd service
echo "[*] Installing systemd service..."
cp "${REPO_DIR}/deploy/botai-backend.service" "/etc/systemd/system/${SERVICE_NAME}.service"
systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
echo "[OK] Service installed and enabled"

# 6. Stop old root process if running
OLD_PID=$(lsof -ti :8000 2>/dev/null || true)
if [ -n "${OLD_PID}" ]; then
    echo "[*] Stopping old process on port 8000 (PID: ${OLD_PID})..."
    kill "${OLD_PID}" 2>/dev/null || true
    sleep 2
    echo "[OK] Old process stopped"
fi

# 7. Start service
echo "[*] Starting ${SERVICE_NAME}..."
systemctl start "${SERVICE_NAME}"
sleep 3

# 8. Verify
if systemctl is-active --quiet "${SERVICE_NAME}"; then
    echo "[OK] ${SERVICE_NAME} is running!"
    echo ""
    echo "=== Setup Complete ==="
    echo "Check status:  sudo systemctl status ${SERVICE_NAME}"
    echo "View logs:     sudo journalctl -u ${SERVICE_NAME} -f"
    echo "Restart:       sudo systemctl restart ${SERVICE_NAME}"
else
    echo "[FAIL] Service failed to start. Check logs:"
    echo "       sudo journalctl -u ${SERVICE_NAME} -n 50"
    exit 1
fi
