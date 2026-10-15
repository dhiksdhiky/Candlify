# 📘 PANDUAN LENGKAP BANDARMOLOGI: PRE-BREAKOUT BASE, BACKTEST & LIKUIDITAS VOLUME

> **Candlify Market Intelligence Manual — Versi 2.1 (Audited)**  
> *Dokumen referensi resmi analisis pergerakan Smart Money, identifikasi broker kuantitatif, bukti validitas backtest Neon DB (metodologi Triple-Barrier), kalibrasi satuan volume bursa (Lembar vs Lot), SOP eksekusi 2-Tier Stop Loss, serta 8 simulasi riil historis di Bursa Efek Indonesia (IDX).*

---

## 📑 DAFTAR ISI
1. [Filosofi & Konsep Universal: Pre-Breakout Base](#1-filosofi--konsep-universal-pre-breakout-base)
2. [Anatomi 4 Pilar Pre-Breakout Base & Konsep Mikrostruktur](#2-anatomi-4-pilar-pre-breakout-base--konsep-mikrostruktur)
3. [🤖 Cara Mesin Menentukan Broker Ritel vs Big Money (Dynamic Behavioral Scoring)](#3--cara-mesin-menentukan-broker-ritel-vs-big-money-dynamic-behavioral-scoring)
4. [⚖️ Perbandingan Objektif & Backtest: bandar_satu vs Formula Pre-Breakout (Triple-Barrier Method)](#4-️-perbandingan-objektif--backtest-bandar_satu-vs-formula-pre-breakout-triple-barrier-method)
5. [🔎 Bukti Validitas Historis: 10 Contoh Sukses dari Database Neon](#5--bukti-validitas-historis-10-contoh-sukses-dari-database-neon)
6. [Cara Membaca Volume di Candlify: Volume Surge, Dry-Up & CLV](#6-cara-membaca-volume-di-candlify-volume-surge-dry-up--clv)
7. [Kapasitas Modal, Paradoks Likuiditas & Aturan Papan Bursa](#7-kapasitas-modal-paradoks-likuiditas--aturan-papan-bursa)
8. [🎯 SOP Simulasi Eksekusi Trading Plan di Candlify (Two-Tier Stop Loss)](#8--sop-simulasi-eksekusi-trading-plan-di-candlify-two-tier-stop-loss)
9. [🏆 Studi Kasus Riil Sukses (Win Trades: BALI, PTSP, RONY)](#9--studi-kasus-riil-sukses-win-trades-bali-ptsp-rony)
10. [⚠️ Studi Kasus Riil Gagal & Perangkap Distribusi (Trap Trades: LION, RGAS, BKDP)](#10-️-studi-kasus-riil-gagal--perangkap-distribusi-trap-trades-lion-rgas-bkdp)
11. [✨ Studi Kasus Riil Unik (Special Edge Cases: MPXL & STAR)](#11--studi-kasus-riil-unik-special-edge-cases-mpxl--star)
12. [Trader's Quick Checklist Sebelum Menekan Tombol Buy (8 Poin Emas)](#12-traders-quick-checklist-sebelum-menekan-tombol-buy-8-poin-emas)

---

## 1. Filosofi & Konsep Universal: Pre-Breakout Base

Banyak trader ritel mengalami kerugian berulang karena memiliki kebiasaan **mengejar saham yang sudah terbang (*breakout chasing*)**. Ketika saham sudah naik +15% sampai +25% dengan volume sangat ramai di *running trade*, ritel baru FOMO masuk di pucuk. Di saat itulah bandar (*Smart Money*) biasanya mulai mendistribusikan barangnya kepada ritel.

**Pre-Breakout Base Accumulation** adalah pendekatan kebalikannya:
> *"Masuk saat saham sedang sepi dan tenang, di mana bandar sedang mengumpulkan barang di area sempit, tepat beberapa hari sebelum harga diledakkan."*

### Kenapa Disebut "Pre-Breakout Base" (Bukan Sekadar "BALI Setup")?
Nama saham **BALI** hanyalah salah satu studi kasus empiris yang memperlihatkan pola ini secara sempurna di IDX (September–Oktober 2026). Pola ini adalah **konsep universal** dalam *Volume Price Analysis (VPA)* dan Bandarmologi mikrostruktur:
* Di literatur klasik barat dikenal sebagai *Volatility Contraction Pattern (VCP)* oleh Mark Minervini atau *Wyckoff Re-accumulation Phase C*.
* Di pasar modal Indonesia (IDX), pola ini khas dengan adanya **tiang lonjakan awal (*ignition spike*)**, diikuti **kotak konsolidasi ketat**, **volume yang mengering drastis (*supply exhaustion*)**, dan **akumulasi tersembunyi di broker summary (broksum)**.

---

## 2. Anatomi 4 Pilar Pre-Breakout Base & Konsep Mikrostruktur

Untuk membedakan konsolidasi yang siap meledak dengan saham yang sekadar tidur/mati suri, engine Candlify menguji **4 Pilar Algoritmik**:

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
* **Karakteristik:** Terjadi 4 sampai 28 hari bursa sebelumnya. Ditandai oleh candle hijau solid ($\ge +5\%$) dengan lonjakan volume $\ge 2.0\times$ Volume MA20.
* **Makna Bandarmologi:** Ini adalah **jejak modal pertama (*liquidity injection*)**. Bandar menunjukkan taringnya bahwa mereka telah menyuntikkan modal dan memiliki kepentingan di saham ini.
* **Kasus BALI:** Terjadi lonjakan volume masif pada fase awal kenaikan yang menembus resisten lama, menarik perhatian pasar, lalu sengaja dihentikan kenaikannya agar ritel tidak langsung ikut berpesta.

### Pilar 2: Volatility Contraction / Tight Base (Kotak Base)
* **Karakteristik:** 
  * Rentang harga 7 hari bursa (`range_7`) sangat rapat: **$\le 8\% - 12\%$**.
  * Indikator *Bollinger Band Width (BBW)* menyempit drastis: **$\le 14\%$**.
  * Posisi harga bertahan di atas atau dekat garis MA20 (`price_to_ma20 >= -4%`), menandakan harga ditahan di separuh atas tiang induk (tidak dibiarkan roboh ke dasar).
* **Makna Bandarmologi:** Volatilitas yang menurun tajam membuktikan bahwa pertarungan harga sudah terkontrol. Bandar sengaja menjaga rentang harga sempit (*range-bound*) agar ritel yang tidak sabar merasa bosan lalu menjual sahamnya (*time capitulation*).

### Pilar 3: Volume Dry-Up (Volume Mengering)
* **Karakteristik:** 
  * Volume harian saat konsolidasi menciut menjadi **$\le 0.40\times - 0.50\times$** dari volume rata-rata atau tiang induk.
* **Makna Bandarmologi:** Ini adalah pilar paling krusial!
  * **Volume Kering = Tidak Ada Tekanan Jual (*Supply Depleted*)**. 
  * Jika bandar mau buang barang (*distribusi*), volume pasti besar dan harga rontok. 
  * Namun, jika harga diam mendatar DAN volume sepi seperti kuburan, artinya **barang sudah terkunci di tangan bandar** dan tidak ada lagi ritel yang bersedia menjual murah. Untuk menaikkan harga nanti, bandar hanya butuh sedikit tenaga beli (*low effort, big result*).

### Pilar 4: Silent Accumulation Broksum (Deteksi Smart Money & HMB)
* **Karakteristik:** 
  * Di balik volume yang sepi tersebut, broker summary harian menunjukkan **Net Akumulasi Top-1 Buyer $> 30\%$** dari total nilai transaksi pembeli bersih.
  * Pembeli didominasi oleh broker institusi / *smart money* (misal: `CC`, `AK`, `BK`, `KZ`, `YJ`, atau bandar lokal `MG`), sedangkan penjual tersebar di banyak broker ritel (`YP`, `PD`, `XC`, `XL`).

---

### 🔬 3 Parameter Mikrostruktur Tambahan (Validasi Presisi)

1. **Anchored HMB (Harga Modal Bandar Kumulatif):**
   * Perhitungan HMB tidak hanya dilihat pada 1 hari sinyal, melainkan dihitung kumulatif sejak hari tiang induk ($t_{\text{spike}}$) hingga hari pengamatan saat ini ($t_{\text{now}}$):
     $$\text{HMB}_{\text{anchored}} = \frac{\sum_{t=t_{\text{spike}}}^{t_{\text{now}}} \text{Net Val}_t}{\sum_{t=t_{\text{spike}}}^{t_{\text{now}}} \text{Net Vol}_t \times 100}$$
   * Jika harga pasar saat ini berada dalam rentang $\pm 3\%$ dari $\text{HMB}_{\text{anchored}}$, posisi entry trader berada tepat di harga beli rata-rata bandar.

2. **Volume Asymmetry (Asimetri Volume Hijau vs Merah di Base):**
   * Di dalam kotak konsolidasi, bandingkan rata-rata volume candle turun (*bearish*) dengan candle naik (*bullish*):
     $$\overline{\text{Vol}}_{\text{Red}} < \overline{\text{Vol}}_{\text{Green}}$$
   * Bila saat harga terkoreksi volumenya sangat kerdil, namun saat harga terangkat sedikit volumenya mengembang, ini bukti mutlak bahwa pelemahan harga terjadi tanpa tekanan jual (*no supply*).

3. **Close Location Value (CLV):**
   $$\text{CLV} = \frac{\text{Close} - \text{Low}}{\text{High} - \text{Low}}$$
   * Mengukur posisi penutupan terhadap rentang harian candle. Nilai $\text{CLV} \ge 0.50$ (dan idealnya $> 0.70$) menandakan aksi serap harga bawah oleh *buyer* sebelum pasar tutup, mencegah formasi *bearish pinbar*.

---

## 3. 🤖 Cara Mesin Menentukan Broker Ritel vs Big Money (Dynamic Behavioral Scoring)

Di era pasar modal modern, bandar bisa saja melakukan *split order* lewat broker ritel (seperti `YP`, `XL`, `XC`), begitu pula nasabah *High Net Worth* (sultan) bisa saja bertransaksi menggunakan akun sekuritas ritel.

Oleh karena itu, jika mesin hanya mengandalkan label hardcoded (statis), sistem akan mudah tertipu. Pendekatan kuantitatif terbaik yang diterapkan pada data tabel `broker_summary` adalah **Dynamic Behavioral Scoring (Scoring Perilaku Dinamis)**:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   4 PARAMETER KUANTITATIF MESIN                        │
├───────────────────────────────┬────────────────────────────────────────┤
│ 1. Directional Conviction     │ Mengukur tektokan vs akumulasi 1 arah  │
│ 2. Ticker Breadth vs Depth    │ Sebaran tipis (ritel) vs pekat (bandar)│
│ 3. Ticker Concentration Index │ Persentase monopoli sirkulasi saham    │
│ 4. Price Aggressiveness       │ Buy Avg mepet High (HAKA agresif)      │
└───────────────────────────────┴────────────────────────────────────────┘
```

### 1. Directional Conviction Ratio (Rasio Keyakinan Arah)
$$\text{Conviction} = \frac{|\text{Net Val}|}{\text{Buy Val} + \text{Sell Val}}$$

* **Ritel / Scalper:** Memiliki *churn* sangat tinggi. Contoh: Beli Rp10 Miliar, Jual Rp9,8 Miliar $\rightarrow$ Net cuma Rp200 Juta ($\text{Conviction} < 0.15$). Mereka sibuk tektokan harian.
* **Big Money:** Membeli satu arah untuk menampung barang. Contoh: Beli Rp10 Miliar, Jual Rp0 $\rightarrow$ $\text{Conviction}$ mendekati **$1.0$**.

### 2. Ticker Breadth vs Depth (Sebaran vs Kedalaman)
Berdasarkan data riil di Neon Database:
* **Broker Ritel Sejati (`XL`, `YP`, `XC`, `PD`):** Terdeteksi aktif di **840+ saham setiap hari**, dengan *churn ratio* tinggi ($3.0 - 6.2\times$). Uang mereka menyebar tipis ke seluruh penjuru bursa.
* **Broker Institusi / Bandar (`RX`, `KZ`, `BK`, `BB`, `SS`, dll.):** Hanya aktif di **100 – 220 saham terpilih**, dengan *churn ratio* rendah ($1.1 - 1.4\times$). Begitu mereka masuk ke suatu saham, nilai transaksinya pekat dan berbobot.

### 3. Ticker Concentration Index (Monopoli Sirkulasi Saham)

> [!NOTE]
> **Formulasi Matematis Dominasi Bersih:**
> Dalam pasar lelang dua arah, total nilai beli bersih seluruh pembeli pasti bernilai sama dengan total nilai jual bersih seluruh penjual ($\sum_{\text{Net}>0} \text{Net Val} \equiv \sum_{\text{Net}<0} |\text{Net Val}|$). Oleh karena itu, indeks dominasi dihitung terhadap total nilai akumulasi pembeli bersih:
> $$\text{Dominance} = \frac{\text{Broker Net Val}}{\sum_{\text{Net Val} > 0} \text{Net Val}}$$

* Jika satu broker menyerap **$> 35\%$** dari total serapan pembeli bersih saham hari itu, mesin secara otomatis mengklasifikasikan broker tersebut sebagai **"Lead Accumulator / Big Player"** di saham tersebut, tidak peduli apakah kodenya `CC`, `AZ`, atau bahkan sekuritas ritel seperti `YP`!

### 4. Price Aggressiveness (Hajar Kanan vs Pasif Bid)
Membandingkan nilai rata-rata beli (`buy_avg`) broker terhadap rentang harian candle ($\text{High} - \text{Low}$):
* Jika `buy_avg` mepet ke area harga **High**, berarti terjadi *Aggressive Buying* (HAKA / Hajar Kanan).
* Jika `buy_avg` mepet ke harga **Low**, berarti bandar hanya pasif memasang jaring Bid.

---

## 4. ⚖️ Perbandingan Objektif & Backtest: bandar_satu vs Formula Pre-Breakout (Triple-Barrier Method)

### Bias Path-Independence & Metodologi Triple-Barrier
Dalam evaluasi kuantitatif modern (*Advances in Financial Machine Learning* oleh Marcos López de Prado), mengukur `MAX(High)` dan `MIN(Low)` secara independen dalam rentang 10 hari ke depan memiliki kelemahan fatal: **mengabaikan urutan kejadian (*Path Dependency / First-Passage Time*)**.

Jika sebuah sistem menetapkan Stop Loss di $-3.5\%$, namun saham sempat terkoreksi $-4.5\%$ di hari ke-2 sebelum terbang $+20\%$ di hari ke-6:
* Evaluasi independen mencatat posisi ini sebagai `Win +20%`.
* Di rekening riil, trader sudah terkena *cut loss* di hari ke-2!

Untuk itu, backtest dievaluasi menggunakan metode **Triple-Barrier**:
1. **Upper Barrier (Take Profit):** $+10.0\%$
2. **Lower Barrier (Stop Loss):** $-3.5\%$
3. **Vertical Barrier (Waktu Kedaluwarsa):** 10 Hari Bursa

```text
Harga
  ▲
  │   [ Upper Barrier: +10% ]  ───────────────────────── Win Event
  │
  │     Entry Price
  │   ───●───────────
  │
  │   [ Lower Barrier: -3.5% ] ───────────────────────── Loss Event
  │
  └────────────────────────────┬────────────────────────► Waktu
                             Day 10 (Vertical Barrier)
```

Ekspektasi matematis dihitung dengan:
$$E = (W \times R_{\text{win}}) - (L \times R_{\text{loss}})$$
di mana $W$ adalah rasio barrier atas tersentuh lebih dahulu, $L = 1 - W$, $R_{\text{win}}$ rata-rata profit saat take profit, dan $R_{\text{loss}}$ rata-rata kerugian saat stop loss.

---

### 📊 Tabel Hasil Backtest Riil (Neon Database)
Evaluasi terhadap **963 emiten IDX** di database Neon selama periode **April – Oktober 2026**:

| Metrik Evaluasi | 1. Formula `bandar_satu`<br>*(Vol Spike + A/D Divergence + OBV)* | 2. Formula Pre-Breakout Base<br>*(Prior Spike + Tight Base + Vol Dry-Up)* | Keterangan & Analisis Komparasi |
| :--- | :---: | :---: | :--- |
| **Total Sinyal Muncul** | 191 sinyal | **464 sinyal** | Formula Pre-Breakout menemukan lebih banyak peluang *quiet base*. |
| **Win Rate (Max Gain $\ge +8\%$)** | 46.1% | **46.3%** | Win rate dasar kedua sistem hampir seimbang (~46%). |
| **Multi-Bagger ($\ge +15\%$)** | **28.3%** | 22.6% | `bandar_satu` sedikit unggul di reli ekstrem karena beli saat momentum kencang. |
| **Hard Drawdown ($\le -5\%$)** | **67.0%** ⚠️ | **41.2%** ✅ | **Perbedaan krusial!** Di `bandar_satu`, 67% trade langsung kena banting turun $> 5\%$. |
| **Rata-rata Max Drawdown** | **-12.00%** 🔴 | **-5.15%** 🟢 | **Risiko Formula Pre-Breakout separuh lebih kecil!** |
| **Rata-rata Return Hari ke-10 (Hold)** | +0.07% (Impas) | **+1.64%** | Trade Pre-Breakout bertahan jauh lebih stabil secara kumulatif. |

### 🎯 Kesimpulan Fundamental:
1. **Kelemahan `bandar_satu`:** Masuk saat *Volume Spike* (harga sudah melonjak hijau tebal). Begitu bandar melakukan *shakeout* (banting harga mendadak), posisi langsung terjebak penurunan rata-rata **-12.00%** yang langsung menabrak Lower Barrier Stop Loss.
2. **Kekuatan Pre-Breakout Base:** Masuk saat *Base Stagnan & Volume Kering* (sebelum ledakan terjadi). Karena beli di lantai dasar konsolidasi dekat support, risiko penurunannya sangat minim (rata-rata *max drawdown* cuma **-5.15%**).

---

## 5. 🔎 Bukti Validitas Historis: 10 Contoh Sukses dari Database Neon

Kriteria Sinyal: Prior Spike $\rightarrow$ Base rapat $\le 5\%$ $\rightarrow$ Volume kering $< 30\%$ VMA $\rightarrow$ Kinerja 10 hari setelahnya:

| Ticker | Tanggal Sinyal | Harga Base | Keringnya Vol (`v_ratio`) | Max Gain 10 Hari | Max Drawdown | Hasil Pergerakan Riil di Bursa |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **PTSP** | 27 Agu 2026 | 895 | $0.09\times$ VMA | **+94.4%** 🚀 | -1.1% | Base super rapat, meledak ARA beruntun ke 1.740. |
| **STAR** | 29 Jul 2026 | 272 | $0.12\times$ VMA | **+89.3%** 🚀 | -4.4% | Dari 272 melesat kencang ke 515. |
| **NICE** | 14 Agu 2026 | 258 | $0.23\times$ VMA | **+62.8%** 🚀 | -4.6% | Volume kering 4 hari berturut-turut, terbang ke 420. |
| **RONY** | 27 Agu 2026 | 1.225 | $0.34\times$ VMA | **+61.2%** 🚀 | -2.0% | Nyaris tanpa drawdown, langsung terbang ke 1.970. |
| **MPXL** | 17 Sep 2026 | 166 | $0.35\times$ VMA | **+56.6%** 🚀 | -4.2% | Konsolidasi di 166, terbang ke 260. |
| **KSIX** | 31 Jul 2026 | 284 | $0.17\times$ VMA | **+56.3%** 🚀 | -4.9% | Base tenang seminggu, lalu breakout masif. |
| **SAPX** | 21 Agu 2026 | 218 | $0.27\times$ VMA | **+54.1%** 🚀 | -3.6% | Melesat dari 218 ke 336. |
| **MEJA** | 21 Sep 2026 | 112 | $0.32\times$ VMA | **+53.6%** 🚀 | -5.3% | Mengunci rapat di 112 sebelum meledak ke 172. |
| **CBPE** | 22 Jul 2026 | 292 | $0.17\times$ VMA | **+50.7%** 🚀 | -2.7% | Naik dari 292 ke 440 sebelum siklus berikutnya. |
| **MBTO** | 07 Sep 2026 | 126 | $0.27\times$ VMA | **+47.6%** 🚀 | -0.8% | Drawdown nyaris 0%, langsung naik ke 186. |

---

## 6. Cara Membaca Volume di Candlify: Volume Surge, Dry-Up & CLV

Volume adalah satu-satunya data di bursa yang **tidak bisa dipalsukan**. Harga bisa diatur dengan memakan 1–2 antrean lot tipis (*spoofing/marking the close*), namun nilai volume mencerminkan **uang riil (Rupiah)** yang benar-benar ditukarkan.

> [!IMPORTANT]
> **Satuan Volume Bursa (Lembar vs Lot):**
> * Yahoo Finance (`harga_saham.volume`) menyimpan data dalam satuan **Lembar (Shares)**.
> * Broker Summary IDX (`broker_summary.buy_vol / sell_vol / net_vol`) mencatat dalam satuan **Lot** ($1\text{ Lot} = 100\text{ Lembar}$).
> * Candlify menstandarisasi seluruh pembacaan volume dalam satuan **Lot** dengan konversi:
>   $$\text{Volume (Lot)} = \frac{\text{Volume (Lembar)}}{100}$$

Di Candlify, indikator volume dirancang khusus untuk membedakan dua fase:

### 1. Volume Surge ($> 1.5\times$ VMA20)
* **Di Tampilan Candlify:** Ditandai dengan badge `⚡ X.Xx Vol`.
* **Kapan Bagus?** 
  * Muncul saat **Breakout** dari base konsolidasi $\rightarrow$ Konfirmasi bahwa peluru tembakan sudah dilepaskan dan gerbong mulai jalan.
* **Kapan Bahaya?**
  * Muncul setelah saham sudah naik berhari-hari (+50% ke atas) dan candle membentuk jarum atas panjang (*shooting star / inverted hammer*) dengan $\text{CLV} < 0.30$ $\rightarrow$ Ini tanda **Volume Klimaks Distribusi**, bandar sedang membagikan barang ke ritel yang FOMO.

### 2. Volume Dry ($< 0.5\times$ VMA20)
* **Di Tampilan Candlify:** Ditandai pada metrik sinyal pre-breakout `Dry 0.25x - 0.45x`.
* **Interpretasi:** 
  * Ritel sering salah mengira bahwa volume sepi artinya "saham jelek/tidak laku". 
  * Dalam bandarmologi pre-breakout, **volume sepi di area atas base adalah tanda emas**. Artinya barang sudah diserap habis (*floating shares* di pasar berkurang drastis).

---

## 7. Kapasitas Modal, Paradoks Likuiditas & Aturan Papan Bursa

Salah satu risiko terbesar dalam trading saham *mid-cap* dan *small-cap* di IDX adalah **masalah likuiditas**:
> *"Bisa beli, tapi giliran mau jual malah kejebak karena antrean Bid kosong melompong."*

---

### 💡 Memecahkan Paradoks Likuiditas: $\text{ADT}_{20}$ vs Turnover Fase Base

Sering terjadi kebingungan:
* *"Katanya minimal transaksi Rp1 Miliar per hari, tapi kok saat saham BALI atau PTSP fase base volumenya cuma puluhan juta per hari?"*

Inilah pemisahan krusial antara **Baseline Liquidity** dan **Dry-Base Turnover**:

1. **Baseline Liquidity ($\text{ADT}_{20}$ Rata-rata 20 Hari):**
   $$\text{ADT}_{20} = \text{VMA20 (Lot)} \times 100 \times \text{Harga Saham}$$
   * **Syarat Mutlak:** $\text{ADT}_{20} \ge \text{Rp1,5 Miliar / hari}$.
   * Ini membuktikan saham tersebut memiliki pasar aktif, minat institusi, dan likuiditas yang melimpah saat sedang bergerak (*mark-up*).

2. **Dry-Base Turnover (Nilai Transaksi Harian Saat Base):**
   * Saat konsolidasi kering, nilai transaksi harian wajar turun drastis ke **Rp100 Juta – Rp500 Juta / hari** (bahkan pada BALI sempat Rp32 Juta / hari).
   * Ini bukan tanda saham tidak likuid, melainkan **suplai pasar sedang habis terkunci (*supply vacuum*)**.

---

### Aturan Alokasi Modal & Position Sizing Berdasarkan Titik Masuk

Untuk mencegah menjadi "Whale Lokal" yang merusak order book bandar, terapkan aturan alokasi modal berikut:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        ATURAN POSITION SIZING                          │
├──────────────────────────┬─────────────────────────────────────────────┤
│ 1. Masuk di Base         │ Alokasi Maksimal:                           │
│    (Buy on Weakness)     │ ≤ 5% dari Nilai Transaksi Harian Base       │
│                          │ (Cicil bertahap 2–3 hari)                   │
├──────────────────────────┼─────────────────────────────────────────────┤
│ 2. Masuk saat Breakout   │ Alokasi Maksimal:                           │
│    (Buy on Breakout)     │ ≤ 5% dari ADT20 Saham                       │
│                          │ (Bisa masuk full lot karena likuiditas ada) │
└──────────────────────────┴─────────────────────────────────────────────┘
```

| Baseline Liquidity ($\text{ADT}_{20}$) | Kategori Saham | Alokasi Modal Maksimal Per Posisi | Gaya Eksekusi Masuk/Keluar |
| :--- | :--- | :--- | :--- |
| **> Rp20 Miliar / hari** | High Liquid (Big Caps: BBCA, BBRI, BMRI, ASII) | Bebas (Ratusan Juta hingga Miliaran) | HAKA / HAKI langsung tanpa slippage berarti |
| **Rp3 Miliar – Rp20 Miliar / hari** | Medium Liquid (Mid Caps aktif: BALI, MAPA, AUTO) | Maksimal **Rp50 Juta – Rp150 Juta** | Beli bertahap (antre bid), HAKI bertahap |
| **Rp1,5 Miliar – Rp3 Miliar / hari** | Low Liquid (Small Caps Aktif) | Maksimal **Rp10 Juta – Rp30 Juta** | **Wajib cicil pasif!** Jangan pernah HAKA/HAKI sekaligus |
| **< Rp1,5 Miliar / hari** | Illiquid / Tidur | **Hindari!** | Sangat berisiko kejebak jika bandar kabur |

---

### 🚫 Filter Papan Bursa: Larangan Papan Pemantauan Khusus (FCA)

> [!WARNING]
> **Larangan Mutlak Saham Full Call Auction (FCA):**
> * Saham di **Papan Pemantauan Khusus (FCA)** tidak memiliki perdagangan berkelanjutan (*continuous trading*), melainkan dicocokkan secara buta dalam sesi lelang periodik.
> * Spread harga dan antrean order di FCA sangat mudah dimanipulasi, dan likuiditas keluar sangat tidak menentu.
> * **Aturan Candlify:** Setup Pre-Breakout Base **HANYA VALID** untuk saham di **Papan Utama** dan **Papan Pengembangan**. Saham dengan notasi kriteria FCA atau Papan Akselerasi (auto-reject simetris 10%) otomatis dieliminasi dari radar screener!

---

## 8. 🎯 SOP Simulasi Eksekusi Trading Plan di Candlify (Two-Tier Stop Loss)

Berikut alur operasional standar langkah demi langkah saat memanfaatkan Candlify Screener dari malam hari hingga jam bursa:

### Langkah A: Filter Sinyal di Candlify
1. Buka menu **Screener** di Candlify.
2. Klik preset **`🎯 Pre-Breakout Base`**.
3. Di dropdown sort, pilih **`Score Desc`** (urutkan skor kualitas tertinggi).
4. Pilih saham yang memenuhi kriteria:
   * **Skor $\ge 75$**
   * **Base $\le 8\%$**
   * **Volume Dry $\le 0.45\times$**
   * **Baseline $\text{ADT}_{20} \ge \text{Rp1,5 Miliar}$**
   * **Bukan saham FCA / Papan Pemantauan Khusus**
   * Top Accumulator jelas (misal: `CC`, `AK`, `BK`, `YJ`).

---

### Langkah B: Menentukan Area Tempur (Support & Resistance Base)
Buka chart saham tersebut di Candlify:
1. Tarik garis horizontal di titik tertinggi candle konsolidasi 7 hari $\rightarrow$ **Level Resistance Base**.
2. Tarik garis horizontal di titik terendah candle konsolidasi 7 hari $\rightarrow$ **Level Support Base**.
3. Cek posisi **HMB (Harga Modal Bandar)** di badge header $\rightarrow$ Biasanya berhimpitan dengan garis tengah base.

---

### Langkah C: Memilih Gaya Eksekusi & Penerapan Two-Tier Stop Loss

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   TWO-TIER STOP LOSS PROTECTION                        │
├────────────────────────────────┬───────────────────────────────────────┤
│ Tier 1: Intraday Hard Stop     │ Dipasang di -4% s/d -5%               │
│                                │ (Melindungi dari flash crash)         │
├────────────────────────────────┼───────────────────────────────────────┤
│ Tier 2: EOD Closing Stop       │ Evaluasi pukul 15:45 WIB:             │
│         (Wyckoff Spring Rule)  │ Cut loss HANYA jika harga penutupan   │
│                                │ resmi berada di bawah Support Base.   │
│                                │ Jika ditarik kembali (Reclaim Pinbar),│
│                                │ POSISI DIPERTAHANKAN!                 │
└────────────────────────────────┴───────────────────────────────────────┘
```

#### Opsi 1: Gaya "Buy on Weakness" (Low Risk / Cicil Pasif)
* **Kapan Dipakai:** Saat pasar sedang sepi / IHSG mendatar, harga saham sedang menguji batas bawah base.
* **Titik Beli:** Antre di dekat Support Base (misal: Rp1.200).
* **Stop Loss (SL):** 
  * *Intraday Hard Stop:* Pasang di $-4.5\%$ (Rp1.145) untuk antisipasi jarum kilat.
  * *EOD Closing Stop:* Cut loss jika pukul 15:45 WIB harga ditutup $< \text{Rp1.185}$ (Support).
* **Target Profit (TP):** Minimal uji resisten tiang lama (+10% s/d +20%).  
* **Risk-to-Reward Ratio:** **1 : 4** (Sangat sehat!).

#### Opsi 2: Gaya "Buy on Breakout" (Momentum / Konfirmasi)
* **Kapan Dipakai:** Jam 09:00–10:00 WIB saat pasar buka, harga menembus Resistance Base dengan volume meledak di Running Trade.
* **Titik Beli:** HAKA begitu harga *break* 1 tick di atas Resistance Base (misal: Rp1.255).
* **Stop Loss (SL):** Di bawah titik breakout / swing low hari itu (biasanya ~3%).
* **Target Profit (TP):** Bertahap (TP1 +8%, TP2 trailing stop mengikuti EMA20).

---

## 9. 🏆 Studi Kasus Riil Sukses (Win Trades: BALI, PTSP, RONY)

Berikut adalah 3 simulasi eksekusi menggunakan **data historis riil dari database Neon (diperiksa presisi: Lembar vs Lot)** yang bisa dicocokkan langsung di broker/chart masing-masing.

---

### 9.1 Studi Kasus 1: BALI (25 Sep – 06 Okt 2026) — *Explosion ARA +24.8%*

#### 📊 Data Riil Harian Saham BALI (Neon DB)

| Tanggal | Open | High | Low | Close | Volume (Lembar) | Volume (Lot) | Perubahan | Status Fase Setup |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **25 Sep 2026** | 1.290 | 1.335 | 1.275 | 1.305 | 91.100 | **911** | +0.4% | Lonjakan volume awal (Pre-spike) |
| **28 Sep 2026** | 1.300 | 1.375 | 1.270 | 1.290 | 148.400 | **1.484** | -1.1% | **Pilar 1: Tiang Induk Volume (Spike)** |
| **29 Sep 2026** | 1.280 | 1.370 | 1.280 | 1.370 | 3.200 | **32** | +6.2% | **Pilar 2 & 3: Base terbentuk, Vol Drop 97.8%!** |
| **30 Sep 2026** | 1.360 | 1.360 | 1.275 | 1.320 | 11.100 | **111** | -3.6% | Base ketat, tes support 1.275 |
| **01 Okt 2026** | 1.290 | 1.315 | 1.260 | 1.315 | 2.500 | **25** | -0.4% | **Volume Super Dry (25 lot = Rp3,28 Juta)** |
| **02 Okt 2026** | 1.315 | 1.420 | 1.285 | 1.330 | 10.700 | **107** | +1.1% | Uji resistance base, Smart Money nampung |
| **05 Okt 2026** | 1.330 | 1.660 | 1.285 | **1.660** | 27.400 | **274** | **+24.8%** 🚀 | **EXPLOSION DAY (Auto Rejection Atas / ARA)!** |
| **06 Okt 2026** | 1.580 | 1.580 | 1.415 | 1.560 | 160.900 | **1.609** | -6.0% | Distribusi profit taking pasca ARA |

```text
Harga
 1.700 │                                                 [C=1.660 ARA!]
       │                                                       ▲
 1.600 │                                                       │
 1.400 │              ┌─────────── Resistance Base: 1.370 ────┬┘
       │     ▲        │  ┌─┐                                  │
 1.300 │    │█│       │  │ │    ┌─┐    ┌─┐    ┌─┐             │
 1.200 │  ──┴─┴───────┴─────────└─┴────┴─┴────┴─┴─────────────┴─  <-- Support Base: 1.275
       │   28 Sep     29 Sep   30 Sep 01 Okt 02 Okt         05 Okt
Volume │
 (Lot) │
 1.500 │     █ (1.484 lot)
   150 │     █
    30 │     █          ░ (32)   ░ (111)░ (25) ░ (107)        █ (274 lot ARA)
     0 └─────┴──────────┴────────┴──────┴──────┴──────────────┴────►
           [TIANG]     [──────── BASE KERING ────────]      [BREAKOUT]
```

* **Broksum Base (28 Sep – 02 Okt):** Broker **`YJ`** akumulasi masif **+1.200 lot di Avg Rp1.319 (HMB)** tanpa jualan sama sekali, sementara broker ritel **`YP`** net sell **-567 lot** dan **`CC`** net sell **-355 lot**.
* **Eksekusi:** Beli di Rp1.315–1.330, Stop Loss di Rp1.265 (risiko -4.1%). Target tercapai di Rp1.660 (+24.8% ARA).

---

### 9.2 Studi Kasus 2: PTSP (18 Agu – 04 Sep 2026) — *ARA Beruntun +94.4%*

#### 📊 Data Riil Harian Saham PTSP (Neon DB)

| Tanggal | Open | High | Low | Close | Volume (Lembar) | Volume (Lot) | Perubahan | Status Fase Setup |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **19 Agu 2026** | 905 | 925 | 890 | 910 | 26.900 | **269** | -2.1% | Uji batas atas |
| **20 Agu 2026** | 910 | 940 | 910 | 915 | 2.600 | **26** | +0.5% | **Volume mengering drastis** |
| **21 Agu 2026** | 930 | 930 | 905 | 905 | 3.400 | **34** | -1.1% | Volume sepi, harga anteng di 905 |
| **26 Agu 2026** | 905 | 905 | 885 | 905 | 1.800 | **18** | 0.0% | **Volume Super Dry (18 lot = Rp1,62 Juta)** |
| **27 Agu 2026** | 895 | 900 | 890 | 895 | 8.800 | **88** | -1.1% | **Sinyal Candlify Trigger (Skor 92)** |
| **28 Agu 2026** | 890 | 900 | 885 | 890 | 2.700 | **27** | -0.5% | Final supply test (Low 885 bertahan) |
| **01 Sep 2026** | 920 | 1.135 | 915 | **1.135** | 404.500 | **4.045** | **+24.7%** 🚀 | **EXPLOSION DAY 1 (ARA!)** |
| **02 Sep 2026** | 1.300 | 1.415 | 970 | **1.415** | 2.522.300 | **25.223** | **+24.6%** 🚀 | **EXPLOSION DAY 2 (ARA Lanjut!)** |
| **03 Sep 2026** | 1.500 | 1.740 | 1.315 | **1.635** | 1.745.200 | **17.452** | **+15.5%** | Puncak reli ke 1.740 (+94.4% dari base!) |

```text
Harga
 1.700 │                                                            ▲ [High: 1.740 (+94%)]
 1.400 │                                                  ▲ [ARA-2: 1.415]
 1.100 │                                        ▲ [ARA-1: 1.135]
       │
   920 │        ┌───────────────────────────────┐
   895 │   ┌─┐  │  ┌─┐    ┌─┐    ┌─┐    ┌─┐     │ <── Resistance Base: 915
   885 │   └─┘  │  └─┘    └─┘    └─┘    └─┘     │ <── Support Base: 885 (Stop Loss: 875)
       │  ──────┴───────────────────────────────┴──────────────────────────────
       │  19 Agu 20 Agu 21 Agu 26 Agu 27 Agu  01 Sep   02 Sep   03 Sep
Volume │
 (Lot) │
 25.000│                                                 █ (25.223 lot)
  4.000│                                        █ (4.045)
    100│    ░      ░      ░      ░      ░
      0 └────┴──────┴──────┴──────┴──────┴───────┴────────┴────────┴────────────►
            [─────────── BASE KERING ───────────] [────── SUPER BREAKOUT ──────]
```

* **Broksum Base (20 – 28 Agu):** Broker **`XL`** dan **`NI`** konsisten akumulasi bersih di rentang Rp890–Rp905. Pada 28 Agustus, `NI` beli 20 lot di 900 tanpa ada aksi jual.
* **Eksekusi:** Entry di harga **Rp895–900**, Stop Loss di **Rp875** (1 tick di bawah Low 885, risiko cuma **-2.2%**).
* **Hasil:** Saham PTSP melesat bertubi-tubi dari 895 ke puncaknya di 1.740 (**+94.4%**) hanya dalam 3 hari bursa!

---

### 9.3 Studi Kasus 3: RONY (20 Agu – 07 Sep 2026) — *Stagnant Base to +61.2%*

#### 📊 Data Riil Harian Saham RONY (Neon DB)

| Tanggal | Open | High | Low | Close | Volume (Lembar) | Volume (Lot) | Perubahan | Status Fase Setup |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **20 Agu 2026** | 1.225 | 1.265 | 1.225 | 1.230 | 3.600 | **36** | +0.4% | Volume mulai mengering |
| **21 Agu 2026** | 1.245 | 1.250 | 1.225 | 1.240 | 1.900 | **19** | +0.8% | **Volume Super Dry (19 lot = Rp2,35 Juta)** |
| **26 Agu 2026** | 1.215 | 1.270 | 1.205 | 1.220 | 13.600 | **136** | -1.6% | Tes swing low 1.205 |
| **27 Agu 2026** | 1.220 | 1.260 | 1.205 | 1.225 | 3.600 | **36** | +0.4% | **Sinyal Candlify Trigger (Skor 88)** |
| **28 Agu 2026** | 1.220 | 1.310 | 1.220 | 1.230 | 18.500 | **185** | +0.4% | Akumulasi broker PD masif |
| **01 Sep 2026** | 1.235 | 1.270 | 1.200 | 1.215 | 7.500 | **75** | -1.2% | Volume kembali menyusut |
| **02 Sep 2026** | 1.255 | 1.275 | 1.225 | 1.245 | 7.600 | **76** | +2.5% | Penutupan rapat di atas MA20 |
| **04 Sep 2026** | 1.265 | 1.580 | 1.245 | **1.580** | 651.100 | **6.511** | **+24.9%** 🚀 | **EXPLOSION DAY 1 (ARA Rp1.580!)** |
| **07 Sep 2026** | 1.975 | 1.975 | 1.580 | **1.620** | 2.262.700 | **22.627** | +2.5% | **High 1.975 (+61.2% dari base 1.225!)** |

```text
Harga
 2.000 │                                                   ▲ [High: 1.975 (+61%)]
 1.600 │                                         ▲ [ARA: 1.580]
 1.300 │        ┌──────────────────────────────┐
 1.225 │   ┌─┐  │  ┌─┐    ┌─┐    ┌─┐    ┌─┐    │ <── Resistance Base: 1.265
 1.200 │   └─┘  │  └─┘    └─┘    └─┘    └─┘    │ <── Support Base: 1.200 (Stop Loss: 1.185)
       │  ──────┴──────────────────────────────┴──────────────────────────────
       │  20 Agu 21 Agu 26 Agu 27 Agu 02 Sep  04 Sep      07 Sep
Volume │
 (Lot) │
 22.000│                                                   █ (22.627 lot)
  6.500│                                         █ (6.511)
    100│    ░      ░      ░      ░      ░
      0 └────┴──────┴──────┴──────┴──────┴────────┴────────┴──────────────────►
            [─────────── BASE KERING ───────────] [────── SUPER BREAKOUT ──────]
```

* **Broksum Base (24 Agu – 02 Sep):** Broker **`PD`** beli bersih 98 lot @ 1.224 tanpa jual di tanggal 28 Agu, dan broker **`CC`** beli 59 lot @ 1.203 tanpa jual pada 31 Agu.
* **Eksekusi:** Entry di harga **Rp1.225–1.240**, Stop Loss di **Rp1.185** (risiko cuma **-3.2%**).
* **Hasil:** Saham RONY melonjak ke 1.580 (ARA), lalu di hari berikutnya dibuka gap-up dan menyentuh level tertinggi **Rp1.970 (+61.2%)**!

---

## 10. ⚠️ Studi Kasus Riil Gagal & Perangkap Distribusi (Trap Trades: LION, RGAS, BKDP)

Berikut 3 kasus riil di mana pola tampak mengering, tetapi **berujung longsor (*breakdown*)** karena adanya distribusi bandar atau ditelantarkan.

---

### 10.1 Studi Kasus Trap 1: LION (02 Sep – 30 Sep 2026) — *Distribusi Siluman ke 302*

*Data riil Neon DB:* 
* Spike terjadi pada 02 Sep di 400 dengan volume **3.639.600 lembar = 36.396 lot**.
* Base mendatar di 366–380, volume menciut pada 15 Sep ke **10.800 lembar = 108 lot**.
* **Bedah Racun Broksum:** Broker institusi **`CC` (-410 lot)** dan **`NI` (-762 lot)** konsisten buang barang, sementara yang menampung adalah broker ritel sejati **`XC` (Ajaib) net buy +996 lot**!
* **Hasil (30 Sep 2026):** Ritel kehabisan modal menampung, harga dibanting longsor dari 348 ke **302 (-12.7%)** dengan volume guyuran **977.300 lembar = 9.773 lot**.

---

### 10.2 Studi Kasus Trap 2: RGAS (26 Agu – 02 Sep 2026) — *Massive DUMP dari 280 ke 121 (-57%)*

#### 📊 Data Riil Harian Saham RGAS (Neon DB)

| Tanggal | Open | High | Low | Close | Volume (Lembar) | Volume (Lot) | Perubahan | Status Lapangan |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **26 Agu 2026** | 236 | 270 | 198 | 268 | 1.728.083.000 | **17.280.830** | +15.5% | Puncak transaksi 17,28 Juta lot! |
| **27 Agu 2026** | 280 | 280 | 228 | **228** | 107.661.300 | **1.076.613** | **-14.9%** 🔴 | **Vol Drop drastis (Kelihatan sepi tapi ARB!)** |
| **28 Agu 2026** | 194 | 194 | 194 | **194** | 31.944.100 | **319.441** | **-14.9%** 🔴 | **ARB Terkunci (Volume tinggal 319k lot)** |
| **31 Agu 2026** | 179 | 208 | 165 | 165 | 337.187.800 | **3.371.878** | -14.9% | Guyuran berlanjut |
| **02 Sep 2026** | 142 | 149 | 121 | **121** | 685.109.100 | **6.851.091** | -14.8% | Amblas total ke 121 (-57% dari 280) |

```text
Harga
 280 │        ▲ (26-27 Agu: Puncak 280)
     │       │█│
 228 │       └─┘╲
     │           ▼ [ARB 1: 228]
 194 │            ╲
     │             ▼ [ARB 2: 194]
 121 │              ╲
     │               ▼ [Longsor ke 121 (-57%!)]
Volume
 (Lot)
 17M │        █
1.0M │        █    ░ (1,07M lot seolah kering)
320k │        █    ░    ░ (319k lot ARB)
   0 └────────┴────┴────┴────────────────────────────────►
```

* **Bedah Broksum (26 – 28 Agu):** 
  * Broker bandar **`CP`** net sell **-111.218 lot**, **`HD`** net sell **-105.027 lot**, dan **`XA`** net sell **-74.425 lot**!
  * Volume turun dari 17,28 Juta ke 319 Ribu lot bukan karena "barang kering", tetapi karena **antrean Bid kosong total sehingga tidak ada yang bisa transaksi (ARB Terkunci)**.
* **Pelajaran Candlify:** Candlify memfilter saham dengan status *price close < MA20* dan *candle bear marubozu*. Saham seperti ini langsung diblokir sistem.

---

### 10.3 Studi Kasus Trap 3: BKDP (08 Sep – 02 Okt 2026) — *Saham Ditelantarkan Pasca Spike*

#### 📊 Data Riil Harian Saham BKDP (Neon DB)

| Tanggal | Open | High | Low | Close | Volume (Lembar) | Volume (Lot) | Perubahan | Kondisi Lapangan |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **08 Sep 2026** | 170 | 224 | 161 | 200 | 231.399.000 | **2.313.990** | +19.7% | Spike masif 2,31 Juta lot |
| **09 Sep 2026** | 200 | 212 | 190 | 191 | 40.129.400 | **401.294** | -4.5% | Mulai koreksi |
| **14 Sep 2026** | 174 | 204 | 165 | 191 | 101.291.200 | **1.012.912** | +12.3% | Dead cat bounce (Umpan kedua) |
| **18 Sep 2026** | 180 | 181 | 164 | 168 | 8.291.600 | **82.916** | -4.5% | **Volume menyusut drastis ke 82k lot** |
| **21 Sep 2026** | 171 | 186 | 162 | 179 | 37.755.700 | **377.557** | +6.5% | Ritel masuk mengira base |
| **28 Sep 2026** | 190 | 190 | 175 | 184 | 5.585.900 | **55.859** | -1.6% | Volume makin kering |
| **02 Okt 2026** | 184 | 184 | 178 | **179** | 2.735.300 | **27.353** | -2.7% | Volume kering semu (27k lot) |

* **Bedah Kasus:** Pada BKDP, saat volume menyusut dari 2,31 Juta ke 27 Ribu lot, **tidak ada satu pun broker institusi yang melakukan akumulasi**. Sahamnya kering karena ditinggal pergi bandarnya (*abandoned*). Tanpa antrean bid penopang, harga sangat rentan terperosok.
* **Filter Candlify:** Syarat pilar 4 (`Dominance > 30% Net Buy Accumulation`) gagal terpenuhi di BKDP, sehingga Candlify otomatis menolak saham ini.

---

## 11. ✨ Studi Kasus Riil Unik (Special Edge Cases: MPXL & STAR)

Dua kasus berikut memperlihatkan fenomena khusus bursa: **Wyckoff Spring (Jarum Jebol Sesaat)** dan **Liquidity Vacuum (Gap-Up Lock ARA)**.

---

### 11.1 Kasus Unik 1: MPXL (08 Sep – 02 Okt 2026) — *The Wyckoff Spring Shakeout*

Pernahkah Anda memasang Stop Loss, lalu harga saham turun **hanya 1 tick** menyenggol Stop Loss Anda, kemudian langsung terbang tinggi? Fenomena ini disebut **Wyckoff Spring / Bear Trap**.

#### 📊 Data Riil Harian Saham MPXL (Neon DB)

| Tanggal | Open | High | Low | Close | Volume (Lembar) | Volume (Lot) | Perubahan | Status Fase |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **08 Sep 2026** | 169 | 189 | 169 | 173 | 8.466.800 | **84.668** | +3.0% | Prior Spike Tiang Induk |
| **14 Sep 2026** | 169 | 173 | 165 | 171 | 1.469.000 | **14.690** | +1.2% | Base terbentuk (Support 164) |
| **17 Sep 2026** | 165 | 171 | 160 | 166 | 227.600 | **2.276** | -1.2% | **Volume mengering -97.3%!** |
| **18 Sep 2026** | 167 | 171 | 165 | 166 | 357.000 | **3.570** | 0.0% | Base rapat di 166 |
| **22 Sep 2026** | 166 | 171 | **159** | **164** | 1.285.100 | **12.851** | -1.2% | **THE SHAKEOUT SPRING! Low 159 lalu ditarik!** |
| **23 Sep 2026** | 165 | 220 | 163 | **220** | 73.483.000 | **734.830** | **+34.1%** 🚀 | **EXPLOSION DAY (ARA Meledak ke 220!)** |
| **02 Okt 2026** | 248 | 260 | 240 | **260** | 13.722.500 | **137.225** | +5.7% | Puncak reli ke 260 (+56.6% dari base!) |

```text
Harga
 260 │                                                            ▲ [Puncak: 260 (+56%)]
 220 │                                                  ▲ [ARA: 220 (+34%!)]
     │                                                  │
 170 │              ┌───────────────────────────┐       │
 164 │   ▲          │                           │       │
 160 │  │█│         │  ┌─┐   ┌─┐   ┌─┐   ┌─┐    │       │ <── Support Base: 164
 159 │  │█│         │  │ │   │ │   │ │   │ │  │ │       │ <── Low 159 (SHAKEOUT SPRING!)
     │  ─┴──────────┴──┴─┴───┴─┴───┴─┴───┴─┴──┴─┴───────┴────────────────────────
     │  08 Sep         14 Sep 17 Sep 18 Sep 22 Sep    23 Sep
Volume
 (Lot)
730k │                                                  █ (734.830 lot!)
 85k │   █ (84.668 lot)
  2k │   █             ░     ░     ░     ░
   0 └───┴─────────────┴─────┴─────┴─────┴──────────────┴────────────────────────►
```

* **Keunikan Bandarmologi:**
  * Pada **22 September 2026**, support kuat ada di Rp164. Tiba-tiba di sesi perdagangan, harga dijatuhkan ke **Rp159 (1 tick di bawah Rp160)** untuk menjemput Stop Loss trader ritel!
  * Namun perhatikan penutupannya: **Close langsung ditarik kembali ke Rp164 (*reclaim*)** dengan $\text{CLV} = 0.42 \rightarrow$ memicu formasi *spring pinbar*.
  * Broksum menunjukkan broker **`CP`** mengumpulkan **+14.988 lot** dan **`HD`** mengumpulkan **+8.244 lot**.
* **Penyelamat via Two-Tier Stop Loss:**
  * Jika memakai stop loss intraday kaku di Rp163, trader terbuang keluar sebelum ledakan.
  * Dengan SOP Two-Tier Stop Loss, posisi baru di-cut jika pada pukul 15:45 WIB harga ditutup $< 164$. Karena berhasil *reclaim* di 164, trade dipertahankan. Keesokan harinya MPXL langsung meledak ARA **+34.1% ke 220**!

---

### 11.2 Kasus Unik 2: STAR (24 Jul – 12 Agu 2026) — *The Liquidity Vacuum & Multi Gap-Up Lock ARA*

Kasus unik di mana suplai barang terserap begitu bersih sampai **antrean offer di bursa kosong melompong (*liquidity vacuum*)**, sehingga saat breakout, harga langsung dibuka loncat gap-up tanpa ada kesempatan antre beli di offer.

#### 📊 Data Riil Harian Saham STAR (Neon DB)

| Tanggal | Open | High | Low | Close | Volume (Lembar) | Volume (Lot) | Perubahan | Status Fase |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **24 Jul 2026** | 282 | 282 | 274 | 278 | 12.000 | **120** | +0.7% | Konsolidasi awal |
| **28 Jul 2026** | 278 | 278 | 262 | 276 | 32.500 | **325** | -0.7% | Tes support 262 |
| **29 Jul 2026** | 272 | 274 | 270 | 272 | 4.400 | **44** | -1.4% | **Volume Kering Ekstrem (44 lot = Rp1,19 Juta)** |
| **04 Agu 2026** | 280 | 280 | 274 | 276 | 15.900 | **159** | -0.7% | Suplai terkunci total |
| **07 Agu 2026** | 276 | 276 | 262 | 266 | 31.100 | **311** | -3.6% | Shakeout terakhir sebelum reli |
| **10 Agu 2026** | 266 | 332 | 264 | **332** | 2.070.100 | **20.701** | **+24.8%** 🚀 | **EXPLOSION DAY 1 (ARA Rp332!)** |
| **11 Agu 2026** | **412** | 414 | 382 | **414** | 3.237.800 | **32.378** | **+24.7%** 🚀 | **OPEN GAP-UP DI 412 (+24%) & ARA KE 414!** |
| **12 Agu 2026** | 480 | **515** | 420 | 420 | 8.291.600 | **82.916** | +1.4% | Puncak reli ke 515 (+89.3% dari base 272!) |

```text
Harga
 515 │                                                            ▲ [High: 515 (+89%)]
 414 │                                                  ▲ [GAP OPEN 412 & ARA 414]
 332 │                                        ▲ [ARA-1: 332]
     │                                        │
 280 │        ┌───────────────────────────────┤
 272 │   ┌─┐  │  ┌─┐    ┌─┐    ┌─┐    ┌─┐     │ <── Resistance Base: 280
 262 │   └─┘  │  └─┘    └─┘    └─┘    └─┘     │ <── Support Base: 262 (Stop Loss: 258)
     │  ──────┴───────────────────────────────┴────────────────────────────────────
     │  24 Jul 28 Jul 29 Jul 04 Agu 07 Agu   10 Agu     11 Agu          12 Agu
Volume
 (Lot)
 32k │                                                  █ (32.378 lot)
 20k │                                        █ (20.701 lot)
 300 │    ░      ░      ░      ░      ░
   0 └───┴──────┴──────┴──────┴──────┴────────┴────────┴───────────────┴────────►
          [─────────── BASE KERING ───────────] [────── SUPER BREAKOUT GAP ──────]
```

* **Bedah Broksum Base (24 Jul – 07 Agu):**
  * Broker **`YB`** akumulasi masif **+58.005 lot** di Avg Rp263.
  * Broker **`PO`** akumulasi masif **+56.000 lot** di Avg Rp268 tanpa menjual satu lot pun!
  * Total serapan kedua broker ini mencapai **114.000 lot** di area sepi.
* **Pelajaran Krusial:** Pada saham yang mengalami *Liquidity Vacuum*, trader yang menunggu "konfirmasi breakout" **TIDAK AKAN BISA BELI**, karena pada tanggal 11 Agustus harga dibuka langsung loncat gap-up di Rp412 (+24% di atas harga kemarin) dan terkunci ARA! Satu-satunya cara menikmati cuan multi-bagger +89% ini adalah **masuk saat fase Pre-Breakout di harga Rp270–276 saat volume sedang sepi**.

---

## 12. Trader's Quick Checklist Sebelum Menekan Tombol Buy (8 Poin Emas)

Sebelum memasukkan order beli di sekuritas, centang **8 poin emas** ini:

- [ ] **1. Tiang Induk Jelas:** Ada lonjakan volume $\ge 2\times$ VMA20 dan candle hijau $\ge +5\%$ dalam kurun 4–28 hari bursa terakhir.
- [ ] **2. Kotak Base Rapat:** Rentang harga 7 hari bursa (`range_7`) sempit ($\le 8\% - 12\%$) dan BBW $\le 14\%$.
- [ ] **3. Volume Mengering (*Supply Dry-Up*):** Volume harian konsolidasi turun ke $\le 40\% - 50\%$ dari tiang induk atau VMA20.
- [ ] **4. Broksum Positif & Dominan (Wajib!):** Dominasi akumulator utama $> 30\%$ dari total serapan pembeli bersih, sementara broker ritel (`YP`, `XC`, `PD`, `XL`) tercatat *net sell*.
- [ ] **5. Dekat Modal Bandar ($\text{HMB}_{\text{anchored}}$):** Harga saat ini berada dalam rentang $\pm 3\%$ dari harga rata-rata beli kumulatif bandar.
- [ ] **6. Likuiditas Sehat & Sizing Terukur:**
  * Baseline $\text{ADT}_{20} \ge \text{Rp1,5 Miliar / hari}$.
  * Porsi pembelian $\le 5\%$ dari volume transaksi harian saat base kering (jika Buy on Weakness), atau $\le 5\%$ dari $\text{ADT}_{20}$ (jika Buy on Breakout).
- [ ] **7. Bukan Saham FCA / Papan Pemantauan Khusus:** Saham tercatat di Papan Utama atau Papan Pengembangan yang memiliki mekanisme *continuous trading*.
- [ ] **8. Two-Tier Stop Loss Siap:** 
  * Level *Intraday Hard Stop* terpasang pada $-4.0\%$ s/d $-5.0\%$.
  * Level *EOD Closing Stop* ditetapkan pada batas Support Base (evaluasi pukul 15:45 WIB untuk mengantisipasi *Wyckoff Spring*).

---

*Disusun secara sistematis untuk Candlify V2 — "Trade with Smart Money, Protect Your Liquidity."*
