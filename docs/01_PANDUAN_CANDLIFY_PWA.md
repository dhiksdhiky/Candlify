# 📱 PANDUAN PENGGUNAAN CANDLIFY PWA & KAMUS FITUR

> **Buku Manual Resmi Candlify v2.2 — Antarmuka Pengguna & Navigasi Kuantitatif**  
> *Panduan komprehensif seluruh modul analitik, navigasi 5 tab, keterangan setiap tombol & tools chart, badge Order Flow, kalkulator position sizing money management, serta log pembaruan terkini.*

---

## 📑 DAFTAR ISI
1. [Sekilas tentang Candlify V2](#1-sekilas-tentang-candlify-v2)
2. [Navigasi 5 Tab Utama](#2-navigasi-5-tab-utama)
3. [Kamus Tombol & Fitur Chart Interaktif](#3-kamus-tombol--fitur-chart-interaktif)
4. [Membaca Order Flow & Broker Summary](#4-membaca-order-flow--broker-summary)
5. [Manajemen Watchlist & Multi-Kategori](#5-manajemen-watchlist--multi-kategori)
6. [Kalkulator Trading Plan & Position Sizing](#6-kalkulator-trading-plan--position-sizing)
7. [Pengaturan Feed & Preferensi Akun](#7-pengaturan-feed--preferensi-akun)
8. [🚀 Catatan Rilis & Log Pembaruan (Changelog)](#8--catatan-rilis--log-pembaruan-changelog)

---

## 1. Sekilas tentang Candlify V2

**Candlify V2** adalah aplikasi analisis pasar saham Bursa Efek Indonesia (IDX) berbasis Progressive Web App (PWA) yang menggabungkan:
* **Analisis Teknikal Presisi**: Charting profesional bertenaga KLineCharts v9 dengan overlay canvas khusus.
* **Deteksi Mikrostruktur Bandarmologi**: Pelacakan akumulasi dan distribusi *Smart Money* secara real-time berbasis data resmi bursa.
* **Position Sizing & Money Management**: Menghitung alokasi lot dan batas risiko rupiah secara matematis sebelum tombol buy ditekan.

Aplikasi ini dapat diakses melalui browser komputer maupun diinstal sebagai aplikasi native di layar utama (home screen) smartphone Android/iOS tanpa perlu melalui app store.

---

## 2. Navigasi 5 Tab Utama

Di bagian bawah layar (Floating Glass Bottom Navigation), tersedia 5 menu utama:

| Tab | Ikon | Fungsi Utama |
|---|:---:|---|
| **Database** | 🗄️ | Pusat sinkronisasi database Neon PostgreSQL, kalender bursa, riwayat data historis emiten, dan ringkasan status engine. |
| **Screener** | 🔍 | Penyaring saham otomatis berbasis algoritma Pre-Breakout Base V2, ranking skor dominansi, filter papan bursa, dan pencarian cepat. |
| **Chart** | 📈 | Area kerja analisis teknikal utama: candlestick multi-timeframe, indikator MA20, volume, SnR lines, serta badge Order Flow bandar. |
| **Watchlist** | ⭐ | Manajemen daftar pantau saham dengan pengelompokan multi-kategori, target entry, catatan personal, dan pembuatan trading plan. |
| **Settings** | ⚙️ | Pengaturan preferensi akun: modal portofolio, batas toleransi risiko per posisi, feed candlestick harian, serta pusat buku panduan edukasi. |

---

## 3. Kamus Tombol & Fitur Chart Interaktif

Saat membuka tab **Chart**, antarmuka terbagi menjadi beberapa area kendali yang dirancang hemat tempat:

### A. Bar Atas (Top Header Controls)
1. **Pilihan Kode Saham (Ticker Bar)**: 
   * Menampilkan kode saham aktif (contoh: `BBRI`, `BALI`).
   * Klik pada kode saham untuk membuka modal pencarian cepat (*Quick Ticker Search*).
2. **Top Stock Switcher Bar (Daftar Saham Horizontal)**:
   * Bar horizontal tepat di atas chart yang dapat di-swipe ke kanan dan kiri.
   * Menampilkan daftar saham pilihan (dari watchlist atau hasil screener) lengkap dengan harga terakhir dan persentase perubahan hari ini.
   * Sekali tap pada salah satu saham, chart langsung berganti secara instan tanpa perlu kembali ke menu screener.
3. **Badge Order Flow Bandar (`📊 🟢 +1.2B • HMB 4.850`)**:
   * **Warna Hijau (`🟢`)**: Smart Money berada dalam fase **Net Akumulasi**.
   * **Warna Merah (`🔴`)**: Smart Money berada dalam fase **Net Distribusi**.
   * **Nominal Flow (`+1.2B` / `-500M`)**: Nilai bersih transaksi Top-3 broker buyer/seller (Miliar / Juta Rupiah).
   * **HMB (`HMB Rp 4.850`)**: *Harga Modal Bandar* tertimbang rata-rata kumulatif.
   * *Tips:* Klik badge ini untuk membuka lembar detail Broker Flow & Broksum harian.
4. **Tombol Bintang ⭐ (Watchlist Action)**:
   * Menandai apakah saham saat ini sudah tersimpan di watchlist.
   * Jika ikon bergaris putih (`☆`): Saham belum ada di watchlist. Sekali klik akan membuka modal penyimpanan.
   * Jika ikon kuning menyala (`⭐`): Saham sudah ada di watchlist. Klik untuk mengubah kategori atau melihat catatan.

### B. Bar Indikator & Timeframe
1. **Timeframe Pills (`1D`, `1W`, `1M`, `1h`, `15m`, `5m`, `1m`)**:
   * Mengubah periode candle chart. Default adalah `1D` (Harian).
2. **Tombol `MA20`**:
   * Mengaktifkan/menonaktifkan garis rata-rata 20 hari bursa (garis oranye tipis). Dalam strategi Pre-Breakout, harga wajib bertahan di atas MA20.
3. **Tombol `SnR` (Support & Resistance)**:
   * Menghitung dan menggambar garis otomatis pivot support dan resistance horizontal berbasis harga tertinggi/terendah historis.
4. **Tombol `⚙️ SnR`**:
   * Mengatur sensitivitas deteksi titik pivot SnR (periode swing high/low).

---

## 4. Membaca Order Flow & Broker Summary

Ketika badge Order Flow di atas chart diklik, muncul panel interaktif di bagian bawah:

### A. Tab Ringkasan Broksum (Broker Summary)
* **Top 1 Buyer & Seller**: Broker dengan akumulasi atau distribusi terbesar hari ini.
* **Top 3 & Top 5 Concentration**: Persentase dominasi volume broker teratas terhadap total transaksi bursa. Jika Top-3 menguasai > 60%, pergerakan harga berada dalam kendali kuat satu konsorsium.

### B. Tab Daily Activity & Broker Flow
* **Tombol Broker Interaktif**: Menampilkan daftar broker yang aktif bertransaksi pada saham tersebut (diurutkan dari broker paling akumulatif di sebelah kiri).
* **Klik Tombol Broker**: Memfilter pergerakan harga dan riwayat beli/jual spesifik hanya untuk broker yang dipilih.
* **Grafik Aliran Kumulatif (Broker Flow Line)**: Memperlihatkan grafik apakah broker tertentu konsisten menambah barang (grafik menanjak) atau diam-diam membuang barang saat harga naik (grafik menukik/divergence).

---

## 5. Manajemen Watchlist & Multi-Kategori

Tab Watchlist didesain fleksibel untuk memisahkan saham berdasarkan gaya trading atau status setup:

1. **Tab Kategori Pinned ("Semua")**:
   * Menampilkan seluruh saham dari semua kategori dalam satu daftar terpadu.
   * Di sebelah tombol *Semua*, terdapat tombol gerigi `⚙️` untuk mengelola, menambah, atau mengubah nama kategori watchlist.
2. **Kategori Kustom (Swipeable Chips)**:
   * Geser ke kanan untuk melihat kategori khusus seperti `💥 Breakout`, `Swing`, `Pantau`, atau nama buatan sendiri.
3. **Penyimpanan Multi-Kategori (Modal Bintang ⭐)**:
   * Satu saham dapat dimasukkan ke dalam beberapa kategori sekaligus (misal: *BBRI* masuk ke `Swing` sekaligus `Pantau Dividen`).
   * Tampilan modal terbuka bersih tanpa flicker, memberikan kebebasan memilih kategori sebelum menekan tombol simpan.
4. **Tombol Aksi pada Kartu Watchlist**:
   * `🎯 Target/Plan`: Membuka modal kalkulator Trading Plan untuk menghitung lot dan stop loss.
   * `✏️ Edit`: Mengubah catatan (*notes*) dan kategori watchlist.
   * `🗑️ Hapus`: Menghapus saham dari watchlist terpilih.

---

## 6. Kalkulator Trading Plan & Position Sizing

Fitur Trading Plan menerapkan disiplin *Dual-Constraint Position Sizing* profesional:

### Rumus Matematis:
$$\text{Nominal Risiko} = \text{Total Modal Portofolio} \times \text{Toleransi Risiko \%}$$

$$\text{Jarak Risiko per Lembar} = \text{Harga Entry} - \text{Level Stop Loss}$$

$$\text{Alokasi Lot Maksimal} = \left\lfloor \frac{\text{Nominal Risiko}}{\text{Jarak Risiko per Lembar} \times 100} \right\rfloor$$

### Keamanan Tambahan:
* **Cap Maksimum Alokasi**: Sistem membatasi nilai total pembelian tidak boleh melebihi persentase modal yang aman (default: maksimal 25% modal per posisi saham) guna menghindari konsentrasi risiko yang berlebihan (*over-betting*).
* **Perhitungan Risk-to-Reward (RRR)**: Membandingkan potensi keuntungan hingga target resisten dengan jarak risiko stop loss. Disarankan hanya mengambil setup dengan $\text{RRR} \ge 1:2$.

---

## 7. Pengaturan Feed & Preferensi Akun

Di tab **Settings**, Mas Dhika dapat menyesuaikan konfigurasi mesin sesuai kenyamanan:

1. **Sumber Data 1D (`⚡ Neon DB` vs `🌐 Yahoo`)**:
   * **Neon DB**: Mengambil candlestick langsung dari database master internal yang tersinkronisasi dengan data resmi bursa dan broksum.
   * **Yahoo**: Mengambil candlestick langsung dari feed Yahoo Finance sebagai pembanding cadangan.
2. **Total Modal Portofolio & Toleransi Risiko**:
   * Input nominal modal trading riil yang dimiliki (contoh: Rp 50.000.000).
   * Slider toleransi risiko per posisi (contoh: 1.0% = Rp 500.000).
   * Nilai ini secara otomatis menjadi acuan dasar pada seluruh kalkulator Trading Plan dan Screener.
3. **Pusat Panduan & Dokumentasi Dinamis**:
   * Mengakses seluruh buku materi strategi, teori bandarmologi, dan modul SOP langsung di dalam aplikasi.

---

## 8. 🚀 Catatan Rilis & Log Pembaruan (Changelog)

### Versi 2.2 — Rilis Terbaru (Oktober 2026)
* ✨ **Pusat Dokumentasi Dinamis**: Seluruh panduan dipecah modular ke dalam file Markdown yang disinkronisasi langsung oleh server secara otomatis.
* 🧹 **Simplifikasi Tab Settings**: Desain ultra-clean dengan segmented switch pills, penghapusan dropdown kategori default yang mubazir, dan ringkasan footer arsitektur minimalis.
* 🛡️ **Eliminasi Watchlist Flicker**: Modal bintang ⭐ kini terbuka bersih tanpa flicker auto-unselect untuk pengalaman pengguna PWA smartphone yang mulus.
* 📊 **Compact Order Flow Badge**: Teks badge chart diperingkas (`📊 🟢 +1.2B • HMB 4.850`) dengan proteksi single-line agar tidak turun ke baris kedua di layar HP.
* 🎛️ **Swipeable Broker Flow Buttons**: Urutan broker diurutkan secara cerdas dengan broker akumulasi teratas di paling kiri.
* ⭐ **Default View "Semua" pada Watchlist**: Tombol "Semua" dipin permanen di sebelah ikon pengaturan kategori, memudahkan navigasi cepat seluruh portofolio pantauan.
* 📅 **Sinkronisasi Kalender Bursa Otomatis**: Integrasi batch downloader kalender bursa konsensus dengan fallback aman terhadap hari libur pasar modal.

---
*Dokumen ini diperbarui secara berkala mengikuti perkembangan dan peningkatan fitur Candlify.*
