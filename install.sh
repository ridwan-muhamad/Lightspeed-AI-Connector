#!/usr/bin/env bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}==============================================================${NC}"
echo -e "${GREEN} 🚀 Red Hat Lightspeed AI Portal & OpenCode Bridge Installer ${NC}"
echo -e "${BLUE}==============================================================${NC}\n"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Step 1: Check Prerequisites
echo -e "${YELLOW}[1/6] Memeriksa Prasyarat Sistem...${NC}"

# Check clad.service / command-line-assistant
if ! systemctl is-active --quiet clad.service; then
    echo -e "${YELLOW}  * clad.service belum aktif. Mencoba mengaktifkan...${NC}"
    if command -v sudo >/dev/null 2>&1; then
        sudo systemctl enable --now clad.service || true
    fi
fi

if systemctl is-active --quiet clad.service; then
    echo -e "${GREEN}  ✓ Red Hat Lightspeed Daemon (clad.service) aktif.${NC}"
else
    echo -e "${RED}  ✗ Peringatan: clad.service tidak aktif. Pastikan paket 'command-line-assistant' terpasang dan sistem terdaftar di Red Hat Subscription.${NC}"
fi

# Step 2: Configure Port 80 for Non-Root User Service
echo -e "\n${YELLOW}[2/6] Mengonfigurasi Hak Port 80 (Unprivileged Port Sysctl)...${NC}"
SYSCTL_VAL=$(sysctl -n net.ipv4.ip_unprivileged_port_start 2>/dev/null || echo "1024")
if [ "$SYSCTL_VAL" -gt 80 ]; then
    echo "  * Mengatur net.ipv4.ip_unprivileged_port_start = 80..."
    if command -v sudo >/dev/null 2>&1; then
        echo "net.ipv4.ip_unprivileged_port_start = 80" | sudo tee /etc/sysctl.d/50-unprivileged-ports.conf >/dev/null
        sudo sysctl -p /etc/sysctl.d/50-unprivileged-ports.conf >/dev/null 2>&1 || true
        echo -e "${GREEN}  ✓ Sysctl port 80 berhasil dikonfigurasi permanen.${NC}"
    else
        echo -e "${RED}  ✗ Gagal menjalankan sudo untuk mengatur sysctl. Port 80 memerlukan privilege root/sysctl.${NC}"
    fi
else
    echo -e "${GREEN}  ✓ Sysctl port 80 sudah aktif (${SYSCTL_VAL} <= 80).${NC}"
fi

# Configure Firewall for HTTP if active
if command -v firewall-cmd >/dev/null 2>&1 && sudo firewall-cmd --state >/dev/null 2>&1; then
    echo "  * Memastikan service http (port 80) diizinkan pada Firewalld..."
    sudo firewall-cmd --permanent --add-service=http >/dev/null 2>&1 || true
    sudo firewall-cmd --reload >/dev/null 2>&1 || true
    echo -e "${GREEN}  ✓ Firewalld port 80 (HTTP) terbuka.${NC}"
fi

# Step 3: Copy Files
echo -e "\n${YELLOW}[3/6] Menyalin Script Bridge & Asset...${NC}"
mkdir -p "$HOME/.config/opencode"
mkdir -p "$HOME/.config/systemd/user"

cp "$SCRIPT_DIR/lightspeed_bridge.py" "$HOME/.config/opencode/lightspeed_bridge.py"
chmod +x "$HOME/.config/opencode/lightspeed_bridge.py"
echo -e "${GREEN}  ✓ Bridge script terpasang di ~/.config/opencode/lightspeed_bridge.py${NC}"

# Step 4: Systemd User Service Configuration
echo -e "\n${YELLOW}[4/6] Menyiapkan Background Service (Systemd User)...${NC}"
cp "$SCRIPT_DIR/systemd/lightspeed-bridge.service" "$HOME/.config/systemd/user/lightspeed-bridge.service"

systemctl --user daemon-reload
systemctl --user enable --now lightspeed-bridge.service

# Enable lingering so service persists after logout
if command -v loginctl >/dev/null 2>&1; then
    loginctl enable-linger "$USER" 2>/dev/null || true
fi
echo -e "${GREEN}  ✓ Service 'lightspeed-bridge.service' aktif dan berjalan di background.${NC}"

# Step 5: Configure OpenCode
echo -e "\n${YELLOW}[5/6] Mengonfigurasi Provider OpenCode...${NC}"
if [ ! -f "$HOME/.config/opencode/opencode.jsonc" ]; then
    cp "$SCRIPT_DIR/config/opencode.jsonc" "$HOME/.config/opencode/opencode.jsonc"
    echo -e "${GREEN}  ✓ File konfigurasi dibuat di ~/.config/opencode/opencode.jsonc${NC}"
else
    echo -e "${GREEN}  ✓ File konfigurasi sudah ada di ~/.config/opencode/opencode.jsonc${NC}"
fi

# Step 6: Health Verification
echo -e "\n${YELLOW}[6/6] Melakukan Verifikasi Endpoint...${NC}"
sleep 1
HEALTH_RESP=$(curl -s http://127.0.0.1/health 2>/dev/null || echo "FAILED")

if [[ "$HEALTH_RESP" == *"healthy"* ]]; then
    echo -e "${GREEN}  ✓ Health check BERHASIL: Server merespons di http://127.0.0.1/health${NC}"
else
    echo -e "${YELLOW}  ! Server sedang memulai. Cek status: systemctl --user status lightspeed-bridge.service${NC}"
fi

# Get Local IP
LOCAL_IP=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7; exit}' || echo "127.0.0.1")

echo -e "\n${BLUE}==============================================================${NC}"
echo -e "${GREEN} 🎉 INSTALASI & KONFIGURASI SELESAI DENGAN SUKSES! 🎉${NC}"
echo -e "${BLUE}==============================================================${NC}"
echo -e "
${YELLOW}1. Akses Web Portal via Browser:${NC}
   👉 Lokal   : ${GREEN}http://localhost${NC} atau ${GREEN}http://127.0.0.1${NC}
   👉 Jaringan: ${GREEN}http://${LOCAL_IP}${NC}

${YELLOW}2. Gunakan di OpenCode CLI:${NC}
   $ ${GREEN}opencode${NC}
   $ ${GREEN}opencode run --auto \"jalankan perintah uname -a dan laporkan hasilnya\"${NC}

${YELLOW}3. Perintah Manajemen Service:${NC}
   - Status : ${BLUE}systemctl --user status lightspeed-bridge.service${NC}
   - Restart: ${BLUE}systemctl --user restart lightspeed-bridge.service${NC}
   - Logs   : ${BLUE}journalctl --user -u lightspeed-bridge.service -f${NC}
"
