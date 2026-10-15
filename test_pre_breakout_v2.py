"""
test_pre_breakout_v2.py — Unit Tests for Pre-Breakout Enhancements & IDX Downloader
===================================================================================
Tests:
- StockRecord schema & validation
- DirectApiExtractor / StockRecord parsing
- calculate_score with Dominance (>= 30%) and Close Location Value (CLV)
- get_pre_breakout_signals schema integrity (board, is_fca, hmb, score)
"""

import pytest
from worker.downloader_idx import StockRecord
from worker.scanner_bali import calculate_score
from lib.screener import get_pre_breakout_signals, filter_by_preset


def test_stock_record_parsing():
    raw_data = {
        "Code": "BBCA",
        "Name": "Bank Central Asia Tbk.",
        "ListingDate": "2000-05-31T00:00:00",
        "Shares": 123275050000,
        "ListingBoard": "Utama",
        "Sector": "Financials",
        "No": 120
    }
    rec = StockRecord.from_raw(raw_data)
    assert rec.code == "BBCA"
    assert rec.name == "Bank Central Asia Tbk."
    assert rec.listing_date == "2000-05-31"
    assert rec.shares == 123275050000
    assert rec.listing_board == "Utama"
    assert rec.no == 120


def test_stock_record_invalid_code():
    with pytest.raises(ValueError):
        StockRecord.from_raw({"Code": "B@D!", "Name": "Test"})


def test_calculate_score_dominance_and_clv():
    # Skenario 1: Base rapat (2%), Volume kering (0.12x), BBW (5%), HMB dekat (1%), Dominansi kuat (45%), CLV tinggi (0.80)
    score_super = calculate_score(
        range_7=2.0,
        vol_dry=0.12,
        bbw=5.0,
        price=1000.0,
        hmb=1010.0,
        has_acc=True,
        dominance=45.0,
        clv=0.80
    )
    # 25 (base) + 25 (vol) + 15 (bbw) + 25 (hmb + dom) + 10 (clv) = 100
    assert score_super == 100

    # Skenario 2: Base lebih lebar (6%), Dominansi rendah (10%), CLV negatif (-0.60)
    score_mid = calculate_score(
        range_7=6.0,
        vol_dry=0.30,
        bbw=11.0,
        price=1000.0,
        hmb=1050.0,
        has_acc=True,
        dominance=10.0,
        clv=-0.60
    )
    assert score_mid < score_super
    assert score_mid >= 40


def test_pre_breakout_signals_schema():
    # Ambil sinyal pre-breakout (jika ada di DB)
    res = get_pre_breakout_signals(min_score=50, limit=5)
    assert res.get("success") is True
    signals = res.get("signals", [])
    if signals:
        first = signals[0]
        assert "ticker" in first
        assert "score" in first
        assert "board" in first
        assert "is_fca" in first
        assert isinstance(first["is_fca"], bool)
        assert first["board"] in ["Utama", "Pengembangan", "Pemantauan Khusus", "Akselerasi", "Ekonomi Baru"]


def test_screener_preset_pre_breakout_integration():
    mock_stocks = [
        {"symbol": "TEST1", "name": "Test 1 Tbk.", "price": 1000, "change_pct": 1.5, "volume": 100000, "market_cap": 1e12}
    ]
    # filter_by_preset pre_breakout
    result = filter_by_preset(mock_stocks, "pre_breakout")
    assert isinstance(result, list)
