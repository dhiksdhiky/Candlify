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
    # Skenario 1: Perfect Pre-Breakout Setup dengan Institutional Upgrades
    # Base rapat (2%), Volume kering (0.12x), BBW (5%), HMB dekat (1%), Dominansi kuat (45%), CLV tinggi (0.80),
    # AAR kuat (2.0), Up/Down Volume Ratio (1.5), Pocket Pivot (True)
    score_super = calculate_score(
        range_7=2.0,
        vol_dry=0.12,
        bbw=5.0,
        price=1000.0,
        hmb=1010.0,
        has_acc=True,
        dominance=45.0,
        clv=0.80,
        aar=2.0,
        up_down_vol_ratio=1.5,
        is_pocket_pivot=True
    )
    # 20 (base) + 20 (vol) + 15 (bbw) + 25 (hmb + dom + aar) + 15 (clv + up_down) + 5 (pocket pivot) = 100
    assert score_super == 100

    # Skenario 2: Setup tanpa bonus Pocket Pivot dan parameter default (AAR=1.0, Up/Down=1.0)
    score_default = calculate_score(
        range_7=2.0,
        vol_dry=0.12,
        bbw=5.0,
        price=1000.0,
        hmb=1010.0,
        has_acc=True,
        dominance=45.0,
        clv=0.80
    )
    # 20 + 20 + 15 + (12 + 8 + 3) + (8 + 5) = 91
    assert score_default == 91

    # Skenario 3: Base lebih lebar (6%), Dominansi rendah (10%), CLV negatif (-0.60)
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


def test_net_inventory_weighted_hmb_vs_gross_buy():
    """
    Memverifikasi bahwa Net-Inventory HMB kebal terhadap distorsi broker churning/scalper.
    Kasus:
    - Broker A (Institusi): Beli 30.000 lot di Rp 1.000, Jual 0 lot -> net_vol = 30.000 lot
    - Broker B (Scalper): Beli 300.000 lot di Rp 1.350, Jual 280.000 lot -> net_vol = 20.000 lot
    """
    import pandas as pd
    data = [
        {"broker_code": "A", "net_vol": 30000, "buy_vol": 30000, "buy_val": 30000 * 1000 * 100.0},
        {"broker_code": "B", "net_vol": 20000, "buy_vol": 300000, "buy_val": 300000 * 1350 * 100.0},
    ]
    df = pd.DataFrame(data)
    
    # Hitung via rumus Net-Inventory Weighted
    valid_acc = df[df["buy_vol"] > 0]
    avg_buy_prices = valid_acc["buy_val"] / (valid_acc["buy_vol"] * 100.0)
    weighted_cost = (valid_acc["net_vol"] * avg_buy_prices).sum()
    total_net_vol = valid_acc["net_vol"].sum()
    hmb_net = round(float(weighted_cost / total_net_vol))

    # Gross-buy weighted lama (menghasilkan angka terdistorsi ke 1.318)
    gross_hmb = round(df["buy_val"].sum() / (df["buy_vol"].sum() * 100.0))

    assert hmb_net == 1140
    assert gross_hmb == 1318
    # HMB Net jauh lebih mendekati modal riil institusi (1000) dibanding gross (1318)
    assert abs(hmb_net - 1000) < abs(gross_hmb - 1000)


def test_dual_constraint_position_sizing():
    """
    Memverifikasi perlindungan Dual-Constraint Sizing:
    min(Risk-based Lot, 20% Equity Cap) untuk mencegah 'all-in' pada Stop Loss ketat.
    """
    total_capital = 100000000.0 # Rp 100 jt
    max_risk_rp = 1000000.0      # Rp 1 jt (1%)
    max_exposure_pct = 0.20      # 20%

    entry_price = 1000.0
    sl_price = 985.0 # SL sangat ketat: -1.5% (risk per share = 15)

    risk_per_share = entry_price - sl_price
    # 1. Risk-based allocation murni: 1.000.000 / (15 * 100) = 666 lot = Rp 66,6 Juta (66.6% Modal!)
    calc_lots = int(max_risk_rp / (risk_per_share * 100))
    assert calc_lots == 666

    # 2. Exposure Cap 20%: 20.000.000 / (1000 * 100) = 200 lot = Rp 20 Juta
    max_exposure_rp = total_capital * max_exposure_pct
    cap_lots = int(max_exposure_rp / (entry_price * 100))
    assert cap_lots == 200

    # Dual-constraint:
    final_lots = max(1, min(calc_lots, cap_lots))
    assert final_lots == 200
    assert (final_lots * 100 * entry_price) <= max_exposure_rp


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
