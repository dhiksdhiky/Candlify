"""
lib/pre_breakout_report.py — Hybrid Dynamic Pre-Breakout Performance Report
===========================================================================
Menghitung evaluasi performa sinyal Pre-Breakout secara live dari tabel
`candlify_signals` dan `harga_saham` (window T+1 s/d T+10), lalu menggabungkannya
dengan catatan forensik manual yang tersimpan di `docs/04_LAPORAN_KINERJA_PRE_BREAKOUT.md`.

Keunggulan arsitektur Hybrid:
- Angka performa & status (HIT / STOP OUT / RUNNING / EXPIRED) selalu up-to-date otomatis.
- Catatan interpretasi mendalam dari analisis berkala tersimpan aman di file .md (tidak tertimpa).
- Sinyal RUNNING yang belum dianalisis menampilkan kolom evaluasi kosong (`—`).
- Menggunakan in-memory cache (TTL 10 menit) agar nol beban untuk Neon DB.
"""

import logging
import re
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from lib.db import get_engine

logger = logging.getLogger("candlify.pre_breakout_report")

_REPORT_CACHE: Dict[str, Any] = {"timestamp": 0.0, "markdown_section": None, "stats": None}
_REPORT_LOCK = threading.Lock()
_REPORT_TTL = 600.0  # 10 menit

PLACEHOLDER_TAG = "<!-- LIVE_PRE_BREAKOUT_SCORECARD -->"
NOTES_PATTERN = re.compile(
    r"<!--\s*FORENSIC_NOTES_START\s*(.*?)\s*FORENSIC_NOTES_END\s*-->",
    re.DOTALL,
)


def clear_report_cache() -> None:
    with _REPORT_LOCK:
        _REPORT_CACHE["timestamp"] = 0.0
        _REPORT_CACHE["markdown_section"] = None
        _REPORT_CACHE["stats"] = None


def parse_forensic_notes(markdown_text: str) -> Dict[str, str]:
    """
    Parse catatan forensik manual dari blok komentar:
    <!-- FORENSIC_NOTES_START
    2026-10-02|DKHH: Multi-bagger T+2, base kering di 69 reli 3 hari ke 127.
    2026-10-16|BINA: Waspada crossing Pasar Nego RS/RB Rp 102,5 M (Standby Repo).
    FORENSIC_NOTES_END -->
    """
    notes_map: Dict[str, str] = {}
    match = NOTES_PATTERN.search(markdown_text or "")
    if not match:
        return notes_map

    block = match.group(1)
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key_part, note_part = line.split(":", 1)
            key_clean = key_part.strip().upper()
            note_clean = note_part.strip()
            if "|" in key_clean and note_clean:
                notes_map[key_clean] = note_clean
    return notes_map


def _fmt_rp(val: float) -> str:
    try:
        return f"Rp {int(round(val)):,}".replace(",", ".")
    except Exception:
        return f"Rp {val}"


def evaluate_all_signals_from_db() -> Dict[str, Any]:
    """
    Evaluasi seluruh sinyal historis pada tabel `candlify_signals` menggunakan data
    harga T+1 s/d T+10 dari tabel `harga_saham`.
    """
    engine = get_engine()
    if not engine:
        return {"success": False, "error": "Database tidak terhubung", "records": []}

    try:
        with engine.connect() as conn:
            sig_rows = conn.execute(
                text("""
                    SELECT
                        date, ticker, price, score, range_7, volume_dry_ratio,
                        top_accumulator, dominance, aar, is_pocket_pivot
                    FROM candlify_signals
                    ORDER BY date DESC, score DESC
                """)
            ).fetchall()

            if not sig_rows:
                return {
                    "success": True,
                    "latest_market_date": None,
                    "total": 0,
                    "records": [],
                }

            latest_market_date = conn.execute(text("SELECT MAX(tanggal) FROM harga_saham")).scalar()
            latest_market_str = str(latest_market_date)[:10] if latest_market_date else None

            tickers = sorted({str(r[1]) for r in sig_rows if r[1]})
            min_sig_date = min(str(r[0])[:10] for r in sig_rows)

            # Query harga_saham portabel untuk SQLite & PostgreSQL
            placeholders = ", ".join([f":t_{i}" for i in range(len(tickers))])
            params: Dict[str, Any] = {f"t_{i}": tickers[i] for i in range(len(tickers))}
            params["min_d"] = min_sig_date

            price_rows = conn.execute(
                text(f"""
                    SELECT ticker, tanggal, high, low, close
                    FROM harga_saham
                    WHERE ticker IN ({placeholders})
                      AND tanggal >= :min_d
                    ORDER BY ticker ASC, tanggal ASC
                """),
                params,
            ).fetchall()

        price_map: Dict[str, List[Tuple[str, float, float, float]]] = {}
        for pr in price_rows:
            tkr = str(pr[0])
            price_map.setdefault(tkr, []).append(
                (str(pr[1])[:10], float(pr[2] or 0.0), float(pr[3] or 0.0), float(pr[4] or 0.0))
            )

        records: List[Dict[str, Any]] = []
        for r in sig_rows:
            sig_date = str(r[0])[:10]
            ticker = str(r[1])
            p0 = float(r[2] or 0.0)
            score = int(r[3] or 0)
            dom = float(r[7] or 0.0)
            aar = float(r[8] or 1.0)
            top_acc = str(r[6] or "-")

            if p0 <= 0:
                continue

            bars = [b for b in price_map.get(ticker, []) if b[0] > sig_date][:10]
            days_elapsed = len(bars)

            if days_elapsed == 0:
                records.append({
                    "date": sig_date,
                    "ticker": ticker,
                    "p0": p0,
                    "score": score,
                    "top_acc": top_acc,
                    "dom": dom,
                    "aar": aar,
                    "days_elapsed": 0,
                    "p_max": p0,
                    "p_min": p0,
                    "p_last": p0,
                    "max_gain": 0.0,
                    "max_dd": 0.0,
                    "cur_pnl": 0.0,
                    "status": "⏳ RUNNING",
                    "event_day": 0,
                })
                continue

            p_max = max(b[1] for b in bars)
            p_min = min(b[2] for b in bars)
            p_last = bars[-1][3]
            max_gain = round(((p_max - p0) / p0) * 100.0, 1)
            max_dd = round(((p_min - p0) / p0) * 100.0, 1)
            cur_pnl = round(((p_last - p0) / p0) * 100.0, 1)

            hit_super = False
            hit_target = False
            stopped_out = False
            event_day = 0

            for idx, (_, b_high, b_low, _) in enumerate(bars, 1):
                h_gain = ((b_high - p0) / p0) * 100.0
                l_dd = ((b_low - p0) / p0) * 100.0

                if h_gain >= 15.0 and not stopped_out and not hit_target:
                    hit_super = True
                    hit_target = True
                    event_day = idx
                elif h_gain >= 8.0 and not stopped_out and not hit_target:
                    hit_target = True
                    event_day = idx

                if l_dd <= -4.0 and not hit_target:
                    stopped_out = True
                    event_day = idx
                    break

            if hit_super:
                status = "🎯 HIT (SUPER)"
            elif hit_target:
                status = "🎯 HIT"
            elif stopped_out:
                status = "🛑 STOP OUT"
            elif days_elapsed < 10:
                status = "⏳ RUNNING"
            else:
                status = "⚪ EXPIRED"

            records.append({
                "date": sig_date,
                "ticker": ticker,
                "p0": p0,
                "score": score,
                "top_acc": top_acc,
                "dom": dom,
                "aar": aar,
                "days_elapsed": days_elapsed,
                "p_max": p_max,
                "p_min": p_min,
                "p_last": p_last,
                "max_gain": max_gain,
                "max_dd": max_dd,
                "cur_pnl": cur_pnl,
                "status": status,
                "event_day": event_day,
            })

        return {
            "success": True,
            "latest_market_date": latest_market_str,
            "total": len(records),
            "records": records,
        }
    except Exception as e:
        logger.error(f"Error evaluating pre-breakout signals: {e}", exc_info=True)
        return {"success": False, "error": str(e), "records": []}


def build_live_scorecard_markdown(forensic_notes: Optional[Dict[str, str]] = None) -> str:
    """
    Bangun blok Markdown live scorecard dari Neon DB & gabungkan dengan catatan forensik manual.
    """
    notes_map = forensic_notes or {}
    eval_res = evaluate_all_signals_from_db()

    if not eval_res.get("success"):
        err = eval_res.get("error", "Koneksi database tidak tersedia")
        return f"> ⚠️ *Data scorecard live belum dapat dimuat dari Neon DB ({err}).*"

    records = eval_res.get("records", [])
    latest_dt = eval_res.get("latest_market_date") or "-"

    if not records:
        return "> ℹ️ *Belum ada sinyal historis tersimpan pada tabel `candlify_signals`.*"

    running = [r for r in records if "RUNNING" in r["status"]]
    hits = [r for r in records if "HIT" in r["status"]]
    stops = [r for r in records if "STOP" in r["status"]]
    expired = [r for r in records if "EXPIRED" in r["status"]]
    closed = hits + stops + expired

    win_rate = round((len(hits) / len(closed)) * 100.0, 1) if closed else 0.0
    avg_hit_gain = round(sum(r["max_gain"] for r in hits) / len(hits), 1) if hits else 0.0
    avg_stop_dd = round(sum(r["max_dd"] for r in stops) / len(stops), 1) if stops else 0.0

    # Pisahkan sinyal V2 (>= 2026-10-16) untuk transparansi performa rumus baru
    v2_records = [r for r in records if r["date"] >= "2026-10-16"]
    v2_hits = [r for r in v2_records if "HIT" in r["status"]]
    v2_closed = [r for r in v2_records if "RUNNING" not in r["status"]]
    v2_wr = f"{round((len(v2_hits) / len(v2_closed)) * 100.0, 1)}%" if v2_closed else "Menunggu penutupan window T+10"

    lines: List[str] = []
    lines.append(f"> 🔄 **Live Scorecard Neon DB** • Data Harga Terakhir: **`{latest_dt}`** • Total Sinyal Terekam: **`{len(records)}`**")
    lines.append("")
    lines.append("| Ringkasan Metrik Keseluruhan (V1 + V2) | Nilai |")
    lines.append("| :--- | :---: |")
    lines.append(f"| 🎯 **Total HIT ($\ge +8\%$ s/d ARA)** | **{len(hits)} sinyal** *(Avg Gain: `+{avg_hit_gain}%`)* |")
    lines.append(f"| ⏳ **Sedang Berjalan (`RUNNING` $< T+10$)** | **{len(running)} sinyal** |")
    lines.append(f"| 🛑 **Total STOP OUT ($\le -4\%$)** | **{len(stops)} sinyal** *(Avg DD: `{avg_stop_dd}%`)* |")
    lines.append(f"| ⚪ **EXPIRED (Datar 10 Hari)** | **{len(expired)} sinyal** |")
    lines.append(f"| 📈 **Win Rate Sinyal Selesai (Gabungan V1+V2)** | **{win_rate}%** *({len(hits)} / {len(closed)})* |")
    lines.append(f"| 🚀 **Tracking Khusus Era V2 ($\ge$ 16 Okt 2026)** | **{len(v2_records)} sinyal** *(Win Rate: {v2_wr})* |")
    lines.append("")

    # 1. Tabel Sinyal RUNNING
    lines.append("### ⏳ A. Sinyal Aktif Berjalan (`RUNNING`)")
    lines.append("")
    if not running:
        lines.append("*Tidak ada sinyal yang sedang berstatus RUNNING saat ini.*")
    else:
        lines.append("| Tanggal | Ticker | Skor | Entry ($P_0$) | Hari | Close | P&L | Status | Evaluasi / Interpretasi |")
        lines.append("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |")
        for r in running:
            key = f"{r['date']}|{r['ticker']}".upper()
            note = notes_map.get(key, "—")
            pnl_str = f"{r['cur_pnl']:+.1f}%"
            lines.append(
                f"| {r['date']} | **{r['ticker']}** | {r['score']} | {_fmt_rp(r['p0'])} | T+{r['days_elapsed']} | {_fmt_rp(r['p_last'])} | **{pnl_str}** | {r['status']} | {note} |"
            )
    lines.append("")

    # 2. Tabel Sinyal HIT (Juara Breakout)
    lines.append("### 🎯 B. Histori Sinyal Berhasil (`HIT` $\ge +8\%$)")
    lines.append("")
    if not hits:
        lines.append("*Belum ada sinyal selesai yang mencapai target HIT.*")
    else:
        hits_sorted = sorted(hits, key=lambda x: (x["date"], x["max_gain"]), reverse=True)
        lines.append("| Tanggal | Ticker | Skor | Entry ($P_0$) | Max High | Max Gain | Max DD | Status | Evaluasi / Interpretasi |")
        lines.append("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |")
        for r in hits_sorted[:30]:
            key = f"{r['date']}|{r['ticker']}".upper()
            default_note = f"Target T+{r['event_day']} (High {_fmt_rp(r['p_max'])})" if r["event_day"] > 0 else "—"
            note = notes_map.get(key, default_note)
            lines.append(
                f"| {r['date']} | **{r['ticker']}** | {r['score']} | {_fmt_rp(r['p0'])} | {_fmt_rp(r['p_max'])} | **+{r['max_gain']:.1f}%** | {r['max_dd']:.1f}% | {r['status']} | {note} |"
            )
    lines.append("")

    # 3. Tabel Sampel STOP OUT / EXPIRED Terbaru (Maks 20 baris agar tetap ringkas)
    failed_or_exp = sorted(stops + expired, key=lambda x: (x["date"], x["max_dd"]), reverse=True)
    lines.append("### 🛑 C. Histori Sinyal Gagal / Datar Terbaru (Bahan Audit Rumus)")
    lines.append("")
    if not failed_or_exp:
        lines.append("*Belum ada sinyal STOP OUT atau EXPIRED.*")
    else:
        lines.append("| Tanggal | Ticker | Skor | Entry ($P_0$) | Max Gain | Max DD | Status | Evaluasi / Interpretasi |")
        lines.append("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |")
        for r in failed_or_exp[:20]:
            key = f"{r['date']}|{r['ticker']}".upper()
            default_note = f"Cut loss T+{r['event_day']}" if "STOP" in r["status"] and r["event_day"] > 0 else "—"
            note = notes_map.get(key, default_note)
            lines.append(
                f"| {r['date']} | **{r['ticker']}** | {r['score']} | {_fmt_rp(r['p0'])} | +{r['max_gain']:.1f}% | {r['max_dd']:.1f}% | {r['status']} | {note} |"
            )
        if len(failed_or_exp) > 20:
            lines.append("")
            lines.append(f"*Menampilkan 20 sinyal terbaru dari total {len(failed_or_exp)} sinyal gagal/datar historis.*")

    return "\n".join(lines)


def render_hybrid_pre_breakout_doc(raw_markdown: str) -> str:
    """
    Gabungkan file Markdown statis dengan tabel live scorecard dari Neon DB
    jika placeholder `<!-- LIVE_PRE_BREAKOUT_SCORECARD -->` ditemukan.
    """
    if PLACEHOLDER_TAG not in raw_markdown:
        return raw_markdown

    forensic_notes = parse_forensic_notes(raw_markdown)
    now = time.time()

    with _REPORT_LOCK:
        cached_md = _REPORT_CACHE.get("markdown_section")
        cached_notes_hash = _REPORT_CACHE.get("notes_hash")
        cur_notes_hash = hash(tuple(sorted(forensic_notes.items())))
        if cached_md is not None and cached_notes_hash == cur_notes_hash and (now - _REPORT_CACHE["timestamp"] < _REPORT_TTL):
            live_section = cached_md
        else:
            live_section = None

    if live_section is None:
        live_section = build_live_scorecard_markdown(forensic_notes)
        with _REPORT_LOCK:
            _REPORT_CACHE["timestamp"] = now
            _REPORT_CACHE["markdown_section"] = live_section
            _REPORT_CACHE["notes_hash"] = hash(tuple(sorted(forensic_notes.items())))

    return raw_markdown.replace(PLACEHOLDER_TAG, live_section)
