# Candlify v2 🕯️ — Lean, Bandarmology-Powered IDX Engine

Modul Candlify versi 2 yang dirancang ulang dari nol (*clean slate*) agar jauh lebih ramping (*lean*), fokus pada kebutuhan esensial trader IDX, dan 100% beroperasi di infrastruktur *Zero-Cost*.

---

## 🏗️ Struktur Folder `v2/`

```text
v2/
├── api/
│   └── history.py       # Core Hybrid Candlestick Engine (Neon DB + YFinance + Stockbit BYOT)
├── test_feed.py         # Skrip pengujian penarikan data multi-timeframe & cache
├── requirements.txt     # Dependensi Python minimal
└── README.md            # Dokumentasi arsitektur v2
```

---

## ⚡ 1. Hybrid Candlestick Data Engine (`v2/api/history.py`)

Engine ini bertugas mendistribusikan data candlestick langsung ke library visualisasi kanvas **KLineCharts v9**:

1. **Jalur Database Neon (Timeframe 1D):**
   * Membaca langsung dari tabel lokal `harga_saham` di Neon PostgreSQL.
   * Super instan (0ms delay jaringan luar), 100% konsisten dengan data garis HMB (Harga Modal Bandar) dan broker summary.
2. **Jalur Yahoo Finance (Timeframe 1m, 5m, 15m, 1h, 1D fallback):**
   * Mengambil data via endpoint resmi Yahoo Finance chart API v8 tanpa butuh API key (`query1.finance.yahoo.com/v8/finance/chart/{ticker}.JK`).
   * Dilengkapi **In-Memory Cache (TTL 60 detik)** untuk mencegah *rate-limiting* dan membuat fetch kedua bernilai **0ms**.
3. **Jalur Stockbit BYOT (Timeframe 1m Intraday + Broker Flow - Opsional):**
   * Jika user menyertakan token sesi pribadi Stockbit (`stockbit_token`), engine otomatis menarik data 1m *pure real-time* dari gateway Exodus Stockbit.

---

## 🧪 Cara Menjalankan Tes

```bash
# Jalankan tes untuk ticker default (BBRI)
python v2/test_feed.py

# Atau uji saham lain (misal: TLKM, ASII, BBCA)
python v2/test_feed.py TLKM
```
