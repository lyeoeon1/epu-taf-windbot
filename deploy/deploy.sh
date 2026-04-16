#!/usr/bin/env bash
# Deploy/update BotAI backend (run as root)
# Usage: sudo bash deploy/deploy.sh
set -euo pipefail

APP_USER="botai"
REPO_DIR="/home/${APP_USER}/botai-backend/repo"
VENV_DIR="${REPO_DIR}/backend/venv"
SERVICE_NAME="botai-backend"
SMOKE_URL="${SMOKE_URL:-http://127.0.0.1:8001}"

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

# 4. Verify systemd unit is active
if systemctl is-active --quiet "${SERVICE_NAME}"; then
    echo "[OK] ${SERVICE_NAME} restarted successfully!"
    systemctl status "${SERVICE_NAME}" --no-pager
else
    echo "[FAIL] Service failed to restart. Check logs:"
    echo "       sudo journalctl -u ${SERVICE_NAME} -n 50"
    exit 1
fi

# 5. Smoke-test endpoints (gate the deploy)
# Skip with SKIP_SMOKE=1 if intentionally deploying without OpenAI/Supabase reachable.
if [ "${SKIP_SMOKE:-0}" = "1" ]; then
    echo "[SKIP] Smoke test (SKIP_SMOKE=1)"
else
    echo "[*] Running smoke test against ${SMOKE_URL}..."
    if sudo -u "${APP_USER}" "${VENV_DIR}/bin/python" \
        "${REPO_DIR}/backend/scripts/smoke.py" "${SMOKE_URL}" --skip-chat; then
        echo "[OK] Smoke test passed"
    else
        echo "[FAIL] Smoke test failed — backend up but endpoints broken."
        echo "       Check logs: sudo journalctl -u ${SERVICE_NAME} -n 100"
        echo "       Re-run smoke manually: ${VENV_DIR}/bin/python ${REPO_DIR}/backend/scripts/smoke.py ${SMOKE_URL}"
        exit 1
    fi
fi
