"""
worker/ai_analyst.py — Candlify AI Quant Analyst (Gemini 4 Neon High + Fallback Hydrogen High)
==============================================================================================
Berjalan otomatis sebagai Step 6 di worker/run.py setelah Harga, IDX Official, Broksum,
dan Pre-Breakout Scanner selesai.

Fitur Utama:
1. Completeness Gate: Hanya jalan jika 3 data harian (Harga, IDX Official, Broksum) LENGKAP.
2. Statistical Pattern Miner: Menghitung korelasi Win Rate nyata dari sinyal historis
   (Foreign Flow, Dominance, AAR, Pocket Pivot, Pasar Nego, Cuaca Makro MA20).
3. Gemini 4 Reasoning: Primary `gemini-4-neon` (thinking_level="high") + automatic fallback
   `gemini-4-hydrogen` (thinking_level="high") menghasilkan output 2-level:
   - Ringkas: `daily_brief` (3-4 poin), `post_radar_checklist` (4-5 step padat), & `signal_notes`.
   - Komprehensif: `full_report_md` (bedah makro, forensik saham, winning pattern DNA, tuning rumus).
4. Disimpan ke tabel `ai_daily_reports` di Neon DB (0 spam commit GitHub, API key hanya di worker).
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

# Pastikan root project & worker ada di sys.path agar bisa dijalankan dari root maupun folder worker/
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_THIS_DIR)
for _p in (_ROOT_DIR, _THIS_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from lib.db import get_engine
from lib.daily_insight import get_daily_foreign_insight, get_multi_broker_insight
from lib.pre_breakout_report import evaluate_all_signals_from_db, clear_report_cache

logger = logging.getLogger("candlify.ai_analyst")

PRIMARY_MODEL = os.environ.get("GEMINI_MODEL", "gemini-4-neon")
FALLBACK_MODEL = os.environ.get("GEMINI_FALLBACK_MODEL", "gemini-4-hydrogen")
THINKING_LEVEL = os.environ.get("GEMINI_THINKING_LEVEL", "high")

RESPONSE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "daily_brief": {
            "type": "array",
            "items": {"type": "string"},
            "description": "3 sampai 4 poin singkat & tajam kondisi makro bursa, foreign flow, dan sorotan sinyal Pre-Breakout hari ini."
        },
        "post_radar_checklist": {
            "type": "array",
            "items": {"type": "string"},
            "description": "4 sampai 5 langkah verifikasi ringkas & padat (Step 1..5) yang wajib dicek trader setelah saham masuk radar Pre-Breakout, belajar dari pola paling sering WIN."
        },
        "winning_patterns": {
            "type": "array",
            "items": {"type": "string"},
            "description": "3 sampai 4 temuan pola statistik paling sering WIN dan kombinasi jebakan (trap) yang paling sering STOP OUT berdasarkan data riil."
        },
        "signal_notes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Format persis YYYY-MM-DD|TICKER"},
                    "note": {"type": "string", "description": "Catatan forensik tajam 1 kalimat (maks 110 karakter)"}
                },
                "required": ["key", "note"]
            },
            "description": "Catatan forensik 1 baris untuk sinyal yang baru selesai (HIT/STOP OUT) atau sinyal baru yang patut diwaspadai."
        },
        "full_report_md": {
            "type": "string",
            "description": "Laporan analisis harian & evaluasi kinerja lengkap dan komprehensif dalam format Markdown bahasa Indonesia."
        }
    },
    "required": [
        "daily_brief",
        "post_radar_checklist",
        "winning_patterns",
        "signal_notes",
        "full_report_md"
    ]
}

SYSTEM_INSTRUCTION = """Kamu adalah Senior Quantitative Analyst & Bandarmology Specialist untuk aplikasi Candlify (Bursa Efek Indonesia / IDX).
Tugasmu adalah menganalisis data kuantitatif riil dari database Neon (OHLCV, Foreign Flow resmi BEI, Broker Summary, Pasar Nego/Crossing, Market Breadth MA20, dan histori sinyal Pre-Breakout).

ATURAN KETAT (ANTI-HALU):
1. DILARANG mengarang angka, nama saham, atau kode broker di luar data JSON yang diberikan.
2. Semua klaim Win Rate, net flow, crossing, dan harga WAJIB merujuk angka aktual di payload.
3. Gaya bahasa: Bahasa Indonesia profesional-tajam, padat, to-the-point, tanpa basa-basi.
4. Untuk `post_radar_checklist`, susun 4-5 step praktis berurutan yang langsung bisa dipakai trader setelah saham muncul di radar Pre-Breakout (memanfaatkan pola yang terbukti paling sering WIN di data statistik).
5. Untuk `signal_notes`, hanya isi untuk sinyal yang sudah selesai (HIT/STOP OUT/EXPIRED) atau sinyal hari ini yang punya anomali penting (misal Crossing Nego besar / Foreign Outflow tajam). Jangan isi catatan panjang untuk sinyal RUNNING normal.
6. Untuk `full_report_md`, susun laporan komprehensif terstruktur dengan heading Markdown (`##`):
   - `## 1. 🌐 Cuaca Makro Bursa, Foreign Flow & Peta Broker`
   - `## 2. 🎯 Bedah Sinyal Pre-Breakout Hari Ini & Evaluasi Terbaru`
   - `## 3. 🏆 Winning Pattern DNA (Pola Paling Sering WIN vs Trap)`
   - `## 4. ✅ Playbook Checklist Pasca-Radar & Saran Tuning Rumus`
"""


def ensure_ai_reports_table(engine) -> None:
    """Pastikan tabel `ai_daily_reports` sudah ada di SQLite maupun PostgreSQL."""
    dialect = engine.dialect.name
    with engine.begin() as conn:
        if dialect == "sqlite":
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ai_daily_reports (
                    report_date TEXT PRIMARY KEY,
                    model_used TEXT NOT NULL,
                    thinking_level TEXT DEFAULT 'high',
                    daily_brief_json TEXT,
                    checklist_json TEXT,
                    signal_notes_json TEXT,
                    winning_patterns_json TEXT,
                    full_report_md TEXT NOT NULL,
                    stats_snapshot_json TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
        else:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ai_daily_reports (
                    report_date DATE PRIMARY KEY,
                    model_used VARCHAR(60) NOT NULL,
                    thinking_level VARCHAR(20) DEFAULT 'high',
                    daily_brief_json TEXT,
                    checklist_json TEXT,
                    signal_notes_json TEXT,
                    winning_patterns_json TEXT,
                    full_report_md TEXT NOT NULL,
                    stats_snapshot_json TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """))


def check_day_completeness(
    engine,
    target_date: Optional[str] = None,
    min_stocks: int = 700,
    min_idx: int = 700,
    min_broksum_ratio: float = 0.85,
) -> Dict[str, Any]:
    """
    Completeness Gate: Pastikan hari bursa target sudah LENGKAP 3 sumber data
    (Harga OHLCV, IDX Official frequency/foreign, dan Broker Summary).
    """
    with engine.connect() as conn:
        if not target_date:
            max_d = conn.execute(text("SELECT MAX(tanggal) FROM harga_saham")).scalar()
            if not max_d:
                return {"ready": False, "reason": "Belum ada data di harga_saham", "date": None}
            eff_date = str(max_d)[:10]
        else:
            eff_date = str(target_date)[:10]

        row = conn.execute(
            text("""
                SELECT
                    COUNT(DISTINCT ticker) AS total_harga,
                    SUM(CASE WHEN COALESCE(volume, 0) > 0 THEN 1 ELSE 0 END) AS active_vol,
                    SUM(CASE WHEN COALESCE(frequency, 0) > 0 THEN 1 ELSE 0 END) AS idx_official
                FROM harga_saham
                WHERE tanggal = :d
            """),
            {"d": eff_date},
        ).fetchone()

        total_harga = int(row[0] or 0) if row else 0
        active_vol = int(row[1] or 0) if row else 0
        idx_official = int(row[2] or 0) if row else 0

        broksum_cnt = int(
            conn.execute(
                text("SELECT COUNT(DISTINCT ticker) FROM broker_summary WHERE date = :d"),
                {"d": eff_date},
            ).scalar()
            or 0
        )

    broksum_ratio = (broksum_cnt / active_vol) if active_vol > 0 else 0.0
    reasons = []
    if total_harga < min_stocks:
        reasons.append(f"harga_saham baru {total_harga}/{min_stocks}")
    if idx_official < min_idx:
        reasons.append(f"idx_official baru {idx_official}/{min_idx}")
    if active_vol == 0 or broksum_ratio < min_broksum_ratio:
        reasons.append(f"broksum baru {broksum_cnt}/{active_vol} ({broksum_ratio*100:.1f}% < {min_broksum_ratio*100:.0f}%)")

    return {
        "ready": len(reasons) == 0,
        "date": eff_date,
        "total_harga": total_harga,
        "active_vol": active_vol,
        "idx_official": idx_official,
        "broksum_count": broksum_cnt,
        "broksum_ratio": round(broksum_ratio * 100.0, 1),
        "reason": "; ".join(reasons) if reasons else "Lengkap (Harga + IDX + Broksum)",
    }


def report_exists_for_date(engine, report_date: str) -> bool:
    ensure_ai_reports_table(engine)
    with engine.connect() as conn:
        val = conn.execute(
            text("SELECT 1 FROM ai_daily_reports WHERE report_date = :d"),
            {"d": report_date},
        ).scalar()
        return val is not None


def _calc_bucket_wr(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not items:
        return {"count": 0, "hits": 0, "stops": 0, "win_rate": 0.0, "avg_gain": 0.0}
    hits = [x for x in items if "HIT" in x["status"]]
    stops = [x for x in items if "STOP" in x["status"]]
    return {
        "count": len(items),
        "hits": len(hits),
        "stops": len(stops),
        "win_rate": round((len(hits) / len(items)) * 100.0, 1),
        "avg_gain": round(sum(x["max_gain"] for x in hits) / len(hits), 1) if hits else 0.0,
    }


def compute_winning_pattern_stats(engine, evaluated_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Hitung korelasi statistik Win Rate nyata dari seluruh sinyal selesai (`HIT` vs `STOP OUT`)
    dikaitkan dengan Foreign Flow, Pasar Nego, Dominance, AAR, dan Skor pada hari sinyal.
    """
    closed = [r for r in evaluated_records if "RUNNING" not in r["status"]]
    if not closed:
        return {"total_closed": 0, "overall_win_rate": 0.0, "by_factor": {}}

    # Tarik metadata foreign_net & non_regular_value pada hari sinyal
    sig_dates = sorted({r["date"] for r in closed})
    sig_tickers = sorted({r["ticker"] for r in closed})

    meta_map: Dict[Tuple[str, str], Dict[str, float]] = {}
    if sig_dates and sig_tickers:
        d_ph = ", ".join([f":d_{i}" for i in range(len(sig_dates))])
        t_ph = ", ".join([f":t_{i}" for i in range(len(sig_tickers))])
        params: Dict[str, Any] = {f"d_{i}": sig_dates[i] for i in range(len(sig_dates))}
        params.update({f"t_{i}": sig_tickers[i] for i in range(len(sig_tickers))})

        with engine.connect() as conn:
            rows = conn.execute(
                text(f"""
                    SELECT
                        tanggal, ticker,
                        COALESCE(foreign_net, 0) AS f_net,
                        CAST(COALESCE(non_regular_value, 0) AS FLOAT) AS nego_val,
                        COALESCE(frequency, 0) AS freq,
                        COALESCE(volume, 0) AS vol
                    FROM harga_saham
                    WHERE tanggal IN ({d_ph}) AND ticker IN ({t_ph})
                """),
                params,
            ).fetchall()
            for row in rows:
                meta_map[(str(row[0])[:10], str(row[1]))] = {
                    "foreign_net": float(row[2] or 0.0),
                    "nego_val": float(row[3] or 0.0),
                    "freq": float(row[4] or 0.0),
                    "vol": float(row[5] or 0.0),
                }

    enriched = []
    for r in closed:
        m = meta_map.get((r["date"], r["ticker"]), {})
        item = dict(r)
        item["foreign_net"] = m.get("foreign_net", 0.0)
        item["nego_val"] = m.get("nego_val", 0.0)
        enriched.append(item)

    by_factor = {
        "score_high_gte80": _calc_bucket_wr([x for x in enriched if x["score"] >= 80]),
        "score_mid_60_79": _calc_bucket_wr([x for x in enriched if 60 <= x["score"] < 80]),
        "foreign_inflow": _calc_bucket_wr([x for x in enriched if x["foreign_net"] > 0]),
        "foreign_outflow": _calc_bucket_wr([x for x in enriched if x["foreign_net"] < 0]),
        "foreign_neutral": _calc_bucket_wr([x for x in enriched if x["foreign_net"] == 0]),
        "dominance_gte30": _calc_bucket_wr([x for x in enriched if x["dom"] >= 30.0]),
        "dominance_lt30": _calc_bucket_wr([x for x in enriched if x["dom"] < 30.0]),
        "aar_gte1_5": _calc_bucket_wr([x for x in enriched if x["aar"] >= 1.5]),
        "aar_lt1_5": _calc_bucket_wr([x for x in enriched if x["aar"] < 1.5]),
        "nego_clean": _calc_bucket_wr([x for x in enriched if x["nego_val"] < 10_000_000_000]),
        "nego_crossing_gte10b": _calc_bucket_wr([x for x in enriched if x["nego_val"] >= 10_000_000_000]),
        "era_v2_since_2026_10_16": _calc_bucket_wr([x for x in enriched if x["date"] >= "2026-10-16"]),
        "era_v1_before_2026_10_16": _calc_bucket_wr([x for x in enriched if x["date"] < "2026-10-16"]),
    }

    overall = _calc_bucket_wr(enriched)
    return {
        "total_closed": overall["count"],
        "overall_win_rate": overall["win_rate"],
        "overall_avg_hit_gain": overall["avg_gain"],
        "by_factor": by_factor,
    }


def build_daily_analysis_context(engine, target_date: str) -> Dict[str, Any]:
    """Kumpulkan seluruh fakta kuantitatif harian + korelasi statistik dari Neon DB."""
    # 1. Evaluasi & freeze seluruh sinyal terbaru
    eval_res = evaluate_all_signals_from_db()
    all_records = eval_res.get("records", [])

    # 2. Korelasi Winning Pattern DNA
    pattern_stats = compute_winning_pattern_stats(engine, all_records)

    # 3. Market-Wide Foreign Flow & Breadth hari ini
    foreign_today = get_daily_foreign_insight(target_date=target_date)
    foreign_compact = {
        "date": foreign_today.get("date"),
        "foreign_summary": foreign_today.get("foreign_summary"),
        "breadth": foreign_today.get("breadth"),
        "trend_5d": (foreign_today.get("trend_20d") or [])[-5:],
        "top_buy": (foreign_today.get("top_buy") or [])[:8],
        "top_sell": (foreign_today.get("top_sell") or [])[:8],
    }

    # 4. Multi-Broker Institutional (AK+BK+ZP+KZ) vs Retail (YP+XL+XC) hari ini
    inst_radar = get_multi_broker_insight(target_date=target_date, brokers=["AK", "BK", "ZP", "KZ"], days=1, limit=6)
    retail_radar = get_multi_broker_insight(target_date=target_date, brokers=["YP", "XL", "XC"], days=1, limit=6)

    # 5. Sinyal hari ini, sinyal RUNNING terbaru, dan sinyal selesai terbaru (HIT / STOP OUT)
    today_signals = [r for r in all_records if r["date"] == target_date]
    running_signals = [r for r in all_records if "RUNNING" in r["status"]][:15]
    recent_hits = [r for r in all_records if "HIT" in r["status"]][:10]
    recent_stops = [r for r in all_records if "STOP" in r["status"]][:10]

    # Enrich sinyal hari ini & running dengan data Foreign Flow & Pasar Nego hari target_date
    focus_tickers = sorted({r["ticker"] for r in (today_signals + running_signals[:8])})
    focus_intel: Dict[str, Dict[str, Any]] = {}
    if focus_tickers:
        t_ph = ", ".join([f":ft_{i}" for i in range(len(focus_tickers))])
        params = {f"ft_{i}": focus_tickers[i] for i in range(len(focus_tickers))}
        params["d"] = target_date
        with engine.connect() as conn:
            rows = conn.execute(
                text(f"""
                    SELECT ticker, close, volume, value, frequency, foreign_net, non_regular_value
                    FROM harga_saham
                    WHERE tanggal = :d AND ticker IN ({t_ph})
                """),
                params,
            ).fetchall()
            for r in rows:
                vol = int(r[2] or 0)
                freq = int(r[4] or 0)
                lpt = round((vol / 100.0) / freq, 1) if freq > 0 else 0.0
                focus_intel[str(r[0])] = {
                    "close": float(r[1] or 0.0),
                    "value_b": round(float(r[3] or 0.0) / 1e9, 2),
                    "lot_per_trade": lpt,
                    "foreign_net_shares": int(r[5] or 0),
                    "nego_value_b": round(float(r[6] or 0.0) / 1e9, 2),
                }

    return {
        "report_date": target_date,
        "market_foreign_and_breadth": foreign_compact,
        "institutional_brokers_AK_BK_ZP_KZ": {
            "summary": inst_radar.get("summary"),
            "top_buy": inst_radar.get("top_buy", []),
            "top_sell": inst_radar.get("top_sell", []),
        },
        "retail_brokers_YP_XL_XC": {
            "summary": retail_radar.get("summary"),
            "top_buy": retail_radar.get("top_buy", []),
            "top_sell": retail_radar.get("top_sell", []),
        },
        "pre_breakout_summary": {
            "total_signals_all_time": len(all_records),
            "today_signals": today_signals,
            "running_signals_sample": running_signals,
            "recent_hits": recent_hits,
            "recent_stops": recent_stops,
            "focus_stock_market_intel": focus_intel,
        },
        "winning_pattern_correlations": pattern_stats,
    }


def _extract_json_from_text(raw_text: str) -> Dict[str, Any]:
    txt = (raw_text or "").strip()
    if txt.startswith("```"):
        txt = txt.split("\n", 1)[-1]
        if txt.endswith("```"):
            txt = txt.rsplit("```", 1)[0]
    return json.loads(txt.strip())


def call_gemini_analyst(
    context_payload: Dict[str, Any],
    api_key: Optional[str] = None,
    primary_model: Optional[str] = None,
    fallback_model: Optional[str] = None,
    thinking_level: Optional[str] = None,
) -> Tuple[Dict[str, Any], str]:
    """
    Panggil Gemini Interactions API (`google-genai`) dengan Primary `gemini-4-neon` (high)
    dan automatic fallback ke `gemini-4-hydrogen` (high).
    """
    key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY tidak ditemukan di environment variables.")

    from google import genai

    p_model = primary_model or PRIMARY_MODEL
    f_model = fallback_model or FALLBACK_MODEL
    t_level = thinking_level or THINKING_LEVEL

    models_to_try = [p_model]
    if f_model and f_model != p_model:
        models_to_try.append(f_model)

    prompt_text = (
        f"Analisis data pasar BEI & kinerja Pre-Breakout untuk tanggal {context_payload['report_date']} berikut. "
        "Keluarkan HANYA JSON valid sesuai schema.\n\n"
        f"DATA_JSON:\n{json.dumps(context_payload, ensure_ascii=False, default=str)}"
    )

    client = genai.Client(api_key=key)
    last_err: Optional[Exception] = None

    for model_name in models_to_try:
        try:
            logger.info(f"🤖 Memanggil Gemini API ({model_name}, thinking_level={t_level})...")
            interaction = client.interactions.create(
                model=model_name,
                input=prompt_text,
                system_instruction=SYSTEM_INSTRUCTION,
                generation_config={
                    "thinking_level": t_level,
                    "temperature": 0.25,
                },
                response_mime_type="application/json",
                response_format=RESPONSE_SCHEMA,
                store=False,
            )
            out_text = interaction.output_text
            if not out_text:
                raise RuntimeError(f"Output kosong dari model {model_name}")
            parsed = _extract_json_from_text(out_text)
            logger.info(f"✅ Analisa Gemini berhasil via {model_name}.")
            return parsed, model_name
        except Exception as err:
            logger.warning(f"⚠️ Model {model_name} gagal ({err}), mencoba fallback jika tersedia...")
            last_err = err

    raise RuntimeError(f"Semua model Gemini gagal: {last_err}")


def save_ai_daily_report(
    engine,
    report_date: str,
    model_used: str,
    parsed_json: Dict[str, Any],
    stats_snapshot: Dict[str, Any],
    thinking_level: str = THINKING_LEVEL,
) -> None:
    """Simpan hasil analisa AI harian ke tabel `ai_daily_reports` (idempotent UPSERT)."""
    ensure_ai_reports_table(engine)
    dialect = engine.dialect.name

    # Normalisasi signal_notes ke dict {YYYY-MM-DD|TICKER: note}
    notes_dict: Dict[str, str] = {}
    raw_notes = parsed_json.get("signal_notes") or []
    if isinstance(raw_notes, dict):
        notes_dict = {str(k).upper().strip(): str(v).strip() for k, v in raw_notes.items() if k and v}
    elif isinstance(raw_notes, list):
        for item in raw_notes:
            if isinstance(item, dict) and item.get("key") and item.get("note"):
                notes_dict[str(item["key"]).upper().strip()] = str(item["note"]).strip()

    params = {
        "report_date": report_date,
        "model_used": model_used,
        "thinking_level": thinking_level,
        "daily_brief_json": json.dumps(parsed_json.get("daily_brief") or [], ensure_ascii=False),
        "checklist_json": json.dumps(parsed_json.get("post_radar_checklist") or [], ensure_ascii=False),
        "signal_notes_json": json.dumps(notes_dict, ensure_ascii=False),
        "winning_patterns_json": json.dumps(parsed_json.get("winning_patterns") or [], ensure_ascii=False),
        "full_report_md": str(parsed_json.get("full_report_md") or "").strip(),
        "stats_snapshot_json": json.dumps(stats_snapshot or {}, ensure_ascii=False, default=str),
    }

    with engine.begin() as conn:
        if dialect == "sqlite":
            conn.execute(text("""
                INSERT OR REPLACE INTO ai_daily_reports (
                    report_date, model_used, thinking_level,
                    daily_brief_json, checklist_json, signal_notes_json,
                    winning_patterns_json, full_report_md, stats_snapshot_json
                ) VALUES (
                    :report_date, :model_used, :thinking_level,
                    :daily_brief_json, :checklist_json, :signal_notes_json,
                    :winning_patterns_json, :full_report_md, :stats_snapshot_json
                )
            """), params)
        else:
            conn.execute(text("""
                INSERT INTO ai_daily_reports (
                    report_date, model_used, thinking_level,
                    daily_brief_json, checklist_json, signal_notes_json,
                    winning_patterns_json, full_report_md, stats_snapshot_json
                ) VALUES (
                    :report_date, :model_used, :thinking_level,
                    :daily_brief_json, :checklist_json, :signal_notes_json,
                    :winning_patterns_json, :full_report_md, :stats_snapshot_json
                )
                ON CONFLICT (report_date) DO UPDATE SET
                    model_used = EXCLUDED.model_used,
                    thinking_level = EXCLUDED.thinking_level,
                    daily_brief_json = EXCLUDED.daily_brief_json,
                    checklist_json = EXCLUDED.checklist_json,
                    signal_notes_json = EXCLUDED.signal_notes_json,
                    winning_patterns_json = EXCLUDED.winning_patterns_json,
                    full_report_md = EXCLUDED.full_report_md,
                    stats_snapshot_json = EXCLUDED.stats_snapshot_json,
                    created_at = NOW()
            """), params)

    clear_report_cache()


def run_ai_analyst(
    target_date: Optional[str] = None,
    force: bool = False,
    api_key: Optional[str] = None,
    min_stocks: int = 700,
    min_idx: int = 700,
    min_broksum_ratio: float = 0.85,
) -> Dict[str, Any]:
    """
    Entry point utama Step 6 worker/run.py (atau dijalankan manual via CLI).
    """
    key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        logger.warning("⚠️ GEMINI_API_KEY belum diset. AI Daily Analyst dilewati dengan aman.")
        return {"status": "skipped", "reason": "GEMINI_API_KEY tidak tersedia"}

    engine = get_engine()
    if not engine:
        return {"status": "error", "reason": "Database tidak terhubung"}

    ensure_ai_reports_table(engine)

    # 1. Completeness Gate
    gate = check_day_completeness(
        engine,
        target_date=target_date,
        min_stocks=min_stocks,
        min_idx=min_idx,
        min_broksum_ratio=min_broksum_ratio,
    )
    eff_date = gate.get("date")
    if not gate.get("ready") and not force:
        logger.info(f"⏭️ AI Analyst ditunda untuk {eff_date}: data belum lengkap ({gate.get('reason')}).")
        return {"status": "skipped_incomplete", "date": eff_date, "gate": gate}

    # 2. Idempotency Check
    if eff_date and report_exists_for_date(engine, eff_date) and not force:
        logger.info(f"✅ Laporan AI untuk {eff_date} sudah tersedia di DB (skip untuk hemat kuota).")
        return {"status": "already_exists", "date": eff_date}

    # 3. Kumpulkan Konteks & Panggil Gemini 4
    logger.info(f"🧠 Menyusun paket data kuantitatif & korelasi untuk {eff_date}...")
    context_payload = build_daily_analysis_context(engine, eff_date)
    parsed_json, model_used = call_gemini_analyst(context_payload, api_key=key)

    # 4. Simpan ke Neon DB
    save_ai_daily_report(
        engine=engine,
        report_date=eff_date,
        model_used=model_used,
        parsed_json=parsed_json,
        stats_snapshot=context_payload.get("winning_pattern_correlations", {}),
    )
    logger.info(f"💾 Laporan AI harian {eff_date} berhasil disimpan via {model_used}!")

    return {
        "status": "success",
        "date": eff_date,
        "model_used": model_used,
        "brief_count": len(parsed_json.get("daily_brief") or []),
        "checklist_count": len(parsed_json.get("post_radar_checklist") or []),
        "full_report_chars": len(parsed_json.get("full_report_md") or ""),
    }


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(description="Candlify AI Daily Quant Analyst")
    parser.add_argument("--date", type=str, default=None, help="Tanggal target (YYYY-MM-DD)")
    parser.add_argument("--force", action="store_true", help="Paksa re-generate walau sudah ada / data parsial")
    args = parser.parse_args()

    res = run_ai_analyst(target_date=args.date, force=args.force)
    print(json.dumps(res, indent=2, ensure_ascii=False))
