# Candlify V2 🕯️ — Lean, Bandarmology-Powered IDX Engine

Candlify V2 adalah platform analisis saham Bursa Efek Indonesia (BEI/IDX) modern, ultra-ramping (*lean*), dan berorientasi pada visualisasi **KLineCharts**, perhitungan **Bandarmologi (HMB & Net Flow)**, screener multi-strategi, watchlist dinamis, dan jurnal trading plan dengan arsitektur *Zero-Cost Infrastructure*.

---

## 🏛️ Arsitektur & Tech Stack

```text
Candlify V2/
├── api/
│   ├── index.py              # Vercel Serverless Function entrypoint
│   └── history.py            # Backward-compatibility endpoint shim
├── docs/
│   ├── 01_PANDUAN_CANDLIFY_PWA.md
│   ├── 02_TEORI_BANDARMOLOGI_MIKROSTRUKTUR.md
│   └── 03_SOP_STRATEGI_PRE_BREAKOUT.md
├── lib/
│   ├── db.py                 # Unified thread-safe SQLAlchemy connection pool
│   ├── utils.py              # Shared timezone, ticker validation & TTL helpers
│   ├── history.py            # Hybrid candlestick engine (Neon DB + Yahoo + Stockbit BYOT)
│   ├── bandarmologi.py       # HMB, Foreign Flow, Whale Trade Size & Broksum engine
│   ├── screener.py           # Multi-preset scanner (Pre-Breakout V2, Foreign Inflow, Whale)
│   ├── portfolio.py          # Watchlist CRUD, risk profile & trading plan journaling
│   └── database_monitor.py   # Glory Engine sync calendar & atomic master emiten upsert
├── public/
│   ├── index.html            # Single Page Application (PWA UI)
│   ├── css/style.css         # Modern dark-theme desktop & mobile responsive styling
│   ├── js/chart.js           # KLineCharts integration, order flow sheet, modal handlers
│   ├── js/marked.min.js      # Offline-capable Markdown documentation renderer
│   └── sw.js                 # Service worker caching strategy (PWA v2.5.0)
├── worker/
│   ├── run.py                # Pipeline (Layer 1 IDX + Layer 2 YF) + Harvester + Scanner
│   ├── sync_idx_daily.py     # Layer 1 All-in-One Official IDX Trading Summary engine
│   ├── pipeline.py           # Layer 2 Daily OHLCV fallback via yfinance & IHSG calendar
│   ├── scanner_bali.py       # Institutional Pre-Breakout Base V2 quantitative scanner
│   ├── harvester.py          # Broker summary scraper & circuit breaker
│   ├── scraper.py            # IndoPremier parser with upsert
│   ├── archiver.py           # Telegram monthly backup & rolling retention cleaner
│   ├── sync_seed.py          # Local SQLite seed builder from production Neon DB
│   ├── db_config.py          # Shared DB setup & auto schema migration
│   └── schema.sql            # DDL database reference (PostgreSQL / Neon)
├── server.py                 # FastAPI application & API endpoints
├── CHANGELOG.md              # Release history & changelog
├── test_*.py                 # Pytest automated test suite
└── vercel.json               # Serverless deployment configuration
```

### ⚡ Komponen Utama
1. **Frontend PWA:** Vanilla JS + KLineCharts v9 + Service Worker (`candlify-v2-2.5.0`) untuk visualisasi kanvas cepat di desktop & smartphone, lengkap dengan pembaca dokumentasi offline.
2. **Backend API:** FastAPI dengan GZip compression, non-blocking sync threadpool, bounded FIFO memory cache, dan CDN caching headers.
3. **Database:** Neon PostgreSQL Cloud (Free Tier) dengan auto-reconnect, pre-ping, connection recycling, dan fallback otomatis ke `worker/local_candlify.db` (SQLite).
4. **Data Worker:** GitHub Actions cron runner (Senin-Jumat 18:17 WIB) yang mengeksekusi Layer 1 Official IDX Engine (fallback ke Layer 2 Yahoo Finance), harvesting broker summary, kalkulasi sinyal *Institutional Pre-Breakout V2*, dan auto-archive ke Telegram.

---

## 🚀 Fitur Unggulan

- **Hybrid Multi-Timeframe Candlestick:**
  - `1D`: 100% konsisten ditarik instan dari Neon PostgreSQL (atau pilihan feed Yahoo Finance).
  - `1m, 5m, 15m, 1h, 4h`: Real-time streaming via Yahoo Finance dengan auto-resample 4 jam (TradingView aligned).
  - `1m Intraday BYOT`: Opsional via Stockbit Exodus API token user.
- **Bandarmologi & Official Market Intelligence Engine:**
  - **HMB (Harga Modal Bandar):** Rata-rata tertimbang *Net-Inventory* akumulator top broker.
  - **Foreign Flow (1D, 5D, 20D):** Pelacakan arus dana asing resmi BEI menggunakan estimasi VWAP harian (`Value / Volume`).
  - **Whale Footprint & Pasar Nego:** Deteksi lonjakan *Lot per Trade* (`whale_ratio >= 1.5x`) dan transaksi crossing pasar negosiasi ($\ge \text{Rp } 10\text{ Miliar}$ atau $\ge 1\%$ *listed shares*).
  - **Broker Summary Side-by-Side:** Perbandingan simetris Top Buyers vs Top Sellers dengan rentang multi-horizon (`1D` hingga `6M`).
- **IDX Stock Screener & Institutional Pre-Breakout V2:**
  - Batch scan 880+ saham IDX (< 1ms in-memory cache).
  - Preset strategi: *🎯 Pre-Breakout Base V2 (Dominance, AAR, CLV 3D, Up/Down Vol Ratio, Pocket Pivot), 🌐 Foreign Inflow, 🐳 Whale Footprint, Swing, Breakout, Vol + BB, Oversold Rebound, Big Cap Leaders*.
- **Risk Management & Trading Plan:**
  - Auto position-sizing (kalkulasi lot otomatis berdasarkan profil risiko modal + referensi HMB langsung di kalkulator).
  - Live tracking unrealized PnL, target price hit, dan trailing stop status.
- **Database & Sync Monitor:**
  - Kalender heatmap sinkronisasi per bulan (rolling 7 bulan) mencakup indikator **Harga, Broksum, dan IDX Official**.
  - Master emiten upload langsung dari file Excel resmi IDX dengan *atomic upsert* yang menjaga keutuhan `tradeable_shares` dan `notasi_khusus`.

---

## 🛠️ Menjalankan Secara Lokal

### 1. Prasyarat
- Python 3.10+
- Database PostgreSQL (misal Neon DB) atau SQLite untuk pengujian lokal.

### 2. Instalasi Dependensi
```bash
pip install -r requirements.txt
```

### 3. Konfigurasi Environment (`.env`)
Salin atau buat file `.env` di root direktori:
```env
DATABASE_URL=postgresql://user:password@ep-sample.neon.tech/candlify?sslmode=require
PORT=8000
# Opsional:
CORS_ORIGINS=*
TELE_BOT_DHIKSDHIKY=your_bot_token
TELE_CHAT_ID_DHIKA=your_chat_id
```

### 4. Menjalankan Server
```bash
python server.py
```
Buka browser di: [http://localhost:8000](http://localhost:8000)

---

## 🧪 Pengujian (Tests)

Jalankan test suite menggunakan `pytest`:
```bash
pytest
```
Semua endpoint, integritas data feed, bandarmologi, watchlist, dan trading plan dicakup dalam test suite.
