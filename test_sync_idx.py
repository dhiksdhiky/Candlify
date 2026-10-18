"""
test_sync_idx.py — Unit & Integration Tests for All-in-One IDX Daily Engine
===========================================================================
Menguji:
1. Decoding Remarks (Papan Pencatatan, Corporate Actions, Notasi Khusus BEI)
2. Parsing Payload IDX GetStockSummary (OHLCV, Foreign Flow, Free Float)
3. Schema Migration & Idempotency
4. History & Screener Compatibility
"""

import os
import sys
import pytest
from datetime import date
from unittest.mock import patch, MagicMock

# Ensure project root & worker are on sys.path
sys.path.insert(0, os.path.abspath("worker"))
sys.path.insert(0, os.path.abspath("."))

from worker.sync_idx_daily import (
    decode_remarks,
    parse_trading_summary_data,
    update_local_csv,
    sync_daftar_saham_bulk,
    sync_harga_saham_bulk,
    format_shares_dot
)
from worker.db_config import engine, migrate_schema, get_dialect
from sqlalchemy import text


class TestRemarksDecoder:
    """Pengujian logika decoding Remarks BEI."""

    def test_board_decoding_utama(self):
        remarks = "--MO1SD0F70000A121------------"
        board, notasi = decode_remarks(remarks)
        assert board == "Utama"
        assert notasi == ""

    def test_board_decoding_pengembangan(self):
        remarks = "--UO2105000000G412------------"
        board, notasi = decode_remarks(remarks)
        assert board == "Pengembangan"
        assert notasi == ""

    def test_board_decoding_akselerasi(self):
        remarks = "--U-3000000000E111------------"
        board, notasi = decode_remarks(remarks)
        assert board == "Akselerasi"
        assert notasi == ""

    def test_board_decoding_fca(self):
        remarks = "--U-4105000000J211ME---------X"
        board, notasi = decode_remarks(remarks)
        assert board == "Pemantauan Khusus"
        assert "X" in notasi
        assert "M" in notasi
        assert "E" in notasi

    def test_board_decoding_ekonomi_baru(self):
        remarks = "--UO5H40544000I111----------N-"
        board, notasi = decode_remarks(remarks)
        assert board == "Ekonomi Baru"
        assert "N" in notasi

    def test_corporate_action_xd(self):
        remarks = "XDMO113E100200D232------------"
        board, notasi = decode_remarks(remarks)
        assert board == "Utama"
        assert "XD" in notasi

    def test_corporate_action_xr(self):
        remarks = "XRUO2100000000G412------------"
        board, notasi = decode_remarks(remarks)
        assert board == "Pengembangan"
        assert "XR" in notasi

    def test_empty_or_short_remarks(self):
        board, notasi = decode_remarks("")
        assert board == "Pengembangan"
        assert notasi == ""

        board_short, notasi_short = decode_remarks("ABC")
        assert board_short == "Pengembangan"
        assert notasi_short == ""


class TestPayloadParser:
    """Pengujian penguraian payload JSON dari BEI."""

    def test_parse_sample_payload(self):
        sample_payload = {
            "draw": 0,
            "recordsTotal": 2,
            "recordsFiltered": 2,
            "data": [
                {
                    "No": 1,
                    "Date": "2026-10-16T00:00:00",
                    "StockCode": "BBCA",
                    "StockName": "Bank Central Asia Tbk.",
                    "Remarks": "--SO1UQNCNU100G111------------",
                    "Previous": 5200.0,
                    "OpenPrice": 5175.0,
                    "High": 5825.0,
                    "Low": 5175.0,
                    "Close": 5175.0,
                    "Volume": 1000000.0,
                    "Value": 5175000000.0,
                    "Frequency": 1500.0,
                    "ForeignBuy": 600000.0,
                    "ForeignSell": 400000.0,
                    "Offer": 5175.0,
                    "OfferVolume": 2000.0,
                    "Bid": 5150.0,
                    "BidVolume": 5000.0,
                    "ListedShares": 122000000000.0,
                    "TradebleShares": 100000000000.0,
                    "NonRegularVolume": 50000.0,
                    "NonRegularValue": 250000000.0,
                },
                {
                    "No": 2,
                    "Date": "2026-10-16T00:00:00",
                    "StockCode": "ACST",
                    "StockName": "Acset Indonusa Tbk.",
                    "Remarks": "--U-4105000000J211ME---------X",
                    "Previous": 76.0,
                    "OpenPrice": 0.0,
                    "High": 69.0,
                    "Low": 69.0,
                    "Close": 69.0,
                    "Volume": 871200.0,
                    "Value": 60112800.0,
                    "Frequency": 81.0,
                    "ForeignBuy": 0.0,
                    "ForeignSell": 0.0,
                    "Offer": 69.0,
                    "OfferVolume": 1400.0,
                    "Bid": 0.0,
                    "BidVolume": 0.0,
                    "ListedShares": 17675160000.0,
                    "TradebleShares": 17675160000.0,
                    "NonRegularVolume": 0.0,
                    "NonRegularValue": 0.0,
                }
            ]
        }

        rows_daftar, rows_harga, tgl = parse_trading_summary_data(sample_payload)

        assert tgl == date(2026, 10, 16)
        assert len(rows_daftar) == 2
        assert len(rows_harga) == 2

        # Check BBCA
        bbca_d = next(r for r in rows_daftar if r["kode"] == "BBCA")
        assert bbca_d["papan_pencatatan"] == "Utama"
        assert bbca_d["tradeable_shares"] == 100000000000
        assert bbca_d["saham"] == 122000000000

        bbca_h = next(r for r in rows_harga if r["ticker"] == "BBCA")
        assert bbca_h["close"] == 5175.0
        assert bbca_h["foreign_buy"] == 600000
        assert bbca_h["foreign_sell"] == 400000
        assert bbca_h["foreign_net"] == 200000  # buy - sell
        assert bbca_h["frequency"] == 1500
        assert bbca_h["value"] == 5175000000.0

        # Check ACST zero open handling
        acst_h = next(r for r in rows_harga if r["ticker"] == "ACST")
        assert acst_h["open"] == 69.0  # Fallback from 0.0 to close
        assert acst_h["foreign_net"] == 0

        # Check ACST notations
        acst_d = next(r for r in rows_daftar if r["kode"] == "ACST")
        assert acst_d["papan_pencatatan"] == "Pemantauan Khusus"
        assert "X" in acst_d["notasi_khusus"]


class TestFormattingAndCSV:
    """Pengujian utilitas format dot dan penulisan CSV."""

    def test_format_shares_dot(self):
        assert format_shares_dot(1924688333) == "1.924.688.333"
        assert format_shares_dot(0) == "0"
        assert format_shares_dot(500) == "500"

    def test_update_local_csv(self, tmp_path):
        csv_file = str(tmp_path / "test_daftar_saham.csv")
        dummy_rows = [
            {
                "kode": "BBCA",
                "nama_perusahaan": "Bank Central Asia Tbk.",
                "saham": 122042299500,
                "tradeable_shares": 122042299500,
                "papan_pencatatan": "Utama",
                "notasi_khusus": ""
            },
            {
                "kode": "ACST",
                "nama_perusahaan": "Acset Indonusa Tbk.",
                "saham": 17675160000,
                "tradeable_shares": 17675160000,
                "papan_pencatatan": "Pemantauan Khusus",
                "notasi_khusus": "M, E, X"
            }
        ]
        update_local_csv(dummy_rows, csv_file)

        assert os.path.exists(csv_file)
        with open(csv_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "BBCA" in content
            assert "ACST" in content
            assert "Pemantauan Khusus" in content


class TestDatabaseIntegration:
    """Pengujian migrasi skema dan integrasi query database."""

    def test_schema_migration_idempotent(self):
        # Jalankan migrasi berkali-kali tidak boleh melempar error
        migrate_schema()
        migrate_schema()

        with engine.connect() as conn:
            if get_dialect() == "sqlite":
                cols_h = [r[1] for r in conn.execute(text("PRAGMA table_info(harga_saham)")).fetchall()]
                cols_ds = [r[1] for r in conn.execute(text("PRAGMA table_info(daftar_saham)")).fetchall()]
            else:
                cols_h = [r[0] for r in conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'harga_saham'")).fetchall()]
                cols_ds = [r[0] for r in conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'daftar_saham'")).fetchall()]

            assert "tradeable_shares" in cols_ds
            assert "notasi_khusus" in cols_ds
            assert "foreign_net" in cols_h
            assert "value" in cols_h
            assert "frequency" in cols_h

    def test_screener_notasi_map(self):
        from lib.screener import get_stock_notasi_map, get_stock_board_map
        b_map = get_stock_board_map()
        n_map = get_stock_notasi_map()

        assert isinstance(b_map, dict)
        assert isinstance(n_map, dict)
        assert len(b_map) > 0
        # BBCA harus ada di b_map
        assert "BBCA" in b_map
        assert b_map["BBCA"] == "Utama"
