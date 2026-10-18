"""
test_market_intelligence.py — Verification of Official IDX Market Intelligence Features
======================================================================================
Tests:
1. get_stock_market_intelligence: Foreign flow (1D, 5D, 20D), Trade size, Pasar nego, Notasi
2. API endpoint /api/bandarmologi/intelligence?symbol=BBRI
3. API endpoint /api/bandarmologi includes market_intelligence & foreign_flow in summary
4. API endpoint /api/bandarmologi/broksum includes range foreign flow & market_intelligence
5. Screener presets: foreign_inflow & whale_footprint
6. Frontend UI element presence in public/index.html & chart.js syntax
"""

import pytest
from fastapi.testclient import TestClient
from server import app
from lib.bandarmologi import get_stock_market_intelligence, get_bandarmologi, get_broksum_range
from lib.screener import get_screened_stocks, get_idx_market_intelligence_universe

client = TestClient(app)


def test_market_intelligence_bbri():
    """Verifikasi perhitungan market intelligence resmi BEI untuk BBRI."""
    intel = get_stock_market_intelligence("BBRI")
    assert intel is not None
    assert intel.get("success") is True
    assert intel.get("symbol") == "BBRI"
    
    # Foreign Flow verification
    ff = intel.get("foreign_flow", {})
    assert "today_net_shares" in ff
    assert "today_net_val" in ff
    assert "flow_5d_val" in ff
    assert "flow_20d_val" in ff
    assert ff.get("status_1d") in ("ACCUM", "DISTRIB", "NEUTRAL")
    assert ff.get("status_5d") in ("ACCUM", "DISTRIB", "NEUTRAL")
    assert ff.get("status_20d") in ("ACCUM", "DISTRIB", "NEUTRAL")

    # Trade Size (Whale vs Ritel) verification
    ts = intel.get("trade_size", {})
    assert "today_lot_per_trade" in ts
    assert "avg_lot_per_trade_20d" in ts
    assert "whale_ratio" in ts
    assert "whale_label" in ts
    assert ts.get("whale_ratio") > 0

    # Pasar Nego verification
    pn = intel.get("pasar_nego", {})
    assert "volume_lots" in pn
    assert "value" in pn
    assert "has_crossing" in pn
    assert isinstance(pn.get("has_crossing"), bool)

    # Emiten Info verification
    info = intel.get("emiten_info", {})
    assert "notasi_khusus" in info
    assert "tradeable_shares" in info


def test_api_market_intelligence_endpoint():
    """Verifikasi endpoint GET /api/bandarmologi/intelligence."""
    resp = client.get("/api/bandarmologi/intelligence?symbol=BBRI")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["symbol"] == "BBRI"
    assert "foreign_flow" in data
    assert "trade_size" in data
    assert "pasar_nego" in data
    assert "emiten_info" in data


def test_api_bandarmologi_enrichment():
    """Verifikasi bahwa get_bandarmologi dan API-nya menyertakan market intelligence."""
    resp = client.get("/api/bandarmologi?symbol=BBRI&days=30")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "summary" in data
    summary = data["summary"]
    assert "foreign_flow" in summary
    assert "trade_size" in summary
    assert "pasar_nego" in summary
    assert "notasi_khusus" in summary
    assert "market_intelligence" in data


def test_api_broksum_range_enrichment():
    """Verifikasi bahwa broksum range menyertakan market intelligence dan foreign flow."""
    resp = client.get("/api/bandarmologi/broksum?symbol=BBRI&from_date=2026-10-12&to_date=2026-10-16")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "summary" in data
    summary = data["summary"]
    assert "foreign_flow" in summary
    assert "trade_size" in summary
    assert "pasar_nego" in summary
    assert "notasi_khusus" in summary
    assert "market_intelligence" in data


def test_screener_preset_foreign_inflow():
    """Verifikasi screener preset foreign_inflow menghasilkan saham dengan akumulasi asing."""
    res = get_screened_stocks(preset="foreign_inflow")
    assert res["success"] is True
    assert res["preset"] == "foreign_inflow"
    assert res["count"] > 0
    stocks = res["stocks"]
    assert len(stocks) > 0
    # Top emiten harus memiliki net foreign value positif
    top_stock = stocks[0]
    assert top_stock.get("foreign_val", 0) > 0
    assert "foreign_net_lots" in top_stock


def test_screener_preset_whale_footprint():
    """Verifikasi screener preset whale_footprint mendeteksi lonjakan trade size."""
    res = get_screened_stocks(preset="whale_footprint")
    assert res["success"] is True
    assert res["preset"] == "whale_footprint"
    assert res["count"] > 0
    stocks = res["stocks"]
    assert len(stocks) > 0
    # Top emiten harus memiliki whale_ratio >= 1.5
    top_stock = stocks[0]
    assert top_stock.get("whale_ratio", 0) >= 1.5
    assert "lot_per_trade" in top_stock


def test_ui_market_intelligence_elements():
    """Verifikasi elemen UI foreign flow, whale status, dan notasi khusus di index.html."""
    with open("public/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # Sheet Header & Notasi Pill
    assert 'id="broksum-notasi-pill"' in html
    # Market Intelligence Container
    assert 'class="intel-cards-container"' in html
    assert 'id="intel-foreign-status"' in html
    assert 'id="intel-foreign-1d"' in html
    assert 'id="intel-foreign-5d"' in html
    assert 'id="intel-foreign-20d"' in html
    assert 'id="intel-whale-status"' in html
    assert 'id="intel-whale-today"' in html
    assert 'id="intel-whale-avg"' in html
    assert 'id="intel-nego-val"' in html
    # Screener Presets
    assert 'data-preset="foreign_inflow"' in html
    assert 'data-preset="whale_footprint"' in html
    # Screener Sort Options
    assert 'value="foreign_desc"' in html
    assert 'value="whale_desc"' in html


def test_screener_js_syntax_and_notasi():
    """Verifikasi fmtVal terdefinisi di filterAndRenderScreener dan tidak ada badge-fca redundan."""
    with open("public/js/chart.js", "r", encoding="utf-8") as f:
        js = f.read()

    # Pastikan fmtVal terdefinisi di dalam filterAndRenderScreener
    assert "const fmtVal = (val) => {" in js
    # Pastikan notasi khusus resmi BEI [X], [E], dll. digunakan
    assert "notasi-pill" in js
    # Pastikan tidak ada rendering badge-fca redundan di screener list
    assert "badge-fca" not in js
