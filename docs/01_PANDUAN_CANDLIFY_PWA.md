# 📱 PANDUAN PENGGUNAAN CANDLIFY PWA & KAMUS FITUR

> **Buku Manual Resmi Candlify v2.5 — Antarmuka Pengguna & Navigasi Kuantitatif**  
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
3. **Badge Order Flow Bandar (`🟢 +1.2B • 🌐 +24M • HMB 4.850`)**:
   * **Warna Hijau (`🟢`)**: Smart Money berada dalam fase **Net Akumulasi**.
   * **Warna Merah (`🔴`)**: Smart Money berada dalam fase **Net Distribusi**.
   * **Nominal Flow (`+1.2B` / `-500M`)**: Nilai bersih transaksi Top-3 broker buyer/seller (Miliar / Juta Rupiah).
   * **Flow Asing (`🌐 +24M`)**: Nilai net inflow/outflow investor asing hari ini.
   * **HMB (`HMB Rp 4.850`)**: *Harga Modal Bandar* tertimbang rata-rata kumulatif.
   * *Desain Ramping:* Ikon grafik batang disederhanakan agar seluruh metrik penting muat rapi dalam 1 baris di layar smartphone.
   * *Tips:* Klik badge ini untuk membuka lembar detail Broker Summary & Market Intelligence.
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

Ketika badge Order Flow di atas chart diklik, muncul lembar panel interaktif (**Order Flow & Intelligence Bottom Sheet**). Seluruh tampilan dirancang dengan arsitektur **Kanan-Kiri Kompak (Side-by-Side)** yang simetris, baik di desktop maupun layar HP smartphone:

```
┌────────────────────────────────────────────────────────┐
│  Net Flow Bandar  │  Harga Modal (HMB)  │  Rasio Buy/Sell│
├────────────────────────────────────────────────────────┤
│  [======== Buy 51% ========][======== Sell 49% =======]│
├────────────────────────────┬───────────────────────────┤
│ 🌐 Foreign Flow (Kiri)     │ 🐳 Trade Size & Nego (Kanan│
│ Net 1D │ Net 5D │ Net 20D  │ Lot/Trd │ Rerata 20H│ Nego│
├────────────────────────────┼───────────────────────────┤
│ 🟢 TOP BUYERS (Kiri)       │ 🔴 TOP SELLERS (Kanan)    │
│ Broker │ Lot │ Val │ Avg   │ Broker │ Lot │ Val │ Avg  │
└────────────────────────────┴───────────────────────────┘
```

### A. Ringkasan Arus Modal Utama (Top Bar & Ratio)
* **Net Flow Bandar**: Nominal akumulasi/distribusi bersih Top 3 broker penentu arah harga.
* **Harga Modal (HMB)**: Estimasi rata-rata harga beli bandar sebagai level jangkar support dinamis.
* **Rasio Buy / Sell**: Perbandingan visual kekuatan beli versus jual dalam persentase.

### B. Intelijen Pasar Kanan-Kiri (Market Intelligence Strip)
Tepat di bawah rasio buy/sell, terdapat dua kartu berdampingan (kanan-kiri) yang memberikan konfirmasi lapis kedua:
1. **🌐 Foreign Flow (Asing) — Kolom Kiri**:
   * **Net 1D**: Transaksi bersih investor asing hari ini (Inflow/Outflow).
   * **Net 5D & Net 20D**: Akumulasi bergulir 5 hari bursa (~1 minggu) dan 20 hari bursa (~1 bulan) untuk melihat apakah asing sedang konsisten masuk (*inflow*) atau keluar bertahap (*outflow*).
   * **Buy vs Sell Lot**: Detail volume pembelian vs penjualan lot asing secara riil.
2. **🐳 Trade Size & Pasar Nego — Kolom Kanan**:
   * **Lot per Trade (`Lot/Trd`)**: Rata-rata lot per satu kali transaksi (`Volume / Frekuensi / 100`).
   * **Rerata 20H**: Baseline rata-rata lot per transaksi selama 20 hari bursa terakhir.
   * **Badge Whale / Ritel**: 
     * `🐳 Whale (>= 1.5x)`: Transaksi didominasi pemain bermodal jumbo / institusi.
     * `🦐 Ritel (<= 0.75x)`: Transaksi didominasi investor ritel kecil.
     * `Normal`: Pola transaksi reguler berimbang.
   * **Pasar Nego (`Nego`)**: Menampilkan nilai transaksi non-reguler. Jika terjadi crossing signifikan ($\ge \text{Rp } 10\text{ Miliar}$ atau $\ge 1\%$ saham beredar), sistem akan menampilkan tanda peringatan `⚠️ Crossing`.

### C. Tabel Top Buyers vs Top Sellers (Kanan-Kiri)
* **🟢 TOP BUYERS (Kolom Kiri)**: Daftar 5 hingga 10 broker dengan net buy terbesar (Kode Broker, Volume Lot, Nilai Rupiah, dan Harga Rata-rata).
* **🔴 TOP SELLERS (Kolom Kanan)**: Daftar 5 hingga 10 broker dengan net sell terbesar.
* *Keunggulan Desain:* Kolom buyer dan seller selalu berdampingan (tidak menumpuk atas-bawah), sehingga trader dapat langsung membandingkan broker lawan tanding secara seketika tanpa harus scroll.

### D. Multi-Horizon Presets (`1D`, `1W`, `2W`, `1M`, `3M`, `6M`)
* Menghitung ulang seluruh metrik bandarmologi dan foreign flow untuk rentang tanggal yang dipilih secara instan tanpa perlu menekan tombol submit tambahan.

### E. Tab Daily Activity & Broker Flow
* **Tombol Broker Interaktif**: Menampilkan daftar broker aktif yang diurutkan dari broker paling akumulatif di sebelah kiri.
* **Klik Tombol Broker**: Memfilter pergerakan harga dan riwayat beli/jual spesifik hanya untuk broker terpilih.
* **Grafik Aliran Kumulatif (Broker Flow Line)**: Memperlihatkan grafik apakah broker tertentu konsisten menambah posisi (grafik menanjak) atau diam-diam membuang barang saat harga naik (divergence).

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

### C. Papan Pencatatan & Notasi Khusus BEI
Candlify V2.3 secara otomatis mengidentifikasi klasifikasi papan dan status risiko setiap emiten langsung dari Bursa Efek Indonesia:

1. **Papan Pencatatan:**
   * **Utama**: Emiten mapan dengan aset besar dan rekam jejak keuangan solid (contoh: BBCA, BMRI).
   * **Pengembangan**: Emiten dalam fase bertumbuh.
   * **Akselerasi**: Emiten skala kecil/menengah (UKM).
   * **Pemantauan Khusus (FCA)**: Saham dalam pengawasan khusus bursa dengan metode perdagangan Full Call Auction.
   * **Ekonomi Baru (New Economy)**: Emiten dengan model bisnis berbasis teknologi inovatif (contoh: GOTO).

2. **Kamus Notasi Khusus & Aksi Korporasi:**
   * **`X`** : Saham tercatat di **Papan Pemantauan Khusus (FCA)**.
   * **`E`** : Laporan keuangan terakhir menunjukkan **Ekuitas Negatif**.
   * **`M`** : Terdapat permohonan **PKPU** (Penundaan Kewajiban Pembayaran Utang).
   * **`D`** : Opini auditor 'Disclaimer' (Tidak Menyatakan Pendapat).
   * **`A`** : Opini auditor 'Adverse' (Tidak Wajar).
   * **`N`** : Emiten dengan Saham Hak Suara Multipel (MVS).
   * **`XD`** : **Ex-Dividend** (perdagangan tanpa hak dividen tunai).
   * **`XR`** : **Ex-Right** (perdagangan tanpa hak HMETD).

---

## 8. 🚀 Catatan Rilis & Log Pembaruan (Changelog)

### Versi 2.5 — Institutional Pre-Breakout V2, Data Integrity & Reliability Upgrade (Oktober 2026)
* 🎯 **Institutional Pre-Breakout V2 Persistence**: Kelima metrik institusional dari scanner (`dominance`, `aar`, `clv_3d`, `up_down_vol_ratio`, `is_pocket_pivot`) kini tersimpan permanen di tabel `candlify_signals` dan ditampilkan langsung pada badge (`⚡Pivot`, `% Dom`, serta tooltip rincian di Screener).
* 💱 **Akurasi Valuasi VWAP Foreign Flow & Turnover**:
  * Perhitungan nilai rupiah transaksi asing (`foreign_val`) kini menggunakan harga rata-rata tertimbang harian (**VWAP = Value / Volume**) alih-alih sekadar harga penutupan (`close`).
  * Perbaikan bug inflasi $100\times$ pada estimasi *turnover* tabel harga historis dengan memprioritaskan `harga_saham.value` resmi BEI.
  * Perbaikan indikator tanda minus (`-`) pada angka *Net Outflow* asing di kartu *Order Flow* dan *Screener*.
* 🛡️ **Stabilitas Pipeline & Keamanan Data Master**:
  * Perbaikan orkestrasi fallback Layer 1 (Official IDX) ke Layer 2 (Yahoo Finance) di `worker/run.py` dan `worker/pipeline.py` agar bebas duplikasi eksekusi.
  * Perlindungan kolom `Tanggal Pencatatan` (IPO Date) pada `worker/daftar_saham.csv` dan penggunaan *atomic upsert* (`ON CONFLICT DO UPDATE`) saat upload Excel emiten agar `tradeable_shares` & `notasi_khusus` tidak terhapus.
* 🧠 **Konteks HMB di Kalkulator Trading Plan**: Saat menyusun rencana beli pada saham yang sedang aktif di chart, kalkulator *Position Sizing* kini menampilkan informasi referensi **HMB (Harga Modal Bandar)** secara langsung.
* 🗄️ **Kalender Database & PWA Offline Docs**: Kotak kalender di tab Database kini menampilkan indikator sinkronisasi `IDX Official`, serta Service Worker (`candlify-v2-2.5.0`) mencache parser Markdown agar buku panduan tetap bisa dibaca saat *offline*.

### Versi 2.4 — Official Market Intelligence & Whale Footprint (Oktober 2026)
* 🌐 **Foreign Flow Multi-Horizon (1D, 5D, 20D)**: Visualisasi akumulasi/distribusi dana asing resmi BEI dengan rincian lot dan nilai rupiah pada bottom sheet Order Flow serta indikator compact (`🌐 +24M`) di chart header.
* 🐳 **Trade Size & Whale Footprint Engine**: Perhitungan otomatis rasio Lot/Trade terhadap rerata baseline 20 hari untuk mendeteksi transaksi agresif Smart Money / Whale (`whale_ratio >= 1.5x`) vs aktivitas ritel receh.
* 🤝 **Deteksi Crossing Pasar Nego**: Filter validasi otomatis transaksi pasar negosiasi skala besar (&ge; Rp 10 Miliar atau &ge; 1% saham beredar) yang sering menjadi sinyal awal crossing kepemilikan institusi.
* ⚡ **Screener Presets Terintegrasi**: Tambahan dua preset strategi bursa baru:
  * **🌐 Foreign Inflow**: Menyaring emiten dengan net buy asing positif terbesar hari ini.
  * **🐳 Whale Footprint**: Menyaring emiten dengan lonjakan trade size (lot per trade) &ge; 1.5x di atas rata-rata historis.
* 🏷️ **Subtle Notasi Khusus BEI**: Tampilan notasi khusus (`[X]`, `[E]`, `[N]`, dll.) disematkan secara elegan dan non-intrusif di samping ticker tanpa modal peringatan pop-up yang mengganggu.
* 📱 **Header Order Flow Badge yang Ramping**: Penghapusan ikon bar chart (`📊`) pada badge atas chart sehingga status flow bandar, flow asing, dan HMB selalu muat satu baris rapi di layar smartphone PWA.
* ⚖️ **Broksum Side-by-Side Symmetrical (Kanan-Kiri)**: Desain 2 kolom permanen untuk seluruh panel Broker Summary (Top Buyers di kiri & Top Sellers di kanan, Foreign Flow di kiri & Whale Trade Size di kanan). Menghilangkan penumpukan atas-bawah pada layar smartphone sehingga perbandingan kekuatan pasar langsung terlihat seketika tanpa perlu scroll.

### Versi 2.3 — All-in-One IDX Engine & Foreign Flow (Oktober 2026)
* 🌐 **All-in-One IDX Trading Engine**: Integrasi langsung API Trading Summary resmi Bursa Efek Indonesia (BEI) via TLS impersonation safari17_0 dengan eksekusi super-cepat (1,3 detik untuk seluruh 963 emiten).
* 💰 **Penyimpanan Data Asing Resmi (Foreign Flow)**: Database kini menyimpan data transaksi asing murni (Foreign Buy, Foreign Sell, Foreign Net), nilai transaksi rupiah (Turnover), dan frekuensi perdagangan.
* 🏛️ **Papan Pencatatan & Notasi Khusus Real-Time**: Deteksi otomatis papan pencatatan (Utama, Pengembangan, Akselerasi, FCA, Ekonomi Baru) dan kode notasi (X, E, M, XD, XR).
* 🚀 **Backfiller Multi-Minggu Cepat**: Script backfiller otomatis mengisi 20 hari bursa (~4 minggu) data resmi BEI dalam hitungan detik untuk kebutuhan analisis rolling 5D & 20D.
* 🗄️ **Kompatibilitas Archiver & Database Monitor**: Auto-archiver dan modul monitor database telah diperbarui penuh mendukung seluruh kolom transaksi baru.

### Versi 2.2 — Rilis Sebelumnya (Oktober 2026)
* ✨ **Pusat Dokumentasi Dinamis**: Seluruh panduan dipecah modular ke dalam file Markdown yang disinkronisasi langsung oleh server secara otomatis.
* 🧹 **Simplifikasi Tab Settings**: Desain ultra-clean dengan segmented switch pills, penghapusan dropdown kategori default yang mubazir, dan ringkasan footer arsitektur minimalis.
* 🛡️ **Eliminasi Watchlist Flicker**: Modal bintang ⭐ kini terbuka bersih tanpa flicker auto-unselect untuk pengalaman pengguna PWA smartphone yang mulus.
* 📊 **Compact Order Flow Badge**: Teks badge chart diperingkas (`📊 🟢 +1.2B • HMB 4.850`) dengan proteksi single-line agar tidak turun ke baris kedua di layar HP.
* 🎛️ **Swipeable Broker Flow Buttons**: Urutan broker diurutkan secara cerdas dengan broker akumulasi teratas di paling kiri.
* ⭐ **Default View "Semua" pada Watchlist**: Tombol "Semua" dipin permanen di sebelah ikon pengaturan kategori, memudahkan navigasi cepat seluruh portofolio pantauan.
* 📅 **Sinkronisasi Kalender Bursa Otomatis**: Integrasi batch downloader kalender bursa konsensus dengan fallback aman terhadap hari libur pasar modal.

---
*Dokumen ini diperbarui secara berkala mengikuti perkembangan dan peningkatan fitur Candlify.*
