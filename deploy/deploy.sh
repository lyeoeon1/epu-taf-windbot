#!/usr/bin/env bash
# Deploy/update BotAI backend (run as root)
# Usage: sudo bash deploy/deploy.sh
set -euo pipefail

APP_USER="botai"
REPO_DIR="/home/${APP_USER}/botai-backend/repo"
VENV_DIR="${REPO_DIR}/backend/venv"
SERVICE_NAME="botai-backend"

echo "=== BotAI Backend Deploy ==="

# 1. Pull latest code
echo "[*] Pulling latest code..."
sudo -u "${APP_USER}" git -C "${REPO_DIR}" pull
echo "[OK] Code updated"

# 2. Install/update dependencies
echo "[*] Installing dependencies..."
sudo -u "${APP_USER}" "${VENV_DIR}/bin/pip" install -r "${REPO_DIR}/backend/requirements.txt"
echo "[OK] Dependencies updated"

# 3. Restart service
echo "[*] Restarting service..."
systemctl restart "${SERVICE_NAME}"
sleep 3

# 4. Verify
if systemctl is-active --quiet "${SERVICE_NAME}"; then
    echo "[OK] ${SERVICE_NAME} restarted successfully!"
    systemctl status "${SERVICE_NAME}" --no-pager
else
    echo "[FAIL] Service failed to restart. Check logs:"
    echo "       sudo journalctl -u ${SERVICE_NAME} -n 50"
    exit 1
fi
