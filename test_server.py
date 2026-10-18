"""
v2/test_server.py — Integration Tests for FastAPI Server Endpoints
==================================================================
Tests:
- /api/health
- /api/history
- /api/bandarmologi (Neon DB integration, schema validation, error handling)
- Frontend static assets delivery (index.html, chart.js, style.css)
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

# Pastikan path import bisa membaca module v2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import app

client = TestClient(app)

def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    json_data = res.json()
    assert json_data.get("status") == "ok"
    assert json_data.get("version") == "v2-lean"

def test_api_bandarmologi_bbri():
    res = client.get("/api/bandarmologi?symbol=BBRI")
    assert res.status_code == 200
    data = res.json()
    assert data.get("success") is True
    assert data.get("symbol") == "BBRI"
    assert data.get("count") > 0
    assert "summary" in data
    summary = data["summary"]
    assert summary["latest_hmb"] > 0
    assert summary["latest_status"] in ["ACCUM", "DISTRIB", "NEUTRAL"]
    assert isinstance(summary["top_buyers"], list)
    assert isinstance(summary["top_sellers"], list)
    assert len(summary["top_buyers"]) > 0
    assert len(summary["top_sellers"]) > 0
    assert summary["top_buyers"][0].get("avg_price", 0) > 0
    assert summary["top_sellers"][0].get("avg_price", 0) > 0
    assert summary.get("total_buy_val", 0) > 0
    assert summary.get("total_sell_val", 0) > 0
    
    # Check item structure
    latest_item = data["data"][-1]
    assert "date" in latest_item
    assert "timestamp" in latest_item
    assert "hmb" in latest_item
    assert "net_flow" in latest_item

def test_api_bandarmologi_nckl():
    res = client.get("/api/bandarmologi?symbol=NCKL")
    assert res.status_code == 200
    data = res.json()
    assert data.get("success") is True
    assert data.get("symbol") == "NCKL"

def test_api_bandarmologi_invalid_symbol():
    res = client.get("/api/bandarmologi?symbol=INVALID$$$")
    assert res.status_code == 400
    detail = res.json().get("detail", "")
    assert "tidak valid" in detail

def test_api_history_bbri():
    res = client.get("/api/history?symbol=BBRI&interval=4h")
    assert res.status_code == 200
    data = res.json()
    assert data.get("success") is True
    assert len(data.get("data", [])) > 0

def test_frontend_static_serving():
    res = client.get("/")
    assert res.status_code == 200
    html = res.text
    assert "bandar-badge-label" in html
    assert "toggle-hmb" in html
    assert "toggle-netflow" in html
    assert "Harga Modal Bandar (HMB)" in html
    assert "broksum-sheet" in html
    assert "broksum-filter-bar" in html
    assert "broksum-date-from" in html
    assert "broksum-date-to" in html
    assert "broksum-buyers-list" in html
    assert "broksum-sellers-list" in html
    assert "screener-view" in html
    assert "screener-search-input" in html
    assert "screener-presets-container" in html
    assert "screener-sort-select" in html
    assert "screener-list" in html
    assert "screener-pagination" in html
    assert "btn-toggle-filters" in html
    assert "btn-back-screener" in html
    assert "chart-header-badges" in html
    assert "source-status-pill" in html
    assert "screener-unified-bar" in html
    assert "filter-modal" in html
    assert "filter-modal-backdrop" in html
    assert "screener-active-filter-badge" in html

    res_js = client.get("/js/chart.js")
    assert res_js.status_code == 200
    assert "toggleHmbLine" in res_js.text
    assert "toggleNetFlow" in res_js.text
    assert "NET_FLOW" in res_js.text
    assert "openBroksumSheet" in res_js.text
    assert "applyBroksumPreset" in res_js.text
    assert "fetchBroksumRange" in res_js.text
    assert "saveOverlaysForSymbol" in res_js.text
    assert "loadOverlaysForSymbol" in res_js.text
    assert "clearManualOverlaysFromChart" in res_js.text
    assert "candlify_drawings_" in res_js.text
    assert "manualOverlayIds" in res_js.text
    assert "setupScreenerEvents" in res_js.text
    assert "openFilterModal" in res_js.text
    assert "closeFilterModal" in res_js.text
    assert "applyPresetFilter" in res_js.text
    assert "fetchScreenerData" in res_js.text
    assert "filterAndRenderScreener" in res_js.text
    assert "renderPagination" in res_js.text
    assert "openChartFromScreener" in res_js.text
    assert "renderQuickChipsFromList" in res_js.text
    assert "navigateFilteredStock" in res_js.text
    assert "switchView" in res_js.text
    assert "getDynamicMetric" in res_js.text

def test_api_broksum_range_bbri():
    res = client.get("/api/bandarmologi/broksum?symbol=BBRI")
    assert res.status_code == 200
    data = res.json()
    assert data.get("success") is True
    assert data.get("symbol") == "BBRI"
    assert "from_date" in data
    assert "to_date" in data
    assert "trading_days" in data
    assert "summary" in data
    summary = data["summary"]
    assert len(summary["top_buyers"]) > 0
    assert len(summary["top_sellers"]) > 0
    assert "latest_hmb" in summary
    assert "latest_net_flow" in summary

def test_api_screen():
    res = client.get("/api/screen?preset=all")
    assert res.status_code == 200
    data = res.json()
    assert data.get("success") is True
    assert data.get("count") > 0
    assert len(data.get("stocks", [])) > 0
    first = data["stocks"][0]
    assert "symbol" in first
    assert "price" in first
    assert "change_pct" in first

    # Test preset filter
    res_swing = client.get("/api/screen?preset=swing")
    assert res_swing.status_code == 200
    assert res_swing.json().get("success") is True

    # Test new sort options (3M, RSI)
    res_sort_3m = client.get("/api/screen?preset=all&sort=perf_3m_desc")
    assert res_sort_3m.status_code == 200
    assert res_sort_3m.json().get("success") is True

    res_sort_rsi = client.get("/api/screen?preset=all&sort=rsi_asc")
    assert res_sort_rsi.status_code == 200
    assert res_sort_rsi.json().get("success") is True

def test_api_database_health():
    res = client.get("/api/database/health")
    assert res.status_code == 200
    data = res.json()
    assert data.get("status") == "success"
    assert "data" in data
    d = data["data"]
    assert "saham" in d
    assert d["saham"]["total"] >= 900
    assert "archive" in d
    assert "stats" in d["archive"]
    assert d["archive"]["stats"]["total_harga"] > 0
    assert "history" in d
    assert isinstance(d["history"], list)
    assert len(d["history"]) > 0
    assert "available_months" in d
    assert len(d["available_months"]) >= 6
    assert "current_month" in d

    # Test /api/database/calendar endpoint for specific historical month (August 2026)
    res_cal = client.get("/api/database/calendar?month=2026-08")
    assert res_cal.status_code == 200
    cal_data = res_cal.json()
    assert cal_data.get("status") == "success"
    assert cal_data.get("month") == "2026-08"
    assert len(cal_data.get("history", [])) == 19

    # Also test legacy /api/stock?action=health alias
    res_alias = client.get("/api/stock?action=health")
    assert res_alias.status_code == 200
    assert res_alias.json().get("status") == "success"

def test_database_ui_elements():
    res = client.get("/")
    assert res.status_code == 200
    html = res.text
    assert "database-view" in html
    assert "live-clock" in html
    assert "db-stat-total-emiten" in html
    assert "db-stat-active-price" in html
    assert "db-stat-active-broksum" in html
    assert "db-stat-date-range" in html
    assert "calendar-grid" in html
    assert "calendar-month-title" in html
    assert "btn-cal-prev" in html
    assert "btn-cal-next" in html
    assert "btnActionSuspend" in html
    assert "btnActionLogs" in html
    assert "btnActionUpload" in html
    assert "uploadModal" in html
    assert "suspendModal" in html
    assert "logsModal" in html
    assert "db-dropzone" in html

    res_js = client.get("/js/chart.js")
    assert res_js.status_code == 200
    assert "setupDatabaseEvents" in res_js.text
    assert "renderSyncCalendar" in res_js.text
    assert "navigateCalendarMonth" in res_js.text
    assert "openUploadModal" in res_js.text


def test_api_screener_pre_breakout():
    res = client.get("/api/screener/pre-breakout")
    assert res.status_code == 200
    data = res.json()
    assert data.get("success") is True
    assert "date" in data
    assert "count" in data
    assert "signals" in data
    assert isinstance(data["signals"], list)
    if data["count"] > 0:
        sig = data["signals"][0]
        assert "ticker" in sig
        assert "price" in sig
        assert "range_7" in sig
        assert "volume_dry_ratio" in sig
        assert "score" in sig


def test_api_screen_preset_pre_breakout():
    res = client.get("/api/screen?preset=pre_breakout")
    assert res.status_code == 200
    data = res.json()
    assert data.get("success") is True
    assert data.get("preset") == "pre_breakout"
    assert "stocks" in data
    assert isinstance(data["stocks"], list)
    if len(data["stocks"]) > 0:
        st = data["stocks"][0]
        assert st.get("is_pre_breakout") is True
        assert "score" in st


def test_api_screener_pre_breakout_validation():
    # Test min_score > 100
    res_err1 = client.get("/api/screener/pre-breakout?min_score=150")
    assert res_err1.status_code == 422

    # Test limit < 1
    res_err2 = client.get("/api/screener/pre-breakout?limit=0")
    assert res_err2.status_code == 422


def test_pre_breakout_ui_elements():
    res_html = client.get("/")
    assert res_html.status_code == 200
    assert 'data-preset="pre_breakout"' in res_html.text
    assert 'score_desc' in res_html.text

    res_js = client.get("/js/chart.js")
    assert res_js.status_code == 200
    assert "pre_breakout" in res_js.text
    assert "stock-badge-prebreakout" in res_js.text


def test_api_docs_bandarmology():
    res = client.get("/api/docs/bandarmology")
    assert res.status_code == 200
    data = res.json()
    assert data.get("success") is True
    assert "markdown" in data
    assert len(data["markdown"]) > 1000
    assert "Pre-Breakout" in data["markdown"] or "Bandarmology" in data["markdown"]


def test_doc_reader_ui_elements():
    res_html = client.get("/")
    assert res_html.status_code == 200
    assert "btn-open-doc-modal" in res_html.text
    assert "doc-reader-modal" in res_html.text
    assert "marked.min.js" in res_html.text

    res_js = client.get("/js/chart.js")
    assert res_js.status_code == 200
    assert "btn-open-doc-modal" in res_js.text
    assert "doc-reader-modal" in res_js.text
    assert "marked.parse" in res_js.text


def test_api_stock_historical_data_bbri():
    res = client.get("/api/stock/historical-data?symbol=BBRI&timeframe=daily&limit=20")
    assert res.status_code == 200
    data = res.json()
    assert data.get("success") is True
    assert data.get("symbol") == "BBRI"
    assert data.get("timeframe") == "daily"
    assert "data" in data
    assert isinstance(data["data"], list)
    if data["data"]:
        first = data["data"][0]
        assert "date" in first
        assert "close" in first
        assert "change_pct" in first
        assert "value" in first


def test_api_bandarmologi_broker_activity_bbri():
    res = client.get("/api/bandarmologi/broker-activity?symbol=BBRI&broker_code=XL")
    assert res.status_code == 200
    data = res.json()
    assert data.get("success") is True
    assert data.get("symbol") == "BBRI"
    assert data.get("broker_code") == "XL"
    assert "month" in data
    assert "trading_days" in data
    assert "monthly_net_vol" in data
    assert "monthly_net_val" in data
    assert "daily_activity" in data
    assert isinstance(data["daily_activity"], list)


def test_api_bandarmologi_broker_flow_bbri():
    res = client.get("/api/bandarmologi/broker-flow?symbol=BBRI&days=30&metric=val")
    assert res.status_code == 200
    data = res.json()
    assert data.get("success") is True
    assert data.get("symbol") == "BBRI"
    assert data.get("metric") == "val"
    assert "dates" in data
    assert "series" in data
    assert "top_brokers" in data
    assert "summary" in data
    assert isinstance(data["dates"], list)
    assert isinstance(data["top_brokers"], list)


def test_order_flow_ui_elements():
    res_html = client.get("/")
    assert res_html.status_code == 200
    assert "broksum-nav-tabs" in res_html.text
    assert "tab-pane-summary" in res_html.text
    assert "tab-pane-history" in res_html.text
    assert "tab-pane-flow" in res_html.text
    assert "tab-pane-activity" in res_html.text
    assert "ticker-board-badge" in res_html.text
    assert "broker-flow-canvas" in res_html.text
    assert "activity-calendar-grid" in res_html.text
    assert "activity-broker-chips" in res_html.text

    res_js = client.get("/js/chart.js")
    assert res_js.status_code == 200
    assert "setupBroksumSubTabEvents" in res_js.text
    assert "loadHistoryTable" in res_js.text
    assert "loadBrokerFlow" in res_js.text
    assert "loadBrokerActivity" in res_js.text
    assert "renderActivityCalendar" in res_js.text
    assert "renderActivityBrokerChips" in res_js.text



