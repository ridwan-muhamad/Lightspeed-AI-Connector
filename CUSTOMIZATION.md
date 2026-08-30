# Panduan Kustomisasi & Desain Tampilan (UI) • Red Hat Lightspeed Web Portal

Dokumen ini menjelaskan cara memodifikasi, mempercantik, dan menambahkan fitur baru pada antarmuka web (*Frontend*) maupun konfigurasi backend **Red Hat Lightspeed Web Portal**.

---

## 📍 Lokasi Kode Tampilan

Seluruh antarmuka web (HTML, CSS, dan JavaScript) berada di dalam variabel `WEB_UI_HTML` pada file:
```text
lightspeed_bridge.py
```

---

## 🎨 1. Menambah atau Mengubah Quick Prompts & Kategori

Quick prompt diatur oleh objek JavaScript `CATEGORY_PROMPTS` di dalam `lightspeed_bridge.py`.

### Cara Menambah Prompt Baru pada Kategori yang Ada:
Buka `lightspeed_bridge.py`, cari `const CATEGORY_PROMPTS`, dan tambahkan item baru:
```javascript
const CATEGORY_PROMPTS = {
    rhel: [
        { 
            title: 'Kernel Crash Dump (kdump)', 
            prompt: 'Bagaimana cara mengonfigurasi kdump di RHEL 10 dan menguji trigger crash dump?' 
        },
        // Tambahkan prompt RHEL lainnya di sini...
    ],
    ocp: [
        // Prompt OpenShift...
    ],
    cloud: [
        // Prompt RHOSO / RHOSP...
    ],
    ansible: [
        // Prompt Ansible & Satellite...
    ]
};
```

### Cara Menambah Kategori Produk Baru:
1. Tambahkan tombol tab baru pada bagian HTML `#tab-...`:
   ```html
   <button onclick="switchCategory('storage')" id="tab-storage" class="category-tab p-2 rounded-lg border border-rh-border text-left text-slate-400 hover:text-white font-medium transition flex items-center space-x-2">
       <i class="fa-solid fa-hard-drive text-amber-400"></i>
       <span>Storage (Ceph)</span>
   </button>
   ```
2. Tambahkan data prompt di `CATEGORY_PROMPTS`:
   ```javascript
   storage: [
       { title: 'Ceph OSD Recovery', prompt: 'Bagaimana cara menangani OSD down di Red Hat Ceph Storage?' }
   ]
   ```

---

## 🎯 2. Mengubah Skema Warna & Tema (Tailwind CSS)

Warna tema enterprise didefinisikan pada objek `tailwind.config` di bagian `<head>`:

```javascript
tailwind.config = {
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                rh: {
                    red: '#EE0000',      // Warna merah utama Red Hat
                    darkred: '#A30000',  // Merah gelap untuk gradien
                    black: '#151515',    // Warna hitam kode pre/block
                    dark: '#0F1216',     // Background utama halaman
                    panel: '#1B1D21',    // Background sidebar & header
                    card: '#212429',     // Background kartu & popup
                    border: '#383B40',   // Warna garis border
                    accent: '#4B88EC'    // Warna aksen link / info
                }
            }
        }
    }
}
```

---

## 🏷️ 3. Mengubah Header, Logo, dan Judul Portal

Di bagian tag `<header>`, Anda dapat menyesuaikan teks dan branding organisasi Anda:

```html
<!-- Logo & Title -->
<div class="flex items-center space-x-2">
    <h1 class="font-bold text-sm sm:text-base tracking-wide text-white">Red Hat Lightspeed AI</h1>
    <span class="bg-red-500/15 text-red-400 text-[10px] px-2 py-0.5 rounded border border-red-500/30 font-semibold uppercase">Enterprise</span>
</div>
<p class="text-[11px] text-slate-400 hidden sm:block">AI Assistant for Linux & OpenShift Administrators</p>
```

---

## 🃏 4. Mengubah Kartu Bantuan Halaman Depan (*Welcome Hub*)

Kartu rekomendasi yang muncul saat percakapan masih kosong berada di `<div id="welcomeHub">`. Anda dapat mengubah skenario kasus, ikon [FontAwesome](https://fontawesome.com/), maupun deskripsi singkatnya:

```html
<div class="bg-rh-panel hover:bg-rh-card p-4 rounded-xl border border-rh-border hover:border-red-500/50 cursor-pointer transition flex flex-col justify-between group"
     onclick="usePrompt('RHEL', 'Pertanyaan atau instruksi template Anda...')">
    <div>
        <div class="w-8 h-8 rounded-lg bg-red-500/10 text-red-400 flex items-center justify-center mb-3">
            <i class="fa-solid fa-server"></i>
        </div>
        <h3 class="font-semibold text-sm text-slate-200 mb-1">Judul Skenario</h3>
        <p class="text-xs text-slate-400">Deskripsi singkat fungsi bantuan ini.</p>
    </div>
    <span class="text-[11px] text-red-400 font-medium mt-3">Gunakan Template →</span>
</div>
```

---

## 🔌 5. Mengubah Port atau Host Binding

Secara default aplikasi berjalan di `0.0.0.0:80`. Untuk mengubah port (misal ke port `8088`):

1. **Jalankan manual**:
   ```bash
   python3 lightspeed_bridge.py 8088 0.0.0.0
   ```
2. **Atau ubah konfigurasi systemd**:
   Edit file `/home/ridwan/.config/systemd/user/lightspeed-bridge.service`:
   ```ini
   ExecStart=/usr/bin/python3 %h/lightspeed-webchat/lightspeed_bridge.py 8088 0.0.0.0
   ```
   Lalu reload dan restart:
   ```bash
   systemctl --user daemon-reload
   systemctl --user restart lightspeed-bridge.service
   ```
   *(Jangan lupa buka port baru di firewalld jika diakses dari luar: `sudo firewall-cmd --permanent --add-port=8088/tcp && sudo firewall-cmd --reload`)*

---

## 🔄 6. Workflow Menerapkan Perubahan

Setiap kali Anda selesai melakukan edit pada `lightspeed_bridge.py`:

```bash
# 1. Restart service backend
systemctl --user restart lightspeed-bridge.service

# 2. Cek apakah ada error penulisan syntax di log
journalctl --user -u lightspeed-bridge.service -n 20 --no-pager
```

```text
# 3. Refresh Browser
Buka browser dan lakukan Hard Refresh (Ctrl + Shift + R atau Shift + F5) 
agar cache CSS/JS di browser langsung ter-update.
```
