"""
v2/test_trading_plan.py — Integration Tests for Trading Plan & Journal Module
=============================================================================
Tests:
- GET /api/trading-plans (list with enrichment)
- POST /api/trading-plans (create with auto lot sizing)
- GET /api/trading-plans/stats (portfolio swing metrics)
- PUT /api/trading-plans/{id} (trailing stop & match transition)
- PUT /api/trading-plans/{id} (close position with realized PnL)
- DELETE /api/trading-plans/{id}
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import app

client = TestClient(app)

def test_trading_plan_full_lifecycle():
    # 1. Check initial stats
    res_stats = client.get("/api/trading-plans/stats")
    assert res_stats.status_code == 200
    assert "holding_count" in res_stats.json()

    # 2. Create a new Trading Plan (Antri limit order)
    plan_payload = {
        "symbol": "BBCA",
        "category": "Breakout",
        "order_type": "LIMIT",
        "entry_price": 10000.0,
        "sl_price": 9600.0,
        "tp1_price": 11000.0,
        "tp2_price": 11500.0,
        "notes": "Testing Swing Breakout R1",
        "status": "ANTRI"
    }
    res_create = client.post("/api/trading-plans", json=plan_payload)
    assert res_create.status_code == 200
    created = res_create.json()
    assert created.get("success") is True
    plan_id = created["data"]["id"]
    assert created["data"]["symbol"] == "BBCA"
    assert created["data"]["lot_size"] > 0
    assert created["data"]["risk_reward_ratio"] == 2.5  # (11000-10000) / (10000-9600) = 1000 / 400 = 2.5

    try:
        # 3. List plans and check enrichment
        res_list = client.get("/api/trading-plans?status=ANTRI")
        assert res_list.status_code == 200
        items = res_list.json().get("data", [])
        matched = [i for i in items if i["id"] == plan_id]
        assert len(matched) == 1
        item = matched[0]
        assert item["status"] == "ANTRI"
        assert "distance_to_entry_pct" in item

        # 4. Transition status: ANTRI -> HOLDING (Order Match)
        res_match = client.put(f"/api/trading-plans/{plan_id}", json={"status": "HOLDING"})
        assert res_match.status_code == 200
        assert res_match.json()["data"]["status"] == "HOLDING"
        assert res_match.json()["data"]["entry_date"] is not None

        # 4b. Edit entry price and custom lot size (regression test for user custom entries)
        res_edit = client.put(f"/api/trading-plans/{plan_id}", json={
            "entry_price": 9950.0,
            "lot_size": 15
        })
        assert res_edit.status_code == 200
        edited = res_edit.json()["data"]
        assert edited["entry_price"] == 9950.0
        assert edited["lot_size"] == 15

        # 5. Trailing Stop: Raise Stop Loss
        res_ts = client.put(f"/api/trading-plans/{plan_id}", json={"sl_price": 9850.0})
        assert res_ts.status_code == 200
        assert res_ts.json()["data"]["sl_price"] == 9850.0

        # 6. Exit Position: Hit TP1 -> Close Win
        res_close = client.put(f"/api/trading-plans/{plan_id}", json={
            "status": "CLOSED_WIN",
            "exit_price": 11050.0,
            "notes": "TP1 Hit, mantap swing cuan!"
        })
        assert res_close.status_code == 200
        closed_data = res_close.json()["data"]
        assert closed_data["status"] == "CLOSED_WIN"
        assert closed_data["exit_price"] == 11050.0
        assert closed_data["realized_pnl"] > 0
        assert closed_data["realized_pnl_pct"] > 0

    finally:
        # 7. Clean up
        res_del = client.delete(f"/api/trading-plans/{plan_id}")
        assert res_del.status_code == 200
        assert res_del.json().get("success") is True
