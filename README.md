# 🚀 Red Hat Lightspeed AI Portal & OpenCode Bridge

Bridge & Adapter HTTP kompatibel OpenAI untuk menghubungkan model **Red Hat Lightspeed AI** (`clad.service` / Command Line Assistant Daemon via D-Bus) langsung ke aplikasi **OpenCode** (dengan dukungan penuh **Agentic Tool Calling & Terminal Execution**) serta **Enterprise Web Portal** terintegrasi pada **Port 80 (HTTP)**.

---

## 📑 Daftar Isi
- [Fitur Utama](#-fitur-utama)
- [Arsitektur & Cara Kerja](#-arsitektur--cara-kerja)
- [Prasyarat Sistem (Prerequisites)](#-prasyarat-sistem-prerequisites)
- [Struktur File Proyek](#-struktur-file-proyek)
- [Tutorial Instalasi](#-tutorial-instalasi)
  - [Metode 1: Instalasi Otomatis (Direkomendasikan)](#metode-1-instalasi-otomatis-direkomendasikan)
  - [Metode 2: Instalasi Manual Langkah-demi-Langkah](#metode-2-instalasi-manual-langkah-demi-langkah)
- [Pengujian & Verifikasi](#-pengujian--verifikasi)
- [Panduan Penggunaan](#-panduan-penggunaan)
  - [1. Menggunakan OpenCode CLI (Agentic Terminal Execution)](#1-menggunakan-opencode-cli-agentic-terminal-execution)
  - [2. Menggunakan Web Portal (Browser UI)](#2-menggunakan-web-portal-browser-ui)
- [Manajemen Background Service](#-manajemen-background-service)
- [Troubleshooting & FAQ](#-troubleshooting--faq)
- [Uninstalasi](#-uninstalasi)

---

## ✨ Fitur Utama

- ⚡ **Agentic Tool Calling & Terminal Execution:** Mengonversi rekomendasi perintah RHEL dari Lightspeed menjadi OpenAI `tool_calls` standar (`bash`) sehingga OpenCode dapat mengeksekusi perintah shell langsung di terminal Anda secara otonom.
- 🔄 **Multi-Turn Terminal Feedback Loop:** Mengirim hasil eksekusi terminal (*stdout/stderr*) kembali ke Lightspeed AI untuk dianalisis dan dirangkum.
- 🌐 **Full Enterprise Web Portal (Port 80):** Antarmuka web modern berbasis Tailwind CSS, Markdown parser, dan Highlight.js di `http://localhost/` atau `http://127.0.0.1/`.
- 📑 **Product Categories & Presets:** Quick prompts untuk RHEL Core, OpenShift (OCP), RHOSO / RHOSP Cloud, Ansible & Satellite.
- 🎯 **Red Hat Certification Hub:** Lab simulator untuk persiapan ujian RHCSA (EX200), RHCE (EX294), OpenShift (EX280), dan evaluasi nilai otomatis (*AI Examiner*).
- 📜 **Raw Log Root-Cause Analyzer Modal:** Fitur paste cuplikan log (`journalctl`, `dmesg`, `oc logs`, `/var/log/messages`).
- 💾 **Multi-Session Incident Management:** Riwayat percakapan tersimpan di browser (*Local Storage*) dan dapat di-export ke Markdown (`.md`).
- 🔌 **Universal OpenAI API Compatibility:** Mendukung endpoint standar `/v1/chat/completions` (Streaming SSE & Non-Streaming) dan `/v1/models`.

---

## 🏛 Arsitektur & Cara Kerja

Daemon bawaan **Red Hat Lightspeed** (`clad.service`) berkomunikasi melalui antarmuka **Linux D-Bus System Bus** (`com.redhat.lightspeed.chat`). Bridge ini bertindak sebagai gateway di port `80`:

```
┌─────────────────────────┐          HTTP (REST / SSE)           ┌────────────────────────────┐          D-Bus IPC          ┌────────────────┐          HTTPS (mTLS)          ┌───────────────────────────┐
│       OpenCode CLI      │ ───────────────────────────────────> │    Lightspeed AI Bridge    │ ───────────────────────────> │  clad.service  │ ──────────────────────────────> │   Red Hat Cloud Engine    │
│  - Terminal Execution   │ <── tool_calls: bash ("uname -a") ── │   (lightspeed_bridge.py)   │ <── AskQuestion Response ─── │ (System Daemon)│ <── AI Inference Response ────  │ (Red Hat Lightspeed LLM)  │
│  - File Read/Write      │ ─── tool_result: Linux output ─────> │  - Port 80 HTTP Server     │ ───────────────────────────> │                │                                 └───────────────────────────┘
│  - Interactive TUI      │ <── summary: "Sistem Anda RHEL 10" ─ │  - Tool Call Translator    │                              └────────────────┘
└─────────────────────────┘                                      │  - Web Portal UI (HTML/JS) │
                                                                 └────────────────────────────┘
```

---

## 📋 Prasyarat Sistem (Prerequisites)

1. **Sistem Operasi:** Red Hat Enterprise Linux (RHEL 9 atau RHEL 10) dengan langganan (*subscription*) aktif.
2. **Command Line Assistant terpasang & aktif:**
   ```bash
   sudo dnf install -y command-line-assistant
   sudo systemctl enable --now clad.service
   ```
3. **Python 3:** Menggunakan pustaka standar Python dan `dasbus` (otomatis terpasang bersama `command-line-assistant`).
4. **Aplikasi OpenCode:** Sudah terinstal di mesin lokal:
   ```bash
   curl -fsSL https://opencode.ai/install | bash
   ```

---

## 📁 Struktur File Proyek

```text
lightspeed-opencode-bridge/
├── config/
│   └── opencode.jsonc               # Konfigurasi provider OpenCode (baseURL: http://127.0.0.1/v1)
├── systemd/
│   └── lightspeed-bridge.service    # Unit file systemd user untuk auto-start
├── lightspeed_bridge.py             # Server HTTP Bridge & Enterprise Web Portal UI
├── install.sh                       # Skrip instalasi otomatis (Port 80, Sysctl, Service)
├── uninstall.sh                     # Skrip uninstalasi bersih
├── test_bridge.sh                   # Skrip pengujian endpoint API
├── CUSTOMIZATION.md                 # Panduan kustomisasi UI, Quick Prompts & Tema
├── .gitignore                       # File pengecualian Git
└── README.md                        # Dokumentasi & panduan lengkap ini
```

---

## 🛠 Tutorial Instalasi

### Metode 1: Instalasi Otomatis (Direkomendasikan)

1. Masuk ke direktori repositori:
   ```bash
   cd /home/ridwan/lightspeed-opencode-bridge
   ```

2. Jalankan skrip installer:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

Installer akan secara otomatis:
- Memeriksa keaktifan `clad.service`.
- Mengonfigurasi `net.ipv4.ip_unprivileged_port_start = 80` di sysctl agar service user non-root dapat membuka port 80.
- Membuka port HTTP (80) pada Firewalld (jika aktif).
- Menyalin file script bridge dan mendaftarkan `lightspeed-bridge.service`.
- Mengaktifkan *lingering* (`loginctl enable-linger`) agar service tetap hidup meskipun user logout.
- Mengonfigurasi file `~/.config/opencode/opencode.jsonc`.

---

### Metode 2: Instalasi Manual Langkah-demi-Langkah

Jika Anda ingin melakukan instalasi secara manual:

#### Langkah 1: Izinkan Port 80 untuk User Non-Root
```bash
echo "net.ipv4.ip_unprivileged_port_start = 80" | sudo tee /etc/sysctl.d/50-unprivileged-ports.conf
sudo sysctl -p /etc/sysctl.d/50-unprivileged-ports.conf
```

#### Langkah 2: Buka Port 80 di Firewalld
```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload
```

#### Langkah 3: Pasang Script Bridge
```bash
mkdir -p ~/.config/opencode
cp lightspeed_bridge.py ~/.config/opencode/lightspeed_bridge.py
chmod +x ~/.config/opencode/lightspeed_bridge.py
```

#### Langkah 4: Pasang & Aktifkan Systemd User Service
```bash
mkdir -p ~/.config/systemd/user
cp systemd/lightspeed-bridge.service ~/.config/systemd/user/lightspeed-bridge.service
systemctl --user daemon-reload
systemctl --user enable --now lightspeed-bridge.service
loginctl enable-linger "$USER"
```

#### Langkah 5: Konfigurasikan OpenCode
Buat file `~/.config/opencode/opencode.jsonc`:
```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "model": "lightspeed/rhel-lightspeed",
  "provider": {
    "lightspeed": {
      "name": "Red Hat Lightspeed",
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "baseURL": "http://127.0.0.1/v1",
        "apiKey": "local-dummy-key"
      },
      "models": {
        "rhel-lightspeed": {
          "name": "RHEL Lightspeed AI"
        }
      }
    }
  }
}
```

---

## 🔍 Pengujian & Verifikasi

1. **Uji Health Check API:**
   ```bash
   curl -s http://127.0.0.1/health
   ```
   *Output yang diharapkan:* `{"status": "healthy", ...}`

2. **Jalankan Skrip Uji Bawaan:**
   ```bash
   ./test_bridge.sh
   ```

3. **Cek Ketersediaan Model di OpenCode:**
   ```bash
   opencode models lightspeed
   ```
   *Output yang diharapkan:* `lightspeed/rhel-lightspeed`

---

## 📖 Panduan Penggunaan

### 1. Menggunakan OpenCode CLI (Agentic Terminal Execution)

- **Mode Interaktif TUI (Full Dashboard):**
  ```bash
  opencode
  ```

- **Eksekusi Perintah Terminal Otomatis:**
  ```bash
  # Cek arsitektur & kernel
  opencode run --auto "jalankan perintah uname -a dan laporkan hasilnya"

  # Cek status service sistem
  opencode run --auto "cek status service clad dan firewalld"

  # Pembuatan & eksekusi script
  opencode run --auto "buat file /tmp/check_disk.sh yang berisi df -h dan jalankan"
  ```

- **Tanya Jawab / Konsultasi Konsep:**
  ```bash
  opencode run "Jelaskan langkah konfigurasi LACP bonding di RHEL 10"
  ```

---

### 2. Menggunakan Web Portal (Browser UI)

Buka browser di komputer Anda atau perangkat lain di jaringan lokal:
👉 **`http://localhost`** atau **`http://127.0.0.1`** (atau via IP server: `http://<ip-server>`)

**Fitur yang Tersedia di Web Portal:**
- **Product Categories:** Klik tab RHEL, OpenShift, Cloud, Ansible, atau Cert Prep untuk memunculkan rekomendasi prompt.
- **Log Analyzer:** Klik tombol *"Log Analyzer"* di header untuk menempelkan log error dari `journalctl` atau `dmesg`.
- **New Thread / Multi-Session:** Klik tombol *"+ New Thread"* untuk membuat investigasi baru. Riwayat disimpan otomatis di browser.
- **Export Markdown:** Klik tombol download di header untuk menyimpan percakapan ke file `.md`.
- **Copy Code:** Klik tombol *Copy* pada setiap blok kode perintah atau playbook.

---

## ⚙️ Manajemen Background Service

* **Melihat status:**
  ```bash
  systemctl --user status lightspeed-bridge.service
  ```
* **Restart service:**
  ```bash
  systemctl --user restart lightspeed-bridge.service
  ```
* **Melihat log real-time:**
  ```bash
  journalctl --user -u lightspeed-bridge.service -f
  ```
* **Menghentikan service:**
  ```bash
  systemctl --user stop lightspeed-bridge.service
  ```

---

## ❓ Troubleshooting & FAQ

#### 1. Port 80 Permission Denied saat menjalankan manual
Pastikan sysctl unprivileged port sudah aktif:
```bash
sudo sysctl -w net.ipv4.ip_unprivileged_port_start=80
```

#### 2. OpenCode meminta izin eksekusi perintah shell
Secara default, OpenCode meminta konfirmasi keamanan sebelum menjalankan perintah bash (`[y/N]`). Tambahkan flag `--auto` jika ingin eksekusi otomatis tanpa konfirmasi:
```bash
opencode run --auto "perintah..."
```

#### 3. Error `Communication error with the server` dari Lightspeed
Pastikan mesin RHEL terdaftar pada Red Hat Subscription Manager:
```bash
sudo subscription-manager register
```

---

## 🗑️ Uninstalasi

Jika Anda ingin menghapus service dan script bridge:
```bash
chmod +x uninstall.sh
./uninstall.sh
```

---

## 📄 Lisensi
Didistribusikan di bawah lisensi MIT.
