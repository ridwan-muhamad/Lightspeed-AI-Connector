# 📌 Project Description: Red Hat Lightspeed AI Bridge & Enterprise Web Portal

### 🏷️ Ringkasan Singkat (*Elevator Pitch*)
> **Red Hat Lightspeed AI Bridge** adalah gateway dan adaptor cerdas yang menjembatani model kecerdasan buatan resmi **Red Hat Lightspeed** (`clad.service`) ke dalam ekosistem alat pengembangan modern (khususnya **OpenCode CLI**) melalui protokol standar **OpenAI-Compatible REST/SSE API**, sekaligus menyediakan **Enterprise Web Portal** interaktif pada Port 80 (HTTP) untuk mempermudah administrasi sistem Linux, diagnosa *troubleshooting*, dan persiapan ujian sertifikasi Red Hat.

---

## 1. ❓ Apa Itu Project Ini?

Secara *default*, Red Hat Lightspeed pada RHEL 10 berjalan sebagai layanan latar belakang (*system daemon*) yang hanya dapat diakses melalui antarmuka **Linux D-Bus IPC** lokal (`com.redhat.lightspeed.chat`) dan terbatas sebagai asisten teks penasihat (*advisory-only*).

Project ini hadir sebagai **jembatan multifungsi (*all-in-one bridge*)** yang mengubah keterbatasan tersebut menjadi solusi produktivitas lengkap dengan:
1. **Membuka antarmuka HTTP REST/SSE yang kompatibel dengan OpenAI API**, sehingga model Red Hat Lightspeed dapat digunakan langsung oleh berbagai AI CLI agent (seperti OpenCode), extension editor (seperti Continue.dev/VSCode), maupun skrip kustom.
2. **Menyediakan Engine Penerjemah Tool Call (*Agentic Tool Calling Translator*)**, yang secara cerdas mendeteksi rekomendasi perintah dari Lightspeed dan mengubahnya menjadi aksi eksekusi terminal shell (`bash`) nyata di mesin lokal pengguna secara aman dan otomatis.
3. **Menyediakan Enterprise Web Portal Modern (Port 80)**, sebuah aplikasi web berbasis browser dengan antarmuka gelap modern, template prompt siap pakai lintas ekosistem Red Hat, analisa log mentah, dan manajemen sesi investigasi.

---

## 2. 🏛️ Bagaimana Cara Kerjanya?

Bridge ini bekerja dengan menghubungkan layer D-Bus lokal di sistem operasi RHEL dengan protokol HTTP standar melalui alur berikut:

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       USER INTERACTION LAYER                                     │
│                                                                                                  │
│   [ OpenCode CLI / Terminal Agent ]              [ Browser Web Portal (http://localhost) ]       │
└─────────────────────────────────┬────────────────────────────────┬───────────────────────────────┘
                                  │                                │
                                  │ HTTP REST / SSE (Port 80)      │
                                  ▼                                ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                    LIGHTSPEED AI BRIDGE & WEB PORTAL (lightspeed_bridge.py)                      │
│                                                                                                  │
│  • OpenAI Protocol Engine (/v1/chat/completions, /v1/models)                                     │
│  • Agentic Tool Calling Translator (Mendeteksi Bash Block -> Mengubah ke OpenAI tool_calls)       │
│  • Multi-Turn Terminal Feedback Handler (Mengirim Output Terminal ke Lightspeed untuk Dirangkum) │
│  • Web Portal UI Server (Tailwind CSS, Highlight.js, Session Manager, Log Modal)                 │
└─────────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                  │
                                                  │ Linux D-Bus IPC (dasbus / System Bus)
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               RHEL SYSTEM DAEMON (clad.service)                                  │
│                                                                                                  │
│  • Command Line Assistant Daemon (UID Authentication & Local Session Management)                 │
└─────────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                  │
                                                  │ HTTPS / mTLS (Red Hat Enterprise Subscription)
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 RED HAT CLOUD INFERENCE ENGINE                                   │
│                                                                                                  │
│  • Enterprise LLM yang dilatih khusus dengan Red Hat Knowledgebase, Man Pages, & Best Practices  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Alur Eksekusi Perintah Terminal (*Agentic Workflow*):
1. **User Prompt:** Pengguna memberi perintah di terminal, misal: `opencode run --auto "cek kapasitas disk dan buatkan report ke file /tmp/disk.txt"`.
2. **Konteks Lingkungan:** Bridge memformulasikan instruksi agar Lightspeed merespons dalam format perintah shell ```bash``` yang valid.
3. **Tool Call Generation:** Bridge mengekstrak blok bash tersebut dan membungkusnya sebagai payload `tool_calls` OpenAI (`name: "bash"`).
4. **Eksekusi Lokal:** OpenCode menerima `tool_call`, lalu mengeksekusi perintah shell langsung di terminal lokal pengguna.
5. **Feedback & Rangkuman:** Hasil keluaran (*stdout/stderr*) terminal dikirim kembali ke Lightspeed melalui bridge untuk dianalisis dan dirangkum menjadi laporan akhir yang rapi kepada pengguna.

---

## 3. ⚙️ Fungsi & Fitur Utama

| Fitur | Deskripsi |
| :--- | :--- |
| **Terminal Tool Calling** | Mengeksekusi perintah shell, manajemen file, dan skrip secara otonom di terminal lokal melalui OpenCode. |
| **Multi-Turn Feedback Loop** | Menganalisis output hasil perintah terminal (*exit code, log, output text*) secara interaktif. |
| **Default HTTP Port 80** | Web portal dapat langsung dibuka via browser tanpa perlu mengetik nomor port (`http://localhost` / `http://<IP-Server>`). |
| **Product-Categorized Prompts** | Tab kategori siap pakai: **RHEL Core**, **OpenShift (OCP)**, **RHOSO / RHOSP Cloud**, dan **Ansible & Satellite**. |
| **Red Hat Certification Hub** | Simulator lab interaktif dan penilaian otomatis (*AI Examiner*) untuk ujian **RHCSA (EX200)**, **RHCE (EX294)**, **OpenShift (EX280)**, dan **EX188**. |
| **Raw Log Analyzer** | Modal pop-up khusus untuk menempelkan cuplikan log mentah (`journalctl`, `dmesg`, `oc logs`) guna menemukan akar masalah (*Root Cause Analysis*). |
| **Multi-Session Management** | Menyimpan riwayat percakapan secara lokal di browser, mendukung multi-thread investigasi, dan export ke file Markdown (`.md`). |
| **High-Contrast Citations** | Menampilkan rujukan artikel resmi Red Hat Knowledgebase & dokumentasi teknis dengan tampilan link berdesain kontras tinggi. |

---

## 4. 💡 Manfaat & Nilai Tambah

1. **Efisiensi Waktu SysAdmin & DevOps:**
   - Tidak perlu lagi beralih antara browser dan terminal untuk mencari sintaks perintah `nmcli`, `podman`, `pcs`, `sysctl`, atau playbook Ansible.
   - Diagnosa *error* sistem dapat dilakukan dalam hitungan detik menggunakan fitur *Log Analyzer*.

2. **Otomatisasi Tugas Terminal yang Aman:**
   - Dengan integrasi OpenCode, perintah dapat dieksekusi secara terpandu dengan konfirmasi keamanan pengguna (`[y/N]`) atau secara otomatis via flag `--auto`.

3. **Maksimalisasi Langganan Red Hat (*Cost-Efficient*):**
   - Memanfaatkan model AI enterprise resmi yang sudah termasuk dalam langganan Red Hat Enterprise Linux tanpa perlu membayar biaya token API pihak ketiga (seperti OpenAI GPT-4 atau Claude).

4. **Keamanan & Privasi Enterprise:**
   - Komunikasi backend menggunakan mTLS resmi terautentikasi Red Hat Subscription Manager; bridge berjalan secara lokal (*in-memory*) di mesin Anda tanpa menyimpan log sensitif ke server eksternal perantara.

5. **Akselerasi Belajar & Sertifikasi:**
   - Menjadi asisten belajar interaktif (*Personal AI Mentor*) untuk simulasi ujian sertifikasi Red Hat berstandar industri.
