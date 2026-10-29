"""
worker/downloader_idx.py — IDX Stock List & Board Extraction Engine
===================================================================
Mengambil daftar emiten resmi dari Bursa Efek Indonesia (IDX) beserta
papan pencatatan (Utama, Pengembangan, Pemantauan Khusus/FCA, Akselerasi).

Menggunakan impersonation TLS/JA3 (curl_cffi) untuk melewati proteksi Cloudflare.
Strategi ganda:
1. DirectApiExtractor: Mengambil langsung dari endpoint API internal IDX.
2. NuxtSsrDecompilerExtractor: Fallback dekompilasi state window.__NUXT__ dari HTML SSR.
"""

from __future__ import annotations

import json
import logging
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

from curl_cffi import requests as cf_requests

logger = logging.getLogger("IDXDownloader")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )


@dataclass(frozen=True)
class StockRecord:
    code: str
    name: str
    listing_date: str
    shares: int
    listing_board: str
    sector: str = "Data tidak tersedia"
    no: int = 0

    @classmethod
    def from_raw(cls, raw: Dict[str, Any], index: int = 0) -> StockRecord:
        code = str(raw.get("Code", "")).strip().upper()
        if not re.match(r"^[A-Z0-9]{4,6}$", code):
            raise ValueError(f"Kode saham tidak valid: {code!r}")

        name = str(raw.get("Name", "")).strip()
        listing_date = str(raw.get("ListingDate", "")).strip().split("T")[0]

        raw_shares = raw.get("Shares", 0)
        try:
            shares = int(float(raw_shares))
        except (ValueError, TypeError):
            shares = 0

        board = str(raw.get("ListingBoard", "")).strip() or "Pengembangan"
        sector = str(raw.get("Sector", "Data tidak tersedia")).strip() or "Data tidak tersedia"
        
        raw_no = raw.get("No", index + 1)
        try:
            no = int(raw_no)
        except (ValueError, TypeError):
            no = index + 1

        return cls(
            code=code,
            name=name,
            listing_date=listing_date,
            shares=shares,
            listing_board=board,
            sector=sector,
            no=no
        )


class ExtractionStrategy(ABC):
    @abstractmethod
    def extract(self) -> List[StockRecord]:
        """Ekstraksi daftar saham menjadi list StockRecord."""


class DirectApiExtractor(ExtractionStrategy):
    """
    Strategi Utama: Mengambil JSON langsung dari endpoint internal IDX
    menggunakan TLS impersonation Chrome124.
    """
    BASE_URL = "https://www.idx.co.id/primary/StockData/GetSecuritiesStock"

    def __init__(
        self,
        sector: str = "",
        board: str = "",
        impersonate: str = "chrome131",
        timeout: int = 20,
    ) -> None:
        self.sector = sector.strip()
        self.board = board.strip()
        self.impersonate = impersonate
        self.timeout = timeout

    def extract(self) -> List[StockRecord]:
        params = {
            "start": 0,
            "length": 9999,
            "code": "",
            "sector": self.sector,
            "board": self.board,
            "language": "id-id",
        }
        url = f"{self.BASE_URL}?{urlencode(params)}"
        referer_url = "https://www.idx.co.id/id/data-pasar/data-saham/daftar-saham"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Referer": referer_url,
        }

        proxy_url = os.getenv("IDX_PROXY_URL", "").strip() or None
        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
        proxy_candidates = [proxies, None] if proxies else [None]

        profiles = [self.impersonate, "chrome131", "chrome124", "safari180", "safari184", "firefox133", "chrome120"]
        seen_p = set()
        ordered_profiles = [p for p in profiles if not (p in seen_p or seen_p.add(p))]

        payload: Optional[Dict[str, Any]] = None
        last_err: Optional[Exception] = None

        logger.info("📡 Mengakses endpoint API internal IDX (%s)...", self.BASE_URL)
        for p_cfg in proxy_candidates:
            for prof in ordered_profiles:
                try:
                    mode_lbl = f"{prof}+proxy" if p_cfg else prof
                    logger.debug("📡 Mencoba profil %s: %s", mode_lbl, url)
                    response = cf_requests.get(
                        url,
                        headers=headers,
                        impersonate=prof,
                        proxies=p_cfg,
                        timeout=self.timeout,
                    )
                    if response.status_code == 403:
                        logger.debug("🔄 HTTP 403 pada DirectApiExtractor (%s), mencoba Session Cookie Warm-up...", mode_lbl)
                        with cf_requests.Session(impersonate=prof, proxies=p_cfg) as s:
                            s.get(referer_url, timeout=self.timeout)
                            response = s.get(url, headers=headers, timeout=self.timeout)

                    if response.status_code == 200:
                        payload = response.json()
                        break
                    last_err = RuntimeError(f"HTTP {response.status_code} saat mengakses API IDX (impersonate={mode_lbl}).")
                except Exception as exc:
                    last_err = exc
                    if p_cfg is not None and ("Connection refused" in str(exc) or "Failed to connect" in str(exc) or "(7)" in str(exc)):
                        break
            if payload is not None:
                break

        if payload is None:
            if last_err:
                raise last_err
            raise RuntimeError("Gagal mengakses API IDX setelah mencoba semua profil TLS.")

        raw_rows = payload.get("data", [])
        if not isinstance(raw_rows, list) or not raw_rows:
            raise ValueError("Payload API kosong atau format data berubah.")

        records: List[StockRecord] = []
        for i, row in enumerate(raw_rows):
            try:
                records.append(StockRecord.from_raw(row, index=i))
            except ValueError as err:
                logger.warning("Melewati baris tidak valid: %s", err)

        logger.info("✅ Berhasil mengekstrak %d emiten via DirectApiExtractor.", len(records))
        return records


class NuxtSsrDecompilerExtractor(ExtractionStrategy):
    """
    Strategi Fallback: Mendekompilasi payload window.__NUXT__ dari HTML SSR.
    """
    PAGE_URL = "https://www.idx.co.id/id/data-pasar/data-saham/daftar-saham"

    def __init__(
        self,
        html_source: Optional[str] = None,
        impersonate: str = "chrome131",
        timeout: int = 20,
    ) -> None:
        self.html_source = html_source
        self.impersonate = impersonate
        self.timeout = timeout

    def _fetch_html(self) -> str:
        if self.html_source:
            return self.html_source

        proxy_url = os.getenv("IDX_PROXY_URL", "").strip() or None
        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
        proxy_candidates = [proxies, None] if proxies else [None]
        profiles = [self.impersonate, "chrome131", "chrome124", "safari180", "safari184", "firefox133"]
        seen_p = set()
        ordered_profiles = [p for p in profiles if not (p in seen_p or seen_p.add(p))]

        last_status = 0
        logger.info("📥 Mengunduh HTML SSR dari: %s", self.PAGE_URL)
        for p_cfg in proxy_candidates:
            for prof in ordered_profiles:
                try:
                    logger.debug("📥 Mencoba HTML SSR (impersonate=%s): %s", prof, self.PAGE_URL)
                    response = cf_requests.get(
                        self.PAGE_URL,
                        impersonate=prof,
                        proxies=p_cfg,
                        timeout=self.timeout,
                    )
                    if response.status_code == 200:
                        return response.text
                    last_status = response.status_code
                except Exception as exc:
                    if p_cfg is not None and ("Connection refused" in str(exc) or "Failed to connect" in str(exc) or "(7)" in str(exc)):
                        break
        raise RuntimeError(f"Gagal mengambil HTML SSR. HTTP {last_status or 403}")

    @staticmethod
    def _scan_balanced_block(text: str, start_idx: int, open_char: str, close_char: str) -> Tuple[str, int]:
        depth = 0
        in_string = False
        escape = False

        for idx in range(start_idx, len(text)):
            ch = text[idx]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
            else:
                if ch == '"':
                    in_string = True
                elif ch == open_char:
                    depth += 1
                elif ch == close_char:
                    depth -= 1
                    if depth == 0:
                        return text[start_idx : idx + 1], idx + 1
        raise ValueError(f"Blok {open_char}...{close_char} tidak seimbang.")

    def extract(self) -> List[StockRecord]:
        html = self._fetch_html()
        match = re.search(r"window\.__NUXT__\s*=\s*", html)
        if not match:
            raise ValueError("Tag window.__NUXT__ tidak ditemukan dalam dokumen.")

        start_idx = html.find("(", match.end())
        if start_idx == -1:
            raise ValueError("Blok IIFE Nuxt tidak ditemukan.")

        iife_text, _ = self._scan_balanced_block(html, start_idx, "(", ")")
        args_idx = iife_text.rfind("(")
        if args_idx == -1:
            raise ValueError("Argumen string pool IIFE tidak ditemukan.")

        args_str, _ = self._scan_balanced_block(iife_text, args_idx, "(", ")")
        arg_literals = re.findall(r'"((?:\\.|[^"\\])*)"', args_str)
        pool = [lit.encode("utf-8").decode("unicode_escape") for lit in arg_literals]

        if not pool:
            raise ValueError("String pool Nuxt kosong.")

        # Identifikasi record berbasis pola 4-huruf ticker
        records: List[StockRecord] = []
        code_regex = re.compile(r"^[A-Z0-9]{4,6}$")
        for idx, val in enumerate(pool):
            if code_regex.match(val):
                # Validasi calon emiten
                name = pool[idx + 1] if idx + 1 < len(pool) else ""
                if "Tbk" in name or "Persero" in name or "Indonesia" in name or len(name) > 5:
                    board = "Pengembangan"
                    for b in ["Utama", "Pemantauan Khusus", "Akselerasi", "Ekonomi Baru"]:
                        if b in pool[max(0, idx - 5) : min(len(pool), idx + 10)]:
                            board = b
                            break
                    records.append(StockRecord(
                        code=val,
                        name=name,
                        listing_date="",
                        shares=0,
                        listing_board=board,
                        no=len(records) + 1
                    ))

        logger.info("✅ Berhasil mengekstrak %d emiten via NuxtSsrDecompilerExtractor.", len(records))
        return records


def fetch_idx_stocks(impersonate: str = "chrome131", timeout: int = 20) -> List[StockRecord]:
    """
    Mengambil seluruh daftar saham BEI dengan fallback berjenjang.
    """
    try:
        extractor = DirectApiExtractor(impersonate=impersonate, timeout=timeout)
        return extractor.extract()
    except Exception as err:
        logger.warning("⚠️ Direct API gagal (%s), beralih ke Nuxt SSR decompiler...", err)
        try:
            fallback = NuxtSsrDecompilerExtractor(impersonate=impersonate, timeout=timeout)
            return fallback.extract()
        except Exception as fb_err:
            logger.error("❌ Semua strategi ekstraksi IDX gagal: %s", fb_err)
            raise


if __name__ == "__main__":
    stocks = fetch_idx_stocks()
    print(f"Total emiten terkumpul: {len(stocks)}")
    boards = {}
    for s in stocks:
        boards[s.listing_board] = boards.get(s.listing_board, 0) + 1
    print("Sebaran papan:", boards)
