# 📜 CHANGELOG — Candlify V2

Semua perubahan penting, perbaikan bug, dan peningkatan fitur pada proyek **Candlify V2** didokumentasikan di dalam berkas ini.

---

## [2.5.0] — 2026-10-19
### 🛠️ Bug Fixes (P0, P1, P2)
- **Cloudflare WAF Resilience & Auto Gap-Detector (`worker/sync_idx_daily.py`, `worker/downloader_idx.py`, `.github/workflows/harvester-cron.yml`)**:
  - Memperbaiki kegagalan `HTTP 403` (`cf-mitigated: challenge`) saat mengakses `www.idx.co.id` dengan memensiunkan profil TLS lawas yang diblokir (`safari17_0`, `safari15_5`, `edge101`) dan menggantinya dengan profil modern murni (`chrome131`, `chrome124`, `safari180`, `safari184`, `firefox133`, `chrome120`) tanpa override header `Sec-Fetch-*` manual yang merusak *HTTP/2 pseudo-header fingerprint*.
  - Menambahkan **WARP Pre-Flight Verification & Auto IP Rotation (`_rotate_warp_ip`)** untuk me-reset registrasi & mendapatkan IP keluar Cloudflare WARP baru secara otomatis jika IP sebelumnya terkena challenge 403.
  - Menambahkan **Layer 1B Real Browser Fallback (`fetch_idx_via_browser` via `DrissionPage` + `xvfb`)** untuk mengeksekusi JavaScript Challenge Cloudflare di dalam DOM Chromium asli sebelum beralih ke fallback Layer 2 (Yahoo Finance).
  - Menambahkan fitur **Auto Gap-Detector (`detect_and_fill_idx_gaps`)** pada sinkronisasi harian BEI yang secara otomatis mendeteksi dan menambal tanggal bursa yang terlewat atau yang sebelumnya hanya terisi oleh fallback Yahoo Finance (`frequency = 0`) hingga 14 hari kalender ke belakang tanpa menimpa master emiten terbaru.
- **Worker Pipeline Orchestrator (`worker/run.py`, `worker/pipeline.py`, `worker/sync_idx_daily.py`, `worker/harvester.py`)**:
  - Memperbaiki `NameError: name 'pipeline_success' is not defined` pada `worker/run.py` saat pembuatan laporan status akhir Telegram.
  - Memperbaiki eksekusi ganda (*double execution*) Layer 2 Fallback dengan menonaktifkan internal fallback di dalam `run_sync_daily(use_fallback=False)` ketika dipanggil dari `worker/run.py`.
  - Memperbaiki `NameError: name 'benchmark_tickers' is not defined` dan `NameError: name 'master_cal' is not defined` pada fungsi `get_master_calendar()` dan `run_pipeline()` di `worker/pipeline.py`.
  - Menambahkan **Early-Exit Circuit Breaker (`aborted_by_outage`)** pada `worker/harvester.py` saat server IndoPremier (IPOT) mengalami *down* (`HTTP 502 Bad Gateway` / `NOSERVICE`), sehingga worker berhenti otomatis setelah 8 kegagalan beruntun tanpa membuang waktu ~3,5 jam untuk 500 saham dan tanpa mengotori `harvester_gaps`.
  - Menjalankan *initial pass* `scanner_bali.py` tepat setelah sinkronisasi harga EOD selesai di `worker/run.py`, sehingga sinyal Pre-Breakout V2 selalu ter-update meskipun server Broker Summary sedang *maintenance*.
- **Integritas Data Master Emiten (`worker/sync_idx_daily.py`, `worker/sync_seed.py`, `lib/database_monitor.py`)**:
  - Memperbaiki `update_local_csv()` di `worker/sync_idx_daily.py` agar membaca dan mempertahankan kolom `Tanggal Pencatatan` (IPO date) yang sudah ada di `worker/daftar_saham.csv`.
  - Mengubah `process_saham_excel()` di `lib/database_monitor.py` dari operasi destruktif `DELETE FROM daftar_saham` menjadi *atomic upsert* (`INSERT ... ON CONFLICT (kode) DO UPDATE`) sehingga data `tradeable_shares` dan `notasi_khusus` tidak hilang saat upload Excel.
  - Memperbaiki `worker/sync_seed.py` agar menyalin seluruh skema kolom `daftar_saham` (`nama_perusahaan`, `papan_pencatatan`, `tradeable_shares`, `notasi_khusus`) ke database SQLite lokal.
- **Akurasi Perhitungan Bandarmologi & Tampilan UI (`lib/bandarmologi.py`, `lib/screener.py`, `public/js/chart.js`)**:
  - Memperbaiki bug pengali $100\times$ pada estimasi *turnover* di `get_historical_price_table()` dengan memprioritaskan `harga_saham.value` resmi BEI, diikuti `broker_summary`, lalu fallback `close * volume`.
  - Memperbaiki hilangnya tanda minus (`-`) pada nilai *Foreign Outflow* negatif di panel *Order Flow* (`renderBroksumData`) dan daftar *Screener* (`filterAndRenderScreener`).
  - Mengganti kalkulasi nilai rupiah transaksi asing (`foreign_val`) dari `net_shares * close` menjadi berbasis **VWAP harian** (`value / volume`, dengan fallback ke `close`).

### 🚀 Enhancements & Optimizations
- **Institutional Pre-Breakout V2 Persistence (`worker/schema.sql`, `worker/db_config.py`, `worker/scanner_bali.py`, `lib/screener.py`, `public/js/chart.js`)**:
  - Menambahkan kolom `dominance`, `aar`, `clv_3d`, `up_down_vol_ratio`, dan `is_pocket_pivot` ke tabel `candlify_signals` lengkap dengan migrasi otomatis.
  - Menampilkan indikator `⚡Pivot`, `% Dom`, dan tooltip detail metrik institusional pada kartu saham di tab Screener.
- **Manajemen Memori & Query (`lib/bandarmologi.py`)**:
  - Mengganti penghapusan total `.clear()` pada cache in-memory dengan algoritma *FIFO Eviction* (20% entri tertua) untuk mencegah *cache stampede*.
  - Membatasi query `get_raw_broker_df()` ke jendela 240 hari kalender terakhir guna menjaga kecepatan respons dan efisiensi RAM.
- **UI & PWA Polish (`public/js/chart.js`, `public/css/style.css`, `public/sw.js`, `lib/portfolio.py`, `lib/database_monitor.py`)**:
  - **Watchlist Numeric Age Heatmap Badge**: Mengubah indikator usia pantauan dari teks panjang menjadi angka hari murni ber-border estetik dengan 3 tingkat warna (`age-fresh` hijau 0–5 hari, `age-warm` kuning 6–13 hari, `age-stale` merah $\ge 14$ hari).
  - **Singkatan Kode Papan & Auto-Hide Kategori**: Menyingkat badge papan pencatatan menjadi `UTM`, `PGM`, `AKS`, `EKB` pada Screener & Watchlist, serta menyembunyikan badge kategori saat berada di filter kategori spesifik agar tombol aksi kanan (`🎯 ✏️ 🗑️`) tidak pernah offside.
  - **Target Entry Inline Indicator**: Menampilkan target beli (`🎯`) di baris sub-judul kartu Watchlist dengan highlight hijau saat harga pasar mendekati target ($\pm 2.5\%$).
  - **Indikator Titik Centang Hijau (`✓`) Kalender Database**: Menambahkan `idx_official_synced` ke `get_calendar_history()` dan menampilkannya sebagai bulatan centang hijau `✓` (`cal-idx-dot`) di samping tanggal kalender.
  - **Konteks HMB di Kalkulator Trading Plan**: Menampilkan referensi **HMB (Harga Modal Bandar)** secara kontekstual di dalam kalkulator *Position Sizing*.
  - **PWA Offline Docs**: Memperbarui Service Worker ke `candlify-v2-2.5.0` dan menyertakan `./js/marked.min.js` untuk dukungan pembacaan panduan secara offline.

---

## [2.4.0] — 2026-10-18
- **Foreign Flow Multi-Horizon (1D, 5D, 20D)** pada bottom sheet Order Flow dan badge header chart.
- **Trade Size & Whale Footprint Engine** (`whale_ratio >= 1.5x`) dan deteksi crossing **Pasar Nego**.
- **Screener Presets Baru**: `🌐 Foreign Inflow` dan `🐳 Whale Footprint`.
- **Subtle Notasi Khusus BEI** (`[X]`, `[E]`, dll.) dan layout **Side-by-Side Symmetrical** pada tabel Broker Summary.

---

## [2.3.0] — 2026-10-17
- **All-in-One IDX Trading Engine** (`worker/sync_idx_daily.py`) untuk menarik data OHLCV, Foreign Flow, Frekuensi, Pasar Nego, Papan Pencatatan, dan Notasi Khusus langsung dari endpoint resmi BEI.
- **Backfiller Multi-Minggu Cepat** (`worker/backfill_idx_2w.py`).

---

## [2.2.0] — 2026-10-15
- **Pusat Dokumentasi Dinamis** terintegrasi di tab Settings (`docs/01` s/d `03`).
- **Simplifikasi Tab Settings**, perbaikan modal Watchlist tanpa flicker, dan **Compact Order Flow Badge**.
