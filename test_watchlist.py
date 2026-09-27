"""
v2/test_watchlist.py — Integration Tests for Watchlist & Risk Settings Endpoints
================================================================================
Tests:
- GET /api/watchlist
- POST /api/watchlist (Add to watchlist)
- PUT /api/watchlist/{id} (Update notes & target_entry)
- DELETE /api/watchlist/{id} (Delete from watchlist)
- GET /api/settings/risk
- POST /api/settings/risk
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import app

client = TestClient(app)

def test_watchlist_full_crud():
    # 1. Fetch initial watchlist
    res = client.get("/api/watchlist")
    assert res.status_code == 200
    json_data = res.json()
    assert json_data.get("success") is True
    assert isinstance(json_data.get("data"), list)

    # 2. Add a new stock to Watchlist
    payload = {
        "symbol": "TRUK",
        "category": "Breakout",
        "notes": "Konsolidasi di atas Pivot R1 bulanan",
        "target_entry": 2500.0
    }
    res_add = client.post("/api/watchlist", json=payload)
    assert res_add.status_code == 200
    add_data = res_add.json()
    assert add_data.get("success") is True
    item_id = add_data["data"]["id"]
    assert add_data["data"]["symbol"] == "TRUK"
    assert add_data["data"]["category"] == "Breakout"

    try:
        # 3. Fetch with category filter and verify live enrichment
        res_cat = client.get("/api/watchlist?category=Breakout")
        assert res_cat.status_code == 200
        items = res_cat.json().get("data", [])
        matched = [i for i in items if i["id"] == item_id]
        assert len(matched) == 1
        item = matched[0]
        assert item["symbol"] == "TRUK"
        assert item["category"] == "Breakout"
        assert "age" in item
        assert "change_pct" in item
        assert "volume" in item

        # 4. Update the item
        res_up = client.put(f"/api/watchlist/{item_id}", json={
            "notes": "Target breakout terkonfirmasi volume",
            "target_entry": 2550.0
        })
        assert res_up.status_code == 200
        up_data = res_up.json()
        assert up_data.get("success") is True
        assert up_data["data"]["target_entry"] == 2550.0
        assert up_data["data"]["notes"] == "Target breakout terkonfirmasi volume"

    finally:
        # 5. Delete the item to keep DB clean
        res_del = client.delete(f"/api/watchlist/{item_id}")
        assert res_del.status_code == 200
        assert res_del.json().get("success") is True

    # 6. Verify deleted
    res_verify = client.get("/api/watchlist")
    items_after = res_verify.json().get("data", [])
    assert not any(i["id"] == item_id for i in items_after)


def test_watchlist_delete_invalid_id():
    res = client.delete("/api/watchlist/99999999")
    assert res.status_code == 404


def test_watchlist_add_invalid_symbol():
    res = client.post("/api/watchlist", json={"symbol": ""})
    assert res.status_code == 400


def test_risk_settings_flow():
    # 1. Get risk settings
    res = client.get("/api/settings/risk")
    assert res.status_code == 200
    data = res.json().get("data", {})
    assert "total_capital" in data
    assert "risk_pct" in data
    assert "risk_nominal" in data

    # 2. Save new risk settings (e.g. 100jt, 1.0%)
    res_save = client.post("/api/settings/risk", json={
        "total_capital": 100000000,
        "risk_pct": 1.0,
        "default_category": "Breakout",
        "daily_source": "neon_db"
    })
    assert res_save.status_code == 200
    save_data = res_save.json().get("data", {})
    assert save_data["total_capital"] == 100000000
    assert save_data["risk_pct"] == 1.0
    assert save_data["risk_nominal"] == 1000000


def test_watchlist_categories_flow():
    # 1. Get initial categories (must contain Breakout)
    res = client.get("/api/watchlist/categories")
    assert res.status_code == 200
    cats = res.json().get("categories", [])
    assert "Breakout" in cats

    # 2. Add new category
    test_cat = "Uji Coba Swing"
    res_add = client.post("/api/watchlist/categories", json={"name": test_cat})
    assert res_add.status_code == 200
    assert test_cat in res_add.json().get("categories", [])

    # Duplicate add must fail (400)
    res_dup = client.post("/api/watchlist/categories", json={"name": test_cat})
    assert res_dup.status_code == 400

    try:
        # 3. Rename category
        renamed_cat = "Uji Coba Swing Renamed"
        res_rename = client.put(f"/api/watchlist/categories/{test_cat}", json={"new_name": renamed_cat})
        assert res_rename.status_code == 200
        assert renamed_cat in res_rename.json().get("categories", [])
        assert test_cat not in res_rename.json().get("categories", [])
    finally:
        # 4. Delete category (cleanup)
        res_del = client.delete(f"/api/watchlist/categories/{renamed_cat}")
        assert res_del.status_code == 200
        assert renamed_cat not in res_del.json().get("categories", [])
        assert "Breakout" in res_del.json().get("categories", [])

    # Cannot delete Breakout (400)
    res_del_breakout = client.delete("/api/watchlist/categories/Breakout")
    assert res_del_breakout.status_code == 400


def test_stock_sync_multi_watchlists():
    # 1. Sync stock to multiple categories: Breakout and custom test category
    test_sym = "MEDC"
    sync_payload = {
        "symbol": test_sym,
        "categories": ["Breakout"],
        "target_entry": 1350.0,
        "notes": "Testing multi-category sync"
    }
    res_sync = client.post("/api/watchlist/sync-stock", json=sync_payload)
    assert res_sync.status_code == 200
    assert res_sync.json().get("success") is True
    assert "Breakout" in res_sync.json().get("categories", [])

    # 2. Query stock status
    res_get = client.get(f"/api/watchlist/stock/{test_sym}")
    assert res_get.status_code == 200
    stock_data = res_get.json()
    assert stock_data.get("success") is True
    assert "Breakout" in stock_data.get("categories", [])
    assert stock_data.get("target_entry") == 1350.0

    # 3. Clean up: sync with empty categories (remove from all watchlists)
    res_clean = client.post("/api/watchlist/sync-stock", json={"symbol": test_sym, "categories": []})
    assert res_clean.status_code == 200
    assert res_clean.json().get("success") is True

    # 4. Verify stock is no longer in any watchlist
    res_after = client.get(f"/api/watchlist/stock/{test_sym}")
    assert res_after.status_code == 200
    assert len(res_after.json().get("categories", [])) == 0


