"""
test_daily_insight_and_report.py — Unit Tests for Daily Market Insight,
Multi-Broker Radar (1D/5D/20D), and Hybrid Pre-Breakout Performance Report.
"""

import os
import sys
import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine, text
from fastapi.testclient import TestClient

try:
    import pyarrow.compute  # noqa: F401
except Exception:
    sys.modules["pyarrow"] = None

import lib.daily_insight as daily_insight
import lib.pre_breakout_report as pb_report
from server import app


@pytest.fixture
def sqlite_market_engine(tmp_path, monkeypatch):
    db_file = tmp_path / "test_insight.db"
    engine = create_engine(f"sqlite:///{db_file}")

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE harga_saham (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                tanggal DATE NOT NULL,
                open REAL, high REAL, low REAL, close REAL,
                volume INTEGER, value REAL DEFAULT 0, frequency INTEGER DEFAULT 0,
                foreign_buy INTEGER DEFAULT 0, foreign_sell INTEGER DEFAULT 0, foreign_net INTEGER DEFAULT 0
            )
        """))
        conn.execute(text("""
            CREATE TABLE broker_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                date DATE NOT NULL,
                broker_code TEXT NOT NULL,
                buy_vol INTEGER DEFAULT 0, buy_val REAL DEFAULT 0, buy_avg REAL DEFAULT 0,
                sell_vol INTEGER DEFAULT 0, sell_val REAL DEFAULT 0, sell_avg REAL DEFAULT 0,
                net_vol INTEGER DEFAULT 0, net_val REAL DEFAULT 0
            )
        """))
        conn.execute(text("""
            CREATE TABLE candlify_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                ticker TEXT NOT NULL,
                price REAL NOT NULL,
                range_7 REAL NOT NULL,
                volume_dry_ratio REAL NOT NULL,
                bbw REAL NOT NULL,
                price_to_ma20 REAL NOT NULL,
                hmb REAL, top_accumulator TEXT,
                dominance REAL DEFAULT 0, aar REAL DEFAULT 1.0,
                clv_3d REAL DEFAULT 0, up_down_vol_ratio REAL DEFAULT 1.0,
                is_pocket_pivot INTEGER DEFAULT 0, score INTEGER DEFAULT 70
            )
        """))

        # Seed 6 hari bursa (2026-10-12 s/d 2026-10-17) untuk 4 emiten
        dates = [date(2026, 10, 12) + timedelta(days=i) for i in range(6)]
        for i, d in enumerate(dates):
            d_str = d.strftime("%Y-%m-%d")
            # BBCA: Naik terus + Foreign Net Buy kuat
            bbca_c = 10000 + i * 200
            conn.execute(text("""
                INSERT INTO harga_saham (ticker, tanggal, open, high, low, close, volume, value, frequency, foreign_buy, foreign_sell, foreign_net)
                VALUES ('BBCA', :d, :o, :h, :l, :c, 10000000, :v, 5000, 6000000, 2000000, 4000000)
            """), {"d": d_str, "o": bbca_c - 50, "h": bbca_c + 100, "l": bbca_c - 100, "c": bbca_c, "v": 10000000 * bbca_c})

            # BBRI: Turun + Foreign Net Sell
            bbri_c = 5000 - i * 100
            conn.execute(text("""
                INSERT INTO harga_saham (ticker, tanggal, open, high, low, close, volume, value, frequency, foreign_buy, foreign_sell, foreign_net)
                VALUES ('BBRI', :d, :o, :h, :l, :c, 8000000, :v, 4000, 1000000, 4000000, -3000000)
            """), {"d": d_str, "o": bbri_c + 50, "h": bbri_c + 80, "l": bbri_c - 80, "c": bbri_c, "v": 8000000 * bbri_c})

            # SUPER: Signal 12 Okt di 1000 -> T+2 High 1200 (+20% HIT SUPER)
            super_h = 1200 if i == 2 else 1010
            super_c = 1150 if i >= 2 else 1000
            conn.execute(text("""
                INSERT INTO harga_saham (ticker, tanggal, open, high, low, close, volume, value, frequency, foreign_buy, foreign_sell, foreign_net)
                VALUES ('SUPR', :d, 1000, :h, 990, :c, 500000, :v, 300, 0, 0, 0)
            """), {"d": d_str, "h": super_h, "c": super_c, "v": 500000 * super_c})

            # FAIL: Signal 12 Okt di 1000 -> T+1 Low 920 (-8% STOP OUT)
            fail_l = 920 if i >= 1 else 995
            fail_c = 930 if i >= 1 else 1000
            conn.execute(text("""
                INSERT INTO harga_saham (ticker, tanggal, open, high, low, close, volume, value, frequency, foreign_buy, foreign_sell, foreign_net)
                VALUES ('FAIL', :d, 1000, 1010, :l, :c, 400000, :v, 200, 0, 0, 0)
            """), {"d": d_str, "l": fail_l, "c": fail_c, "v": 400000 * fail_c})

            # RUNN: Signal 16 Okt di 500 -> T+1 tetap 505 (RUNNING)
            run_c = 505 if i == 5 else 500
            conn.execute(text("""
                INSERT INTO harga_saham (ticker, tanggal, open, high, low, close, volume, value, frequency, foreign_buy, foreign_sell, foreign_net)
                VALUES ('RUNN', :d, 500, 510, 495, :c, 300000, :v, 150, 0, 0, 0)
            """), {"d": d_str, "c": run_c, "v": 300000 * run_c})

            # Broker summary untuk AK, BK, dan YP
            conn.execute(text("""
                INSERT INTO broker_summary (ticker, date, broker_code, buy_vol, buy_val, sell_vol, sell_val, net_vol, net_val)
                VALUES
                    ('BBCA', :d, 'AK', 10000, 10500000000, 2000, 2100000000, 8000, 8400000000),
                    ('BBCA', :d, 'BK', 5000,  5250000000,  1000, 1050000000, 4000, 4200000000),
                    ('BBRI', :d, 'AK', 1000,  480000000,   6000, 2880000000, -5000, -2400000000),
                    ('BBRI', :d, 'BK', 500,   240000000,   3500, 1680000000, -3000, -1440000000),
                    ('BBRI', :d, 'YP', 8000,  3840000000,  1000, 480000000,  7000,  3360000000)
            """), {"d": d_str})

        # Seed candlify_signals
        conn.execute(text("""
            INSERT INTO candlify_signals (date, ticker, price, range_7, volume_dry_ratio, bbw, price_to_ma20, score)
            VALUES
                ('2026-10-12', 'SUPR', 1000, 4.0, 0.25, 8.0, 1.5, 88),
                ('2026-10-12', 'FAIL', 1000, 5.0, 0.30, 9.0, 0.5, 72),
                ('2026-10-16', 'RUNN', 500,  3.5, 0.20, 7.0, 1.0, 81)
        """))

    monkeypatch.setattr(daily_insight, "get_engine", lambda: engine)
    monkeypatch.setattr(pb_report, "get_engine", lambda: engine)
    daily_insight.clear_daily_insight_cache()
    pb_report.clear_report_cache()
    return engine


def test_daily_foreign_insight_summary_breadth_and_trend(sqlite_market_engine):
    res = daily_insight.get_daily_foreign_insight(target_date="2026-10-17")
    assert res["success"] is True
    assert res["date"] == "2026-10-17"

    fs = res["foreign_summary"]
    assert fs["net_val"] > 0
    assert fs["status"] == "INFLOW"
    assert fs["buy_pct"] > 50.0

    # Market breadth & MA20 barometer
    br = res["breadth"]
    assert br["advancers"] >= 2  # BBCA & RUNN naik
    assert br["decliners"] >= 1  # BBRI turun
    assert br["total_ma20"] >= 3
    assert 0.0 <= br["above_ma20_pct"] <= 100.0

    # Mini bar trend 20D (6 hari tersedia)
    assert len(res["trend_20d"]) == 6
    assert res["trend_20d"][-1]["date"] == "2026-10-17"

    # Top Buy & Sell
    assert res["top_buy"][0]["ticker"] == "BBCA"
    assert res["top_sell"][0]["ticker"] == "BBRI"


def test_multi_broker_radar_single_and_combined_and_multiday(sqlite_market_engine):
    # 1D Single Broker (AK)
    res_ak_1d = daily_insight.get_multi_broker_insight(target_date="2026-10-17", brokers=["AK"], days=1)
    assert res_ak_1d["success"] is True
    assert res_ak_1d["brokers"] == ["AK"]
    assert res_ak_1d["trading_days"] == 1
    assert res_ak_1d["top_buy"][0]["ticker"] == "BBCA"
    assert res_ak_1d["top_buy"][0]["net_val"] == pytest.approx(8.4e9)
    assert res_ak_1d["top_sell"][0]["ticker"] == "BBRI"
    assert res_ak_1d["top_sell"][0]["net_val"] == pytest.approx(-2.4e9)

    # 1D Combined Brokers (AK + BK) -> harus menjumlahkan 8.4B + 4.2B = 12.6B
    res_combo_1d = daily_insight.get_multi_broker_insight(target_date="2026-10-17", brokers=["AK", "BK"], days=1)
    assert res_combo_1d["success"] is True
    assert res_combo_1d["brokers"] == ["AK", "BK"]
    assert res_combo_1d["top_buy"][0]["net_val"] == pytest.approx(12.6e9)
    assert res_combo_1d["top_sell"][0]["net_val"] == pytest.approx(-3.84e9)

    # 5D Combined Brokers (AK + BK) -> 5 hari x 12.6B = 63B
    res_combo_5d = daily_insight.get_multi_broker_insight(target_date="2026-10-17", brokers=["AK", "BK"], days=5)
    assert res_combo_5d["success"] is True
    assert res_combo_5d["trading_days"] == 5
    assert res_combo_5d["top_buy"][0]["net_val"] == pytest.approx(63.0e9)


def test_hybrid_pre_breakout_report_evaluation_and_notes(sqlite_market_engine):
    sample_md = """# Test Report
<!-- FORENSIC_NOTES_START
2026-10-12|SUPR: Breakout super bersih dengan akumulasi institusi.
FORENSIC_NOTES_END -->

<!-- LIVE_PRE_BREAKOUT_SCORECARD -->
"""
    rendered = pb_report.render_hybrid_pre_breakout_doc(sample_md)

    assert "<!-- LIVE_PRE_BREAKOUT_SCORECARD -->" not in rendered
    assert "🎯 HIT (SUPER)" in rendered
    assert "🛑 STOP OUT" in rendered
    assert "⏳ RUNNING" in rendered
    # Catatan manual untuk SUPR harus ter-merge
    assert "Breakout super bersih dengan akumulasi institusi." in rendered
    # Sinyal RUNNING tanpa catatan harus menampilkan kolom evaluasi kosong (—)
    assert "| 2026-10-16 | **RUNN** |" in rendered
    assert "| — |" in rendered


def test_fastapi_endpoints_daily_insight_broker_radar_and_docs(sqlite_market_engine):
    client = TestClient(app)

    r1 = client.get("/api/database/daily-insight?date=2026-10-17")
    assert r1.status_code == 200
    assert r1.json()["top_buy"][0]["ticker"] == "BBCA"

    r2 = client.get("/api/database/broker-radar?date=2026-10-17&brokers=AK,BK&days=5")
    assert r2.status_code == 200
    assert r2.json()["trading_days"] == 5
    assert r2.json()["top_buy"][0]["ticker"] == "BBCA"

    r3 = client.get("/api/docs")
    assert r3.status_code == 200
    slugs = [d["slug"] for d in r3.json()["docs"]]
    assert "04_laporan_kinerja_pre_breakout" in slugs

    r4 = client.get("/api/docs/04_laporan_kinerja_pre_breakout")
    assert r4.status_code == 200
    md = r4.json()["markdown"]
    assert "<!-- LIVE_PRE_BREAKOUT_SCORECARD -->" not in md
    assert "Live Scorecard Neon DB" in md
    assert "Perbandingan Menyeluruh Formula V1 vs V2" in md
