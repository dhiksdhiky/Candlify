"""
lib/pre_breakout_report.py — Hybrid Dynamic Pre-Breakout Performance Report
===========================================================================
Menghitung evaluasi performa sinyal Pre-Breakout secara live dari tabel
`candlify_signals` dan `harga_saham` (window T+1 s/d T+10), lalu menggabungkannya
dengan catatan forensik manual yang tersimpan di `docs/04_LAPORAN_KINERJA_PRE_BREAKOUT.md`.

Arsitektur Future-Proof:
- Freeze/Persist hasil evaluasi sinyal yang sudah selesai (HIT / STOP OUT / EXPIRED)
  langsung ke kolom `eval_*` di `candlify_signals` sehingga tidak pernah dihitung ulang.
- Hanya sinyal berstatus `RUNNING` yang di-query ke `harga_saham` (super ringan < 50ms).
- Dilengkapi Tabel Rekap Kinerja per Bulan untuk memantau tren Win Rate jangka panjang.
- Sinyal `RUNNING` tanpa catatan forensik menampilkan kolom evaluasi kosong (`—`).
"""

import logging
import re
import threading
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import text
from lib.db import get_engine

logger = logging.getLogger("candlify.pre_breakout_report")

_REPORT_CACHE: Dict[str, Any] = {"timestamp": 0.0, "markdown_section": None, "notes_hash": None}
_REPORT_LOCK = threading.Lock()
_REPORT_TTL = 600.0  # 10 menit
_MIGRATED_ENGINE_IDS: Set[int] = set()

PLACEHOLDER_TAG = "<!-- LIVE_PRE_BREAKOUT_SCORECARD -->"
NOTES_PATTERN = re.compile(
    r"<!--\s*FORENSIC_NOTES_START\s*(.*?)\s*FORENSIC_NOTES_END\s*-->",
    re.DOTALL,
)

MONTH_NAMES_ID = {
    "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
    "05": "Mei", "06": "Jun", "07": "Jul", "08": "Agu",
    "09": "Sep", "10": "Okt", "11": "Nov", "12": "Des",
}


def clear_report_cache() -> None:
    with _REPORT_LOCK:
        _REPORT_CACHE["timestamp"] = 0.0
        _REPORT_CACHE["markdown_section"] = None
        _REPORT_CACHE["notes_hash"] = None


def _ensure_eval_columns(engine) -> None:
    """Pastikan kolom persistensi evaluasi (`eval_*`) tersedia di `candlify_signals`."""
    eng_id = id(engine)
    if eng_id in _MIGRATED_ENGINE_IDS:
        return

    dialect = engine.dialect.name
    try:
        with engine.begin() as conn:
            if dialect == "sqlite":
                cur = conn.execute(text("PRAGMA table_info(candlify_signals)")).fetchall()
                existing = {row[1] for row in cur}
                cols = [
                    ("eval_status", "TEXT"),
                    ("eval_max_gain", "REAL"),
                    ("eval_max_dd", "REAL"),
                    ("eval_p_max", "REAL"),
                    ("eval_p_min", "REAL"),
                    ("eval_p_last", "REAL"),
                    ("eval_event_day", "INTEGER DEFAULT 0"),
                    ("eval_days_elapsed", "INTEGER DEFAULT 0"),
                    ("eval_is_closed", "INTEGER DEFAULT 0"),
                ]
                for col_name, col_type in cols:
                    if col_name not in existing:
                        conn.execute(text(f"ALTER TABLE candlify_signals ADD COLUMN {col_name} {col_type}"))
            else:
                conn.execute(text("ALTER TABLE candlify_signals ADD COLUMN IF NOT EXISTS eval_status VARCHAR(24);"))
                conn.execute(text("ALTER TABLE candlify_signals ADD COLUMN IF NOT EXISTS eval_max_gain FLOAT;"))
                conn.execute(text("ALTER TABLE candlify_signals ADD COLUMN IF NOT EXISTS eval_max_dd FLOAT;"))
                conn.execute(text("ALTER TABLE candlify_signals ADD COLUMN IF NOT EXISTS eval_p_max FLOAT;"))
                conn.execute(text("ALTER TABLE candlify_signals ADD COLUMN IF NOT EXISTS eval_p_min FLOAT;"))
                conn.execute(text("ALTER TABLE candlify_signals ADD COLUMN IF NOT EXISTS eval_p_last FLOAT;"))
                conn.execute(text("ALTER TABLE candlify_signals ADD COLUMN IF NOT EXISTS eval_event_day INTEGER DEFAULT 0;"))
                conn.execute(text("ALTER TABLE candlify_signals ADD COLUMN IF NOT EXISTS eval_days_elapsed INTEGER DEFAULT 0;"))
                conn.execute(text("ALTER TABLE candlify_signals ADD COLUMN IF NOT EXISTS eval_is_closed BOOLEAN DEFAULT FALSE;"))
        _MIGRATED_ENGINE_IDS.add(eng_id)
    except Exception as e:
        logger.warning(f"Gagal migrasi kolom eval_* pada candlify_signals: {e}")


def parse_forensic_notes(markdown_text: str) -> Dict[str, str]:
    """
    Parse catatan forensik manual dari blok komentar:
    <!-- FORENSIC_NOTES_START
    2026-10-02|DKHH: Multi-bagger T+2, base kering di 69 reli 3 hari ke 127.
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


def _fmt_month_id(ym: str) -> str:
    parts = ym.split("-")
    if len(parts) != 2:
        return ym
    return f"{MONTH_NAMES_ID.get(parts[1], parts[1])} {parts[0]}"


def evaluate_all_signals_from_db() -> Dict[str, Any]:
    """
    Evaluasi sinyal historis di `candlify_signals`:
    - Sinyal yang sudah selesai (`eval_is_closed = True`) dibaca langsung tanpa query `harga_saham`.
    - Hanya sinyal yang belum selesai (`RUNNING`) yang dievaluasi terhadap `harga_saham` (T+1..T+10),
      lalu jika baru saja selesai langsung di-freeze permanen ke database.
    """
    engine = get_engine()
    if not engine:
        return {"success": False, "error": "Database tidak terhubung", "records": []}

    _ensure_eval_columns(engine)
    is_sqlite = engine.dialect.name == "sqlite"

    try:
        with engine.connect() as conn:
            sig_rows = conn.execute(
                text("""
                    SELECT
                        id, date, ticker, price, score, range_7, volume_dry_ratio,
                        top_accumulator, dominance, aar, is_pocket_pivot,
                        eval_status, eval_max_gain, eval_max_dd, eval_p_max,
                        eval_p_min, eval_p_last, eval_event_day, eval_days_elapsed,
                        eval_is_closed
                    FROM candlify_signals
                    ORDER BY date DESC, score DESC
                """)
            ).fetchall()

            if not sig_rows:
                return {
                    "success": True,
                    "latest_market_date": None,
                    "total": 0,
                    "frozen_count": 0,
                    "live_evaluated_count": 0,
                    "records": [],
                }

            latest_market_date = conn.execute(text("SELECT MAX(tanggal) FROM harga_saham")).scalar()
            latest_market_str = str(latest_market_date)[:10] if latest_market_date else None

            frozen_records: List[Dict[str, Any]] = []
            open_rows = []

            for r in sig_rows:
                p0 = float(r[3] or 0.0)
                if p0 <= 0:
                    continue

                is_closed = bool(r[19]) and bool(r[11])
                if is_closed:
                    p_last = float(r[16] if r[16] is not None else p0)
                    cur_pnl = round(((p_last - p0) / p0) * 100.0, 1)
                    frozen_records.append({
                        "date": str(r[1])[:10],
                        "ticker": str(r[2]),
                        "p0": p0,
                        "score": int(r[4] or 0),
                        "top_acc": str(r[7] or "-"),
                        "dom": float(r[8] or 0.0),
                        "aar": float(r[9] or 1.0),
                        "days_elapsed": int(r[18] or 0),
                        "p_max": float(r[14] if r[14] is not None else p0),
                        "p_min": float(r[15] if r[15] is not None else p0),
                        "p_last": p_last,
                        "max_gain": float(r[12] or 0.0),
                        "max_dd": float(r[13] or 0.0),
                        "cur_pnl": cur_pnl,
                        "status": str(r[11]),
                        "event_day": int(r[17] or 0),
                    })
                else:
                    open_rows.append(r)

            price_map: Dict[str, List[Tuple[str, float, float, float]]] = {}
            if open_rows:
                open_tickers = sorted({str(r[2]) for r in open_rows if r[2]})
                min_open_date = min(str(r[1])[:10] for r in open_rows)
                placeholders = ", ".join([f":t_{i}" for i in range(len(open_tickers))])
                params: Dict[str, Any] = {f"t_{i}": open_tickers[i] for i in range(len(open_tickers))}
                params["min_d"] = min_open_date

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

                for pr in price_rows:
                    tkr = str(pr[0])
                    price_map.setdefault(tkr, []).append(
                        (str(pr[1])[:10], float(pr[2] or 0.0), float(pr[3] or 0.0), float(pr[4] or 0.0))
                    )

        live_records: List[Dict[str, Any]] = []
        to_freeze_updates: List[Dict[str, Any]] = []

        for r in open_rows:
            row_id = int(r[0])
            sig_date = str(r[1])[:10]
            ticker = str(r[2])
            p0 = float(r[3] or 0.0)
            score = int(r[4] or 0)
            top_acc = str(r[7] or "-")
            dom = float(r[8] or 0.0)
            aar = float(r[9] or 1.0)

            bars = [b for b in price_map.get(ticker, []) if b[0] > sig_date][:10]
            days_elapsed = len(bars)

            if days_elapsed == 0:
                live_records.append({
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

            is_terminal = False
            if hit_super:
                status = "🎯 HIT (SUPER)"
                is_terminal = True
            elif hit_target:
                status = "🎯 HIT"
                is_terminal = True
            elif stopped_out:
                status = "🛑 STOP OUT"
                is_terminal = True
            elif days_elapsed < 10:
                status = "⏳ RUNNING"
            else:
                status = "⚪ EXPIRED"
                is_terminal = True

            rec = {
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
            }
            live_records.append(rec)

            if is_terminal:
                to_freeze_updates.append({
                    "id": row_id,
                    "eval_status": status,
                    "eval_max_gain": max_gain,
                    "eval_max_dd": max_dd,
                    "eval_p_max": p_max,
                    "eval_p_min": p_min,
                    "eval_p_last": p_last,
                    "eval_event_day": event_day,
                    "eval_days_elapsed": days_elapsed,
                    "eval_is_closed": 1 if is_sqlite else True,
                })

        # Persistensi (freeze) sinyal yang baru selesai dalam 1 transaksi ringan
        if to_freeze_updates:
            try:
                with engine.begin() as wconn:
                    wconn.execute(
                        text("""
                            UPDATE candlify_signals
                            SET
                                eval_status = :eval_status,
                                eval_max_gain = :eval_max_gain,
                                eval_max_dd = :eval_max_dd,
                                eval_p_max = :eval_p_max,
                                eval_p_min = :eval_p_min,
                                eval_p_last = :eval_p_last,
                                eval_event_day = :eval_event_day,
                                eval_days_elapsed = :eval_days_elapsed,
                                eval_is_closed = :eval_is_closed
                            WHERE id = :id
                        """),
                        to_freeze_updates,
                    )
            except Exception as freeze_err:
                logger.warning(f"Gagal menyimpan freeze evaluasi sinyal: {freeze_err}")

        all_records = sorted(frozen_records + live_records, key=lambda x: (x["date"], x["score"]), reverse=True)

        return {
            "success": True,
            "latest_market_date": latest_market_str,
            "total": len(all_records),
            "frozen_count": len(frozen_records),
            "live_evaluated_count": len(live_records),
            "newly_frozen_count": len(to_freeze_updates),
            "records": all_records,
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
    lines.append(f"| 🎯 **Total HIT ($\\ge +8\\%$ s/d ARA)** | **{len(hits)} sinyal** *(Avg Gain: `+{avg_hit_gain}%`)* |")
    lines.append(f"| ⏳ **Sedang Berjalan (`RUNNING` $< T+10$)** | **{len(running)} sinyal** |")
    lines.append(f"| 🛑 **Total STOP OUT ($\\le -4\\%$)** | **{len(stops)} sinyal** *(Avg DD: `{avg_stop_dd}%`)* |")
    lines.append(f"| ⚪ **EXPIRED (Datar 10 Hari)** | **{len(expired)} sinyal** |")
    lines.append(f"| 📈 **Win Rate Sinyal Selesai (Gabungan V1+V2)** | **{win_rate}%** *({len(hits)} / {len(closed)})* |")
    lines.append(f"| 🚀 **Tracking Khusus Era V2 ($\\ge$ 16 Okt 2026)** | **{len(v2_records)} sinyal** *(Win Rate: {v2_wr})* |")
    lines.append("")

    # 0. Rekap Kinerja per Bulan (Monthly Summary Table)
    monthly_groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in records:
        ym = str(r["date"])[:7]
        monthly_groups.setdefault(ym, []).append(r)

    if monthly_groups:
        lines.append("### 📅 Rekap Kinerja per Bulan")
        lines.append("")
        lines.append("| Bulan | Total | 🎯 HIT | 🛑 Stop Out | ⏳ Running | Win Rate | Avg Hit Gain |")
        lines.append("| :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
        for ym in sorted(monthly_groups.keys(), reverse=True):
            grp = monthly_groups[ym]
            m_hits = [x for x in grp if "HIT" in x["status"]]
            m_stops = [x for x in grp if "STOP" in x["status"]]
            m_run = [x for x in grp if "RUNNING" in x["status"]]
            m_closed = [x for x in grp if "RUNNING" not in x["status"]]
            m_wr = f"**{round((len(m_hits) / len(m_closed)) * 100.0, 1)}%**" if m_closed else "—"
            m_avg_gain = f"+{round(sum(x['max_gain'] for x in m_hits) / len(m_hits), 1)}%" if m_hits else "—"
            lines.append(
                f"| **{_fmt_month_id(ym)}** | {len(grp)} | {len(m_hits)} | {len(m_stops)} | {len(m_run)} | {m_wr} | {m_avg_gain} |"
            )
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
    lines.append("### 🎯 B. Histori Sinyal Berhasil (`HIT` $\\ge +8\\%$)")
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
