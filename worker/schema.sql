-- ==========================================================
-- Candlify V2 Database Schema (PostgreSQL / Neon DB)
-- Single Source of Truth reference matching worker/db_config.py
-- ==========================================================

-- 1. Master Emiten BEI
CREATE TABLE IF NOT EXISTS daftar_saham (
    kode VARCHAR(10) PRIMARY KEY,
    no INTEGER,
    nama_perusahaan VARCHAR(255) NOT NULL,
    tanggal_pencatatan DATE,
    saham BIGINT,
    tradeable_shares BIGINT,
    papan_pencatatan VARCHAR(50),
    notasi_khusus VARCHAR(50),
    tanggal_update DATE
);

-- 2. Daily Price Historical (OHLCV) & Official Flow
CREATE TABLE IF NOT EXISTS harga_saham (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    tanggal DATE NOT NULL,
    open NUMERIC(20,4),
    high NUMERIC(20,4),
    low NUMERIC(20,4),
    close NUMERIC(20,4),
    volume BIGINT,
    value NUMERIC(24,2) DEFAULT 0,
    frequency BIGINT DEFAULT 0,
    foreign_buy BIGINT DEFAULT 0,
    foreign_sell BIGINT DEFAULT 0,
    foreign_net BIGINT DEFAULT 0,
    offer NUMERIC(20,4),
    offer_volume BIGINT,
    bid NUMERIC(20,4),
    bid_volume BIGINT,
    non_regular_volume BIGINT DEFAULT 0,
    non_regular_value NUMERIC(24,2) DEFAULT 0,
    UNIQUE (ticker, tanggal)
);

-- 3. Broker Summary Harian (BrokSum)
CREATE TABLE IF NOT EXISTS broker_summary (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    broker_code VARCHAR(5) NOT NULL,
    buy_vol BIGINT DEFAULT 0,
    buy_val FLOAT DEFAULT 0,
    buy_avg FLOAT DEFAULT 0,
    sell_vol BIGINT DEFAULT 0,
    sell_val FLOAT DEFAULT 0,
    sell_avg FLOAT DEFAULT 0,
    net_vol BIGINT DEFAULT 0,
    net_val FLOAT DEFAULT 0,
    UNIQUE (ticker, date, broker_code)
);

-- 4. Status Arsip Bulanan
CREATE TABLE IF NOT EXISTS archive_status (
    month VARCHAR(7) PRIMARY KEY,
    status VARCHAR(20) NOT NULL,
    completed_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Harvester Gaps (Suspensi & Isolasi Gap)
CREATE TABLE IF NOT EXISTS harvester_gaps (
    ticker VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    reason VARCHAR(50),
    attempts INT DEFAULT 1,
    last_attempt TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (ticker, date)
);

-- 6. Bot Error Logs
CREATE TABLE IF NOT EXISTS bot_error_logs (
    id SERIAL PRIMARY KEY,
    bot_name VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    error_level VARCHAR(20) NOT NULL,
    ticker VARCHAR(10),
    error_message VARCHAR(255) NOT NULL,
    traceback TEXT
);

-- 7. User Settings (Risk Profile & Watchlist Categories)
CREATE TABLE IF NOT EXISTS candlify_user_settings (
    key VARCHAR(50) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. Multi-Category Watchlists
CREATE TABLE IF NOT EXISTS candlify_watchlists (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    category VARCHAR(50) NOT NULL DEFAULT 'Breakout',
    target_entry FLOAT,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (symbol, category)
);

-- 9. Trading Plans & Journaling
CREATE TABLE IF NOT EXISTS candlify_trading_plans (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    category VARCHAR(50) DEFAULT 'Breakout',
    order_type VARCHAR(20) DEFAULT 'LIMIT',
    entry_price FLOAT NOT NULL,
    sl_price FLOAT NOT NULL,
    tp1_price FLOAT NOT NULL,
    tp2_price FLOAT,
    lot_size INT NOT NULL,
    risk_amount FLOAT,
    risk_reward_ratio FLOAT,
    status VARCHAR(20) DEFAULT 'ANTRI',
    exit_price FLOAT,
    realized_pnl FLOAT,
    realized_pnl_pct FLOAT,
    entry_date TIMESTAMPTZ,
    exit_date TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for Fast Query Performance
CREATE INDEX IF NOT EXISTS idx_broker_summary_ticker_date ON broker_summary (ticker, date);
CREATE INDEX IF NOT EXISTS idx_harga_saham_ticker_date ON harga_saham (ticker, tanggal);
CREATE INDEX IF NOT EXISTS idx_watchlists_symbol ON candlify_watchlists (symbol);
CREATE INDEX IF NOT EXISTS idx_trading_plans_status ON candlify_trading_plans (status);

-- 10. Pre-Breakout Signals (Pre-Breakout Base Engine)
CREATE TABLE IF NOT EXISTS candlify_signals (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    price FLOAT NOT NULL,
    range_7 FLOAT NOT NULL,
    volume_dry_ratio FLOAT NOT NULL,
    bbw FLOAT NOT NULL,
    price_to_ma20 FLOAT NOT NULL,
    hmb FLOAT,
    top_accumulator VARCHAR(5),
    score INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (date, ticker)
);

CREATE INDEX IF NOT EXISTS idx_candlify_signals_date ON candlify_signals (date DESC);
CREATE INDEX IF NOT EXISTS idx_candlify_signals_ticker ON candlify_signals (ticker);
