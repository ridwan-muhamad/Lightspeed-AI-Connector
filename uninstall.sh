#!/usr/bin/env bash
set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== Menghapus Red Hat Lightspeed OpenAI Bridge ===${NC}"

echo "[1/3] Menghentikan dan menonaktifkan systemd user service..."
systemctl --user stop lightspeed-bridge.service 2>/dev/null || true
systemctl --user disable lightspeed-bridge.service 2>/dev/null || true

echo "[2/3] Menghapus file unit service..."
rm -f "$HOME/.config/systemd/user/lightspeed-bridge.service"
systemctl --user daemon-reload

echo "[3/3] Menghapus file script bridge..."
rm -f "$HOME/.config/opencode/lightspeed_bridge.py"

echo -e "${GREEN}✓ Uninstall selesai! Konfigurasi OpenCode di ~/.config/opencode/opencode.jsonc dipertahankan.${NC}"
