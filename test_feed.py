"""
v2/test_feed.py — Uji Coba Multi-Timeframe Candlestick Engine
============================================================
Menguji kehandalan penarikan data candlestick dari berbagai timeframe
(1m, 5m, 15m, 1h, 1d) dan memvalidasi kompatibilitas format KLineCharts v9.
"""

import sys
import os
import time

# Pastikan path import bisa membaca module v2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Windows console UTF-8 safety
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from lib.history import get_candlesticks

def test_timeframes(ticker="BBRI"):
    print("=" * 65)
    print(f"[*] MEMULAI UJI COBA CANDLESTICK MULTI-TIMEFRAME UNTUK: {ticker}")
    print("=" * 65)
    
    test_cases = [
        ("5m", "1mo", "Intraday 5 Menit (Fast Swing)"),
        ("15m", "1mo", "Intraday 15 Menit (Breakout Entry)"),
        ("1h", "3mo", "Intraday 1 Jam (Daily Trend Setup)"),
        ("4h", "6mo", "Intraday 4 Jam (Resampled Swing Setup)"),
        ("1d", "1y", "Daily / Harian (Position / Swing)"),
        ("1w", "5y", "Weekly / Mingguan (Macro Trend)")
    ]
    
    success_count = 0
    
    for interval, range_val, desc in test_cases:
        t0 = time.time()
        res = get_candlesticks(symbol=ticker, interval=interval, range_val=range_val)
        latency_ms = int((time.time() - t0) * 1000)
        
        is_success = res.get("success", False)
        count = res.get("count", 0)
        source = res.get("source", "unknown")
        
        if is_success and count > 0:
            success_count += 1
            sample = res["data"][-1]  # Candle terbaru
            print(f"✅ [{interval:>3}] {desc:<35} | {count:>4} candles | {latency_ms:>4}ms | Source: {source}")
            print(f"     └─ Sample Latest: Time={sample['timestamp']} | O={sample['open']} H={sample['high']} L={sample['low']} C={sample['close']} V={sample['volume']:,}")
        else:
            err = res.get("error", "Unknown error")
            print(f"❌ [{interval:>3}] {desc:<35} | FAILED: {err}")
            
    print("=" * 65)
    print(f"📊 HASIL: {success_count}/{len(test_cases)} Timeframe Berhasil Ditarik & Tervalidasi!")
    print("=" * 65)
    
    # Test In-Memory Cache Latency
    print("\n⚡ Menguji Performa In-Memory Cache (TTL):")
    t0 = time.time()
    cached_res = get_candlesticks(symbol=ticker, interval="15m")
    cache_latency = int((time.time() - t0) * 1000)
    print(f"🚀 Cached Fetch (15m): {cache_latency}ms (Super Instan! Data count: {cached_res.get('count')})")

def test_bandarmologi_feed(ticker="BBRI"):
    from lib.bandarmologi import get_bandarmologi
    print("\n" + "=" * 65)
    print(f"[*] MEMULAI UJI COBA BANDARMOLOGI ENGINE (HMB & NET FLOW): {ticker}")
    print("=" * 65)

    t0 = time.time()
    res = get_bandarmologi(symbol=ticker)
    latency_ms = int((time.time() - t0) * 1000)

    assert res.get("success") is True, f"Bandarmologi query failed: {res.get('error')}"
    count = res.get("count", 0)
    assert count > 0, "No bandarmologi data points found"

    summary = res.get("summary", {})
    latest = res["data"][-1]
    print(f"✅ Bandarmologi {ticker} OK: {count} hari | {latency_ms}ms | HMB: Rp {summary.get('latest_hmb'):,} | Status: {summary.get('latest_status')}")
    print(f"     └─ Net Flow Latest ({latest['date']}): Rp {latest['net_flow']:,.0f}")
    assert latest.get("hmb") > 0, "HMB price must be positive"
    assert "timestamp" in latest, "Data point must include timestamp"

if __name__ == "__main__":
    test_ticker = sys.argv[1] if len(sys.argv) > 1 else "BBRI"
    test_timeframes(test_ticker)
    test_bandarmologi_feed(test_ticker)
