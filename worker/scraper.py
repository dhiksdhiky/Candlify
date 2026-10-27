"""
scraper.py — Stockbit Exodus Broker Summary Scraper
====================================================
Mengambil data Broker Summary harian per emiten dari API resmi Stockbit
(exodus.stockbit.com/marketdetectors/{TICKER}) dengan manajemen sesi JWT
otomatis (auto-refresh token & sinkronisasi ke database PostgreSQL).

Keamanan & Perlindungan Akun:
  - Read-Only Market Data: Hanya mengakses endpoint marketdetectors (terpisah dari PIN Trading).
  - Zero Repeated Login: Menggunakan Bearer JWT + rotasi otomatis via /login/refresh.
  - Circuit Breaker:
      * HTTP 429 Too Many Requests → SoftBlockError (cooldown 10 menit).
      * HTTP 401/403 (dan refresh gagal) → AuthExpiredError (langsung hentikan batch, anti-lockout).
      * Data kosong valid (HTTP 200) → EmptyBrokerDataError (catat gap, tidak memicu outage palsu).
"""

import base64
import json
import logging
import os
import re
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from db_config import (
    SessionLocal,
    get_dialect,
    get_auth_session,
    save_auth_session,
)
from models import BrokerSummary

logger = logging.getLogger("Scraper")


class SoftBlockError(Exception):
    """Dipicu saat API mengembalikan HTTP 429 rate-limiting."""
    pass


class AuthExpiredError(Exception):
    """Dipicu saat access_token dan refresh_token Stockbit ditolak/kedaluwarsa (HTTP 401/403)."""
    pass


class EmptyBrokerDataError(Exception):
    """Dipicu saat API merespons HTTP 200 valid tetapi emiten tidak memiliki transaksi broker pada tanggal tsb."""
    pass


def _decode_jwt_exp(token: str) -> int:
    """Ekstrak klaim exp (unix timestamp) dari JWT tanpa verifikasi signature."""
    if not token or "." not in token:
        return 0
    try:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload_b64))
        return int(claims.get("exp") or 0)
    except Exception:
        return 0


class BroksumScraper:
    def __init__(self):
        self.api_base = "https://exodus.stockbit.com/marketdetectors"
        self.refresh_url = "https://exodus.stockbit.com/login/refresh"
        self.ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )
        self.local_token_path = os.path.join(
            os.path.expanduser("~"), ".stockbit_tokens.json"
        )

        self.access_token = ""
        self.refresh_token = ""
        self.access_exp = 0
        self.refresh_exp = 0

        # Retry strategy khusus error jaringan / 5xx transien (BUKAN 401/403/429)
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET"],
            backoff_factor=2,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self._load_tokens()

    # ── Manajemen Sesi & Token JWT ──────────────────────────────

    def _load_tokens(self):
        """
        Muat token Stockbit dari beberapa sumber (DB auth_sessions, file lokal, env vars)
        dan pilih kandidat dengan masa berlaku paling baru.
        """
        candidates = []

        # 1. Database auth_sessions
        db_sess = get_auth_session("stockbit")
        if db_sess and (db_sess.get("access_token") or db_sess.get("refresh_token")):
            acc = db_sess.get("access_token", "").strip()
            ref = db_sess.get("refresh_token", "").strip()
            acc_exp = int(db_sess.get("access_exp") or _decode_jwt_exp(acc))
            ref_exp = int(db_sess.get("refresh_exp") or _decode_jwt_exp(ref))
            candidates.append({
                "source": "db",
                "access_token": acc,
                "refresh_token": ref,
                "user_agent": db_sess.get("user_agent") or self.ua,
                "access_exp": acc_exp,
                "refresh_exp": ref_exp,
            })

        # 2. File lokal ~/.stockbit_tokens.json
        if os.path.exists(self.local_token_path):
            try:
                with open(self.local_token_path, "r", encoding="utf-8") as f:
                    local_data = json.load(f)
                acc = (local_data.get("access_token") or "").strip()
                ref = (local_data.get("refresh_token") or "").strip()
                if acc or ref:
                    acc_exp = int(local_data.get("access_exp") or _decode_jwt_exp(acc))
                    ref_exp = int(local_data.get("refresh_exp") or _decode_jwt_exp(ref))
                    candidates.append({
                        "source": "local_file",
                        "access_token": acc,
                        "refresh_token": ref,
                        "user_agent": local_data.get("user_agent") or self.ua,
                        "access_exp": acc_exp,
                        "refresh_exp": ref_exp,
                    })
            except Exception as e:
                logger.warning(f"⚠️ Gagal membaca {self.local_token_path}: {e}")

        # 3. Environment variables fallback
        env_acc = os.environ.get("STOCKBIT_ACCESS_TOKEN", "").strip()
        env_ref = os.environ.get("STOCKBIT_REFRESH_TOKEN", "").strip()
        if env_acc or env_ref:
            candidates.append({
                "source": "env",
                "access_token": env_acc,
                "refresh_token": env_ref,
                "user_agent": self.ua,
                "access_exp": _decode_jwt_exp(env_acc),
                "refresh_exp": _decode_jwt_exp(env_ref),
            })

        if not candidates:
            logger.warning("⚠️ Belum ada token Stockbit di DB maupun file lokal.")
            return

        # Pilih kandidat dengan refresh_exp & access_exp paling baru
        best = max(candidates, key=lambda c: (c["refresh_exp"], c["access_exp"]))
        self.access_token = best["access_token"]
        self.refresh_token = best["refresh_token"]
        self.access_exp = best["access_exp"]
        self.refresh_exp = best["refresh_exp"]
        if best.get("user_agent"):
            self.ua = best["user_agent"]

        # Jika kandidat terbaik bukan dari DB, sinkronkan ke DB
        if best["source"] != "db":
            save_auth_session(
                provider="stockbit",
                access_token=self.access_token,
                refresh_token=self.refresh_token,
                user_agent=self.ua,
                access_exp=self.access_exp,
                refresh_exp=self.refresh_exp,
            )

    def _persist_tokens(self, access_token: str, refresh_token: str):
        """Simpan pasangan token baru ke DB dan file lokal secara atomik."""
        self.access_token = (access_token or "").strip()
        if refresh_token:
            self.refresh_token = refresh_token.strip()
        self.access_exp = _decode_jwt_exp(self.access_token)
        self.refresh_exp = _decode_jwt_exp(self.refresh_token)

        # 1. Simpan ke DB (utama untuk lintas lokal & GitHub Actions)
        save_auth_session(
            provider="stockbit",
            access_token=self.access_token,
            refresh_token=self.refresh_token,
            user_agent=self.ua,
            access_exp=self.access_exp,
            refresh_exp=self.refresh_exp,
        )

        # 2. Simpan ke file lokal (cadangan)
        try:
            tmp_path = f"{self.local_token_path}.{os.getpid()}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "access_token": self.access_token,
                        "access_exp": self.access_exp,
                        "refresh_token": self.refresh_token,
                        "refresh_exp": self.refresh_exp,
                        "user_agent": self.ua,
                        "updated_at": time.time(),
                    },
                    f,
                    indent=2,
                )
            os.replace(tmp_path, self.local_token_path)
        except Exception:
            pass

    def _refresh_access_token(self):
        """
        Perbarui access_token dan refresh_token via POST https://exodus.stockbit.com/login/refresh.
        Penting: Stockbit merotasi refresh_token setiap kali endpoint ini dipanggil.
        """
        if not self.refresh_token:
            raise AuthExpiredError(
                "Tidak ada refresh_token Stockbit yang tersedia untuk memperbarui sesi."
            )

        logger.info("🔄 Memperbarui sesi token Stockbit via /login/refresh...")
        headers = {
            "Authorization": f"Bearer {self.refresh_token}",
            "User-Agent": self.ua,
            "Origin": "https://stockbit.com",
            "Referer": "https://stockbit.com/",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        try:
            resp = requests.post(self.refresh_url, headers=headers, timeout=15)
        except requests.RequestException as e:
            raise ConnectionError(f"Gagal menghubungi endpoint refresh Stockbit: {e}")

        if resp.status_code == 200:
            body = resp.json().get("data") or {}
            new_access = (body.get("access") or {}).get("token") or ""
            new_refresh = (body.get("refresh") or {}).get("token") or self.refresh_token
            if not new_access:
                raise AuthExpiredError("Respons /login/refresh 200 tetapi token kosong.")
            self._persist_tokens(new_access, new_refresh)
            logger.info("✅ Token Stockbit berhasil diperbarui & disimpan ke database.")
            return

        if resp.status_code in (401, 403):
            raise AuthExpiredError(
                f"Refresh token Stockbit ditolak/kedaluwarsa (HTTP {resp.status_code})."
            )

        raise ConnectionError(
            f"Gagal refresh token Stockbit (HTTP {resp.status_code}): {resp.text[:200]}"
        )

    def _ensure_valid_token(self):
        """Pastikan access_token masih aktif (> 1 jam sebelum exp), atau perbarui otomatis."""
        now = int(time.time())
        if not self.access_token and not self.refresh_token:
            self._load_tokens()

        if not self.access_token and not self.refresh_token:
            raise AuthExpiredError("Token Stockbit belum dikonfigurasi di database.")

        # Refresh proaktif jika access_token kosong atau sisa waktu < 1 jam (3600s)
        if not self.access_token or (self.access_exp > 0 and now >= self.access_exp - 3600):
            self._refresh_access_token()

    # ── Helper Parsing & Upsert ─────────────────────────────────

    def _convert_to_float(self, value_str: str) -> float:
        """Parse angka dengan suffix K/M/B/T atau notasi ilmiah menjadi float."""
        if value_str is None:
            return 0.0
        if isinstance(value_str, (int, float)):
            return float(value_str)
        clean = str(value_str).strip().upper()
        if not clean or clean in ("", "-"):
            return 0.0

        # Jika notasi ilmiah standar (contoh "2.12629637E+11") atau float murni
        try:
            return float(clean)
        except ValueError:
            pass

        clean = clean.replace(",", ".")
        try:
            multipliers = {"T": 1e12, "B": 1e9, "M": 1e6, "K": 1e3}
            for suffix, mult in multipliers.items():
                if suffix in clean:
                    return float(clean.replace(suffix, "")) * mult
            clean = clean.replace(".", "")
            return float(clean)
        except ValueError:
            return 0.0

    def _clean_broker_code(self, code: str) -> str | None:
        """Bersihkan kode broker menjadi 2 huruf uppercase."""
        if not code:
            return None
        clean = re.sub(r"[^A-Z]", "", str(code).strip().upper())
        return clean[:2] if len(clean) >= 2 else None

    def _do_upsert(self, db, data_to_insert: list):
        """Dialect-aware upsert untuk broker_summary."""
        if not data_to_insert:
            return

        dialect = get_dialect()
        if dialect == "sqlite":
            from sqlalchemy.dialects.sqlite import insert as dialect_insert
        else:
            from sqlalchemy.dialects.postgresql import insert as dialect_insert

        stmt = dialect_insert(BrokerSummary).values(data_to_insert)
        stmt = stmt.on_conflict_do_update(
            index_elements=["ticker", "date", "broker_code"],
            set_={
                "buy_vol": stmt.excluded.buy_vol,
                "buy_val": stmt.excluded.buy_val,
                "buy_avg": stmt.excluded.buy_avg,
                "sell_vol": stmt.excluded.sell_vol,
                "sell_val": stmt.excluded.sell_val,
                "sell_avg": stmt.excluded.sell_avg,
                "net_vol": stmt.excluded.net_vol,
                "net_val": stmt.excluded.net_val,
            },
        )
        db.execute(stmt)
        db.commit()

    # ── Fetch Market Detector API ───────────────────────────────

    def _fetch_market_detector(self, ticker: str, date_str: str, board: str) -> dict:
        """Panggil endpoint marketdetectors Stockbit untuk 1 emiten & 1 tanggal."""
        self._ensure_valid_token()

        url = f"{self.api_base}/{ticker}"
        params = {
            "transaction_type": "TRANSACTION_TYPE_GROSS",
            "market_board": board,
            "investor_type": "INVESTOR_TYPE_ALL",
            "limit": 100,
            "from": date_str,
            "to": date_str,
        }

        for attempt in range(2):
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "User-Agent": self.ua,
                "Origin": "https://stockbit.com",
                "Referer": "https://stockbit.com/",
                "Accept": "application/json",
            }
            resp = self.session.get(url, params=params, headers=headers, timeout=(5, 15))

            if resp.status_code == 200:
                return resp.json()

            if resp.status_code == 401 and attempt == 0:
                # Token mungkin baru saja di-rotasi oleh proses lain; coba muat ulang dari DB lalu refresh
                self._load_tokens()
                self._refresh_access_token()
                continue

            if resp.status_code in (401, 403):
                raise AuthExpiredError(
                    f"Akses marketdetectors ditolak (HTTP {resp.status_code}) untuk {ticker}."
                )

            if resp.status_code == 429:
                raise SoftBlockError(
                    f"Rate-limited oleh Stockbit (HTTP 429) saat mengambil {ticker}."
                )

            resp.raise_for_status()

        raise Exception(f"Gagal mengambil data marketdetectors untuk {ticker}.")

    def fetch_and_save(self, ticker: str, date_obj):
        """
        Ambil Broker Summary (Gross Buy & Gross Sell) untuk 1 ticker + 1 tanggal dari Stockbit,
        hitung net_vol & net_val per broker, lalu upsert ke tabel broker_summary.

        Raises:
            SoftBlockError: jika terkena HTTP 429 rate-limit
            AuthExpiredError: jika token autentikasi kedaluwarsa & gagal di-refresh
            EmptyBrokerDataError: jika API 200 OK tetapi tidak ada transaksi broker
        """
        db = SessionLocal()
        ticker_clean = ticker.upper().strip()
        date_str = date_obj.strftime("%Y-%m-%d")

        try:
            payload = self._fetch_market_detector(
                ticker_clean, date_str, board="MARKET_BOARD_REGULER"
            )
            bs = (payload.get("data") or {}).get("broker_summary") or {}
            buyers = bs.get("brokers_buy") or []
            sellers = bs.get("brokers_sell") or []

            # Fallback ke MARKET_BOARD_ALL jika emiten hanya bertransaksi di pasar Nego/Tunai
            if not buyers and not sellers:
                payload_all = self._fetch_market_detector(
                    ticker_clean, date_str, board="MARKET_BOARD_ALL"
                )
                bs_all = (payload_all.get("data") or {}).get("broker_summary") or {}
                buyers = bs_all.get("brokers_buy") or []
                sellers = bs_all.get("brokers_sell") or []

            if not buyers and not sellers:
                raise EmptyBrokerDataError(
                    f"Tidak ada data transaksi broker untuk {ticker_clean} pada {date_str}"
                )

            broker_map = {}

            for item in buyers:
                b_code = self._clean_broker_code(item.get("netbs_broker_code"))
                if not b_code:
                    continue
                if b_code not in broker_map:
                    broker_map[b_code] = {
                        "buy_lot": 0.0,
                        "buy_val": 0.0,
                        "buy_avg": 0.0,
                        "sell_lot": 0.0,
                        "sell_val": 0.0,
                        "sell_avg": 0.0,
                    }
                b_lot = abs(self._convert_to_float(item.get("blot", 0)))
                b_val = abs(self._convert_to_float(item.get("bval", 0)))
                b_avg = abs(self._convert_to_float(item.get("netbs_buy_avg_price", 0)))
                broker_map[b_code]["buy_lot"] += b_lot
                broker_map[b_code]["buy_val"] += b_val
                if b_avg > 0:
                    broker_map[b_code]["buy_avg"] = b_avg

            for item in sellers:
                s_code = self._clean_broker_code(item.get("netbs_broker_code"))
                if not s_code:
                    continue
                if s_code not in broker_map:
                    broker_map[s_code] = {
                        "buy_lot": 0.0,
                        "buy_val": 0.0,
                        "buy_avg": 0.0,
                        "sell_lot": 0.0,
                        "sell_val": 0.0,
                        "sell_avg": 0.0,
                    }
                s_lot = abs(self._convert_to_float(item.get("slot", 0)))
                s_val = abs(self._convert_to_float(item.get("sval", 0)))
                s_avg = abs(self._convert_to_float(item.get("netbs_sell_avg_price", 0)))
                broker_map[s_code]["sell_lot"] += s_lot
                broker_map[s_code]["sell_val"] += s_val
                if s_avg > 0:
                    broker_map[s_code]["sell_avg"] = s_avg

            data_to_insert = []
            for code, vals in broker_map.items():
                b_lot = int(round(vals["buy_lot"]))
                b_val = float(round(vals["buy_val"], 2))
                s_lot = int(round(vals["sell_lot"]))
                s_val = float(round(vals["sell_val"], 2))

                buy_avg = (
                    vals["buy_avg"]
                    if vals["buy_avg"] > 0
                    else ((b_val / (b_lot * 100.0)) if b_lot > 0 else 0.0)
                )
                sell_avg = (
                    vals["sell_avg"]
                    if vals["sell_avg"] > 0
                    else ((s_val / (s_lot * 100.0)) if s_lot > 0 else 0.0)
                )

                data_to_insert.append(
                    {
                        "ticker": ticker_clean,
                        "date": date_obj,
                        "broker_code": code,
                        "buy_vol": b_lot,
                        "buy_val": b_val,
                        "buy_avg": float(buy_avg),
                        "sell_vol": s_lot,
                        "sell_val": s_val,
                        "sell_avg": float(sell_avg),
                        "net_vol": b_lot - s_lot,
                        "net_val": b_val - s_val,
                    }
                )

            if data_to_insert:
                self._do_upsert(db, data_to_insert)
                logger.info(
                    f"✅ [{ticker_clean}] {date_obj} → {len(data_to_insert)} broker records saved."
                )

        except (SoftBlockError, AuthExpiredError, EmptyBrokerDataError):
            db.rollback()
            raise
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
