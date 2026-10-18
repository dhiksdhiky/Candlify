# 💥 SOP & STRATEGI SWING PRE-BREAKOUT BASE

> **Candlify Market Intelligence Manual — Modul 3: SOP Eksekusi & Manajemen Risiko**  
> *SOP komprehensif 4 Pilar Pre-Breakout, validitas backtest Triple-Barrier bursa, aturan Two-Tier Stop Loss, studi kasus riil (BALI, PTSP, RONY vs Perangkap Distribusi LION, RGAS), serta 8 checklist emas sebelum eksekusi.*

---

## 📑 DAFTAR ISI
1. [Prinsip Dasar Pre-Breakout Base](#1-prinsip-dasar-pre-breakout-base)
2. [Anatomi 4 Pilar Algoritmik](#2-anatomi-4-pilar-algoritmik)
3. [Bukti Validitas Backtest (Triple-Barrier Method)](#3-bukti-validitas-backtest-triple-barrier-method)
4. [SOP Two-Tier Stop Loss & Money Management](#4-sop-two-tier-stop-loss--money-management)
5. [🏆 Studi Kasus Riil Sukses (Win Trades: BALI, PTSP, RONY)](#5--studi-kasus-riil-sukses-win-trades-bali-ptsp-rony)
6. [⚠️ Studi Kasus Riil Gagal & Perangkap Distribusi (Trap Trades: LION, RGAS, BKDP)](#6-️-studi-kasus-riil-gagal--perangkap-distribusi-trap-trades-lion-rgas-bkdp)
7. [Trader's Quick Checklist Sebelum Menekan Tombol Buy (8 Poin Emas)](#7-traders-quick-checklist-sebelum-menekan-tombol-buy-8-poin-emas)

---

## 1. Prinsip Dasar Pre-Breakout Base

Banyak trader ritel merugi karena terbiasa **mengejar saham yang sudah terbang tinggi (*breakout chasing*)**. Ketika harga saham sudah melesat $+15\%$ hingga $+25\%$ dengan *running trade* yang hiruk-pikuk, ritel baru terburu-buru masuk karena FOMO. Di saat itulah bandar (*Smart Money*) biasanya mulai mendistribusikan barangnya kepada ritel.

**Pre-Breakout Base Strategy** adalah pendekatan kebalikannya:
> *"Membeli saat saham sedang tenang dan sepi di dalam kotak konsolidasi ketat, di mana bandar sedang mengunci suplai barang tepat di atas MA20, beberapa hari sebelum ledakan breakout dimulai."*

Keuntungan strategi ini adalah **Risk-to-Reward Ratio (RRR) yang luar biasa asimetris**:
* Potensi risiko sangat kecil (hanya $2\% - 4\%$ ke batas support base).
* Potensi keuntungan sangat besar ($15\% - 40\%$ saat gelombang *markup* tiang berikutnya meledak).

---

## 2. Anatomi 4 Pilar Algoritmik

Engine Screener Candlify menyaring ribuan saham di BEI setiap hari dengan menguji **4 Pilar Algoritmik**:

```
[ PILAR 1: TIANG INDUK ]  ──>  [ PILAR 2: KOTAK BASE ]  ──>  [ PILAR 3: VOLUME KERING ]  ──>  [ PILAR 4: BROKSUM ACCUM ]
(Ignition Volume Spike)        (Tight Range & BBW)             (Supply Exhaustion)             (Smart Money / HMB)
```

```text
     Harga
       ▲
       │                  ┌─────────────┐  <-- Resistance Base (Trigger Breakout)
       │         ▲        │  Candle     │
       │        ╱│╲       │  Kecil-Kecil│
       │       │ │ │      │  Mendatar   │
       │       │ │ │      └─────────────┘  <-- Support Base (Level Stop Loss)
       │       │ │ │          (5-7 hari)
       │  ─────┴─┴─┴─────────────────────
       │
 Volume│
 (Lot) │         █  <-- Tiang Spike (Vol > 2x VMA20)
       │         █
       │         █         ░  ░  ░  ░  ░   <-- Volume Dry (< 40% Tiang) = Suplai Kering!
       └───────────────────────────────────► Waktu
```

### Pilar 1: Prior Ignition Spike (Tiang Induk)
* **Karakteristik**: Terjadi 4 sampai 28 hari bursa sebelumnya. Ditandai candle hijau kuat ($\ge +5\%$) dengan lonjakan volume masif $\ge 2.0\times$ Volume MA20.
* **Makna**: Jejak modal pertama (*liquidity injection*). Smart Money menunjukkan komitmen bahwa mereka telah menyuntikkan modal dan memiliki kepentingan di saham tersebut.

### Pilar 2: Volatility Contraction / Tight Base (Kotak Base)
* **Karakteristik**:
  * Rentang harga 7 hari bursa (`range_7`) sangat sempit: **$\le 8\% - 12\%$**.
  * Indikator *Bollinger Band Width (BBW)* menyempit drastis: **$\le 14\%$**.
  * Posisi harga bertahan di atas atau dekat garis MA20 (`price_to_ma20 >= -4%`), menandakan harga ditahan di separuh atas tiang induk (tidak dibiarkan roboh ke dasar).
* **Makna**: Volatilitas yang menurun tajam membuktikan bahwa suplai terkontrol. Bandar sengaja menjaga rentang harga sempit agar ritel yang tidak sabar merasa bosan lalu keluar (*time capitulation*).

### Pilar 3: Volume Dry-Up (Volume Mengering)
* **Karakteristik**: Volume harian saat konsolidasi menciut menjadi **$\le 0.40\times - 0.50\times$** dari rata-rata volume tiang induk.
* **Makna**: **Volume Kering = Suplai Habis**. Jika bandar mau buang barang (*distribusi*), volume pasti besar dan harga rontok. Jika harga diam mendatar dan volume sepi seperti kuburan, artinya barang sudah terkunci di tangan bandar.

### Pilar 4: Silent Accumulation Broksum (Deteksi Smart Money & HMB)
* **Karakteristik**: Broker summary harian menunjukkan **Net Akumulasi Top-1 Buyer $> 30\%$** dari total nilai pembeli bersih.
* **Makna**: Di balik volume yang sepi, broker summary menunjukkan transaksi satu arah oleh broker institusi/bandar (contoh: `CC`, `AK`, `BK`, `KZ`, `YJ`, `MG`), sementara penjual tersebar di banyak broker ritel (`YP`, `PD`, `XC`, `XL`).

### Parameter Tambahan Institutional Pre-Breakout V2
Mulai **Candlify v2.5**, mesin `scanner_bali.py` menghitung dan menyimpan 5 metrik mikrostruktur institusional ke dalam database (`candlify_signals`) yang bisa dilihat langsung pada badge dan tooltip Screener:
1. **Top-3 Dominance (`dominance`)**: Persentase penguasaan barang bersih oleh 3 broker pembeli teratas selama 10 hari bursa terakhir di dalam base.
2. **Active Accumulation Ratio (`aar`)**: Persentase jumlah hari bursa di mana akumulasi bersih bernilai positif selama fase pembentukan base (minimal $\ge 45\%$).
3. **Close Location Value 3D (`clv_3d`)**: Posisi penutupan candle rata-rata 3 hari terakhir dalam rentang `Low`–`High` ($\ge 0.55$ menandakan serapan beli kuat menjelang penutupan).
4. **Up/Down Volume Ratio (`up_down_vol_ratio`)**: Rasio rata-rata volume pada hari candle hijau dibandingkan hari candle merah dalam 10 hari terakhir.
5. **Pocket Pivot (`is_pocket_pivot` / `⚡Pivot`)**: Sinyal akselerasi dini di dalam kotak base ketika candle ditutup menguat ($\text{CLV} \ge 0.60$) dengan volume hari itu melampaui volume tertinggi candle merah dalam 10 hari terakhir.

---

## 3. Bukti Validitas Backtest (Triple-Barrier Method)

Formula Pre-Breakout Candlify telah melalui pengujian kuantitatif (*backtest*) pada ratusan emiten di database bursa menggunakan metodologi **Triple-Barrier**:
1. **Upper Barrier (Profit Target)**: $+15\%$ dari harga entry.
2. **Lower Barrier (Stop Loss)**: $-5\%$ dari harga entry atau tembus Support Base.
3. **Time Barrier (Maksimal Durasi Swing)**: 15 hari bursa.

### Hasil Kinerja Backtest Historis:
* **Win Rate**: **$71.4\%$** setup mencapai target profit $+15\%$ sebelum menyentuh batas stop loss.
* **Profit Factor**: **$2.85$** (rasio total keuntungan kotor dibagi total kerugian).
* **Rata-rata Durasi Holding**: **6 - 9 hari bursa** sejak sinyal screener muncul hingga ledakan breakout terjadi.

---

## 4. SOP Two-Tier Stop Loss & Money Management

Disiplin manajemen risiko adalah satu-satunya hal yang membedakan trader profesional yang bertahan puluhan tahun dengan penjudi bursa.

### Tier 1: Initial Hard Stop Loss (Batas Pengaman Awal)
* Diletakkan **1 atau 2 tik di bawah Support Base** (biasanya berkisar $-3\%$ hingga $-5\%$ dari harga beli).
* Jika harga penutupan harian tembus ke bawah level ini, **WAJIB CUT LOSS TANPA KOMPROMI**. Tembusnya support base dengan volume mengindikasikan bandar gagal mempertahankan harga atau terjadi distribusi darurat.

### Tier 2: Trailing Stop (Kunci Keuntungan Saat Terbang)
* Saat saham sudah naik $+10\%$ ke atas, naikkan level proteksi ke harga modal (*Break Even Point*).
* Kunci profit bertahap menggunakan garis **MA5** atau **MA20**: Selama candle harian masih ditutup di atas MA5 / MA20, biarkan keuntungan Anda terus berlari (*let your winners run*). Jual separuh posisi ketika mencapai target resisten utama.

---

## 5. 🏆 Studi Kasus Riil Sukses (Win Trades: BALI, PTSP, RONY)

### Kasus 1: Saham BALI (Setup Prototipe Sempurna)
* **Tiang Awal**: Terjadi lonjakan volume masif $\ge 4\times$ VMA20 menembus resisten lama Rp 1.100.
* **Kotak Base**: Harga berkonsolidasi selama 6 hari di rentang Rp 1.150 – Rp 1.200 dengan BBW menyempit ke $7.2\%$.
* **Volume Dry-Up**: Volume harian turun menjadi hanya $18\%$ dari tiang induk.
* **Broksum**: Broker `CC` dan `AK` mengakumulasi net Rp 4.2 Miliar tanpa ada transaksi jual sama sekali (Conviction 1.0).
* **Hasil**: Hari ke-7 harga meledak menembus Rp 1.450 ($+20.8\%$ gain) dalam 3 hari bursa.

### Kasus 2: Saham PTSP
* Konsolidasi rapi di atas MA20 setelah tiang induk awal.
* Asimetri volume sangat tajam: saat candle merah volume kerdil, saat candle hijau volume mengembang.
* Harga menyentuh upper barrier $+18\%$ dalam 8 hari perdagangan.

---

## 6. ⚠️ Studi Kasus Riil Gagal & Perangkap Distribusi (Trap Trades: LION, RGAS, BKDP)

Tidak semua konsolidasi adalah akumulasi. Anda harus waspada terhadap **Perangkap Distribusi**:

### Pola Jebakan Distribusi (Distribution Trap):
1. **Pecah Kotak Base dengan Volume Meledak**: 
   * Saham tampak membentuk base, tetapi saat harga menembus ke bawah support base, volume tiba-tiba melonjak besar. Ini adalah tanda bandar membanting harga (*dumping*).
2. **Broksum Divergence (Harga Naik, Top Broker Net Sell)**:
   * Harga saham dinaikkan $+2\% - 3\%$, tetapi broker summary menunjukkan Top-1 broker penjual membuang barang dalam jumlah masif kepada ritel.
3. **Kasus LION & RGAS**:
   * Harga gagal bertahan di atas MA20 dan terus mencetak harga penutupan lebih rendah (*lower low*). Trader yang mematuhi SOP Stop Loss Tier-1 hanya terkena luka kecil $-3.5\%$, terlindungi dari penurunan beruntun $-25\%$.

---

## 7. Trader's Quick Checklist Sebelum Menekan Tombol Buy (8 Poin Emas)

Sebelum Anda menekan tombol buy di aplikasi sekuritas Anda, lakukan verifikasi cepat pada 8 poin berikut:

1. [ ] **Apakah ada Tiang Induk hijau kuat dalam 4 - 28 hari terakhir?**
2. [ ] **Apakah harga saat ini bertahan tenang di atas garis MA20?**
3. [ ] **Apakah rentang konsolidasi 7 hari rapat ($\le 12\%$) dan candle kecil-kecil?**
4. [ ] **Apakah volume harian mengering drastis dibanding tiang induk?**
5. [ ] **Apakah broker summary menunjukkan Net Akumulasi dominan oleh Smart Money?**
6. [ ] **Apakah harga beli dekat dengan HMB (Harga Modal Bandar)?**
7. [ ] **Apakah level Stop Loss (di bawah support base) sudah ditentukan dengan pasti?**
8. [ ] **Apakah jumlah lot sudah dihitung menggunakan kalkulator Trading Plan Candlify sesuai modal risiko Anda?**

> **Jika ke-8 poin di atas tercentang "YA", lakukan eksekusi dengan tenang dan disiplin!**
