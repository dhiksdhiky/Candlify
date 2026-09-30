# Candlify V2 🕯️ — Lean, Bandarmology-Powered IDX Engine

Candlify V2 adalah platform analisis saham Bursa Efek Indonesia (BEI/IDX) modern, ultra-ramping (*lean*), dan berorientasi pada visualisasi **KLineCharts**, perhitungan **Bandarmologi (HMB & Net Flow)**, screener multi-strategi, watchlist dinamis, dan jurnal trading plan dengan arsitektur *Zero-Cost Infrastructure*.

---

## 🏛️ Arsitektur & Tech Stack

```text
Candlify V2/
├── api/
│   ├── index.py              # Vercel Serverless Function entrypoint
│   └── history.py            # Backward-compatibility endpoint shim
├── lib/
│   ├── db.py                 # Unified thread-safe SQLAlchemy connection pool
│   ├── utils.py              # Shared timezone, ticker validation & TTL helpers
│   ├── history.py            # Hybrid candlestick engine (Neon DB + Yahoo + Stockbit BYOT)
│   ├── bandarmologi.py       # HMB & Broker Summary calculation engine
│   ├── screener.py           # TradingView batch scanner (880+ emiten BEI)
│   ├── portfolio.py          # Watchlist CRUD, risk profile & trading plan journaling
│   └── database_monitor.py   # Glory Engine sync calendar & master emiten upload
├── public/
│   ├── index.html            # Single Page Application (PWA UI)
│   ├── css/style.css         # Modern dark-theme desktop & mobile responsive styling
│   ├── js/chart.js           # KLineCharts integration, drawing tools, modal handlers
│   └── sw.js                 # Service worker caching strategy (PWA)
├── worker/
│   ├── run.py                # Pipeline + Harvester orchestrator
│   ├── pipeline.py           # Daily OHLCV data ingestion via yfinance & IHSG calendar
│   ├── harvester.py          # Broker summary scraper & circuit breaker
│   ├── scraper.py            # IndoPremier parser with upsert
│   ├── archiver.py           # Telegram monthly backup & rolling retention cleaner
│   ├── db_config.py          # Shared DB setup & table creation
│   └── schema.sql            # DDL database reference (PostgreSQL / Neon)
├── server.py                 # FastAPI application & API endpoints
├── test_*.py                 # Pytest test suite
└── vercel.json               # Serverless deployment configuration
```

### ⚡ Komponen Utama
1. **Frontend PWA:** Vanilla JS + KLineCharts v9 + Service Worker untuk visualisasi kanvas super cepat di desktop & mobile.
2. **Backend API:** FastAPI dengan GZip compression, non-blocking sync threadpool, dan CDN caching headers.
3. **Database:** Neon PostgreSQL Cloud (Free Tier) dengan auto-reconnect, pre-ping, dan connection recycling.
4. **Data Worker:** GitHub Actions cron runner (Senin-Jumat 18:17 WIB) yang mengeksekusi pipeline harga harian, harvesting broker summary, dan auto-archive ke Telegram.

---

## 🚀 Fitur Unggulan

- **Hybrid Multi-Timeframe Candlestick:**
  - `1D`: 100% konsisten ditarik instan dari Neon PostgreSQL.
  - `1m, 5m, 15m, 1h, 4h`: Real-time streaming via Yahoo Finance dengan auto-resample 4 jam (TradingView aligned).
  - `1m Intraday BYOT`: Opsional via Stockbit Exodus API token user.
- **Bandarmologi Engine:**
  - **HMB (Harga Modal Bandar):** Rata-rata tertimbang harga beli akumulator top 5 (rolling 20 hari).
  - **Net Flow:** Top 3 Net Buy vs Top 3 Net Sell per hari.
  - **Broker Summary Range:** Filter agregasi custom (1D, 1W, 1M, hingga 6M).
- **IDX Stock Screener:**
  - Batch scan 880+ saham IDX via TradingView Scanner (< 1ms cache in-memory).
  - Preset strategi: *Swing, Breakout, Vol + BB, Oversold Rebound, Big Cap Leaders*.
- **Risk Management & Trading Plan:**
  - Auto position-sizing (kalkulasi lot otomatis berdasarkan profil risiko modal).
  - Live tracking unrealized PnL, target price hit, dan trailing stop status.
- **Database & Sync Monitor:**
  - Kalender heatmap sinkronisasi per bulan (rolling 7 bulan).
  - Master emiten upload langsung dari file Excel resmi IDX.

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
