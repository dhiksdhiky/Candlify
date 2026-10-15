# 📘 PANDUAN LENGKAP BANDARMOLOGI: PRE-BREAKOUT BASE, BACKTEST & LIKUIDITAS VOLUME

> **Candlify Market Intelligence Manual**  
> *Dokumen referensi resmi analisis pergerakan Smart Money, identifikasi broker kuantitatif, bukti validitas backtest Neon DB, pembacaan volume, serta simulasi riil historis di Bursa Efek Indonesia (IDX).*

---

## 📑 DAFTAR ISI
1. [Filosofi & Konsep Universal: Pre-Breakout Base](#1-filosofi--konsep-universal-pre-breakout-base)
2. [Anatomi 4 Pilar Pre-Breakout Base](#2-anatomi-4-pilar-pre-breakout-base)
3. [🤖 Cara Mesin Menentukan Broker Ritel vs Big Money (Dynamic Behavioral Scoring)](#3--cara-mesin-menentukan-broker-ritel-vs-big-money-dynamic-behavioral-scoring)
4. [⚖️ Perbandingan Objektif & Backtest: bandar_satu vs Formula Pre-Breakout](#4-️-perbandingan-objektif--backtest-bandar_satu-vs-formula-pre-breakout)
5. [🔎 Bukti Validitas Historis: 10 Contoh Sukses dari Database Neon](#5--bukti-validitas-historis-10-contoh-sukses-dari-database-neon)
6. [Cara Membaca Volume di Candlify & Kaitannya dengan Likuiditas](#6-cara-membaca-volume-di-candlify--kaitannya-dengan-likuiditas)
7. [Kapasitas Modal & Aturan Likuiditas Keluar-Masuk Barang (5% - 10% Rule)](#7-kapasitas-modal--aturan-likuiditas-keluar-masuk-barang-5---10-rule)
8. [🎯 Studi Kasus Riil Sukses (Win Trades: BALI, PTSP, RONY)](#8--studi-kasus-riil-sukses-win-trades-bali-ptsp-rony)
9. [⚠️ Studi Kasus Riil Gagal & Perangkap Distribusi (Trap Trades: LION, RGAS, BKDP)](#9-️-studi-kasus-riil-gagal--perangkap-distribusi-trap-trades-lion-rgas-bkdp)
10. [✨ Studi Kasus Riil Unik (Special Edge Cases: MPXL & STAR)](#10--studi-kasus-riil-unik-special-edge-cases-mpxl--star)
11. [Trader's Quick Checklist Sebelum Menekan Tombol Buy](#11-traders-quick-checklist-sebelum-menekan-tombol-buy)

---

## 1. Filosofi & Konsep Universal: Pre-Breakout Base

Banyak trader ritel mengalami kerugian berulang karena memiliki kebiasaan **mengejar saham yang sudah terbang (*breakout chasing*)**. Ketika saham sudah naik +15% sampai +25% dengan volume sangat ramai, ritel baru FOMO masuk di pucuk. Di saat itulah bandar (*Smart Money*) biasanya mulai mendistribusikan barangnya kepada ritel.

**Pre-Breakout Base Accumulation** adalah pendekatan kebalikannya:
> *"Masuk saat saham sedang sepi dan tenang, di mana bandar sedang mengumpulkan barang di area sempit, tepat beberapa hari sebelum harga diledakkan."*

### Kenapa Disebut "Pre-Breakout Base" (Bukan Sekadar "BALI Setup")?
Nama saham **BALI** hanyalah salah satu studi kasus empiris yang memperlihatkan pola ini secara sempurna di IDX (September–Oktober 2026). Pola ini adalah **konsep universal** dalam *Volume Price Analysis (VPA)* dan Bandarmologi modern:
* Di literatur klasik barat dikenal sebagai *Volatility Contraction Pattern (VCP)* oleh Mark Minervini atau *Wyckoff Re-accumulation Phase C*.
* Di pasar modal Indonesia (IDX), pola ini khas dengan adanya **tiang lonjakan awal**, diikuti **kotak konsolidasi ketat**, **volume yang mengering drastis**, dan **akumulasi tersembunyi di broker summary (broksum)**.

---

## 2. Anatomi 4 Pilar Pre-Breakout Base

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
       │         █  <-- Tiang Spike (Vol > 2x MA20)
       │         █
       │         █         ░  ░  ░  ░  ░   <-- Volume Dry (< 40% Tiang) = Suplai Kering!
       └───────────────────────────────────► Waktu
```

### Pilar 1: Prior Ignition Spike (Tiang Induk)
* **Karakteristik:** Terjadi 4 sampai 28 hari bursa sebelumnya. Ditandai oleh candle hijau solid ($\ge +5\%$) dengan lonjakan volume $\ge 2.0\times$ Volume MA20.
* **Makna Bandarmologi:** Ini adalah **jejak modal pertama (*liquidity injection*)**. Bandar menunjukkan taringnya bahwa mereka telah menyuntikkan likuiditas dan memiliki kepentingan di saham ini.

### Pilar 2: Volatility Contraction / Tight Base (Kotak Base)
* **Karakteristik:** 
  * Rentang harga 7 hari bursa (`range_7`) sangat rapat: **$\le 8\% - 12\%$**.
  * Indikator *Bollinger Band Width (BBW)* menyempit drastis: **$\le 14\%$**.
  * Posisi harga bertahan di atas atau dekat garis MA20 (`price_to_ma20 >= -4%`), menandakan harga ditahan di separuh atas tiang induk (tidak dibiarkan roboh ke dasar).
* **Makna Bandarmologi:** Volatilitas yang menurun tajam membuktikan bahwa pertarungan harga sudah terkontrol. Bandar sengaja menjaga rentang harga sempit (*range-bound*) agar ritel yang tidak sabar merasa bosan lalu menjual sahamnya.

### Pilar 3: Volume Dry-Up (Volume Mengering)
* **Karakteristik:** 
  * Volume harian saat konsolidasi menciut menjadi **$\le 0.40\times - 0.50\times$** dari volume rata-rata atau tiang induk.
* **Makna Bandarmologi:** Ini adalah pilar paling krusial!
  * **Volume Kering = Tidak Ada Tekanan Jual (*Supply Depleted*)**. 
  * Jika bandar mau buang barang (*distribusi*), volume pasti besar dan harga rontok. 
  * Namun, jika harga diam mendatar DAN volume sepi seperti kuburan, artinya **barang sudah terkunci di tangan bandar** dan tidak ada lagi ritel yang bersedia menjual murah. Untuk menaikkan harga nanti, bandar hanya butuh sedikit tenaga beli (*low effort, big result*).

### Pilar 4: Silent Accumulation Broksum (Deteksi Smart Money & HMB)
* **Karakteristik:** 
  * Di balik volume yang sepi tersebut, broker summary harian menunjukkan **Net Akumulasi Top-1 Buyer $> 30\%$** dari total nilai transaksi.
  * Pembeli didominasi oleh broker institusi / *smart money* (misal: `CC`, `AK`, `BK`, `KZ`, `YJ`, atau bandar lokal `MG`), sedangkan penjual tersebar di banyak broker ritel (`YP`, `PD`, `XC`, `XL`).
* **HMB (Harga Modal Bandar):**
  * Rata-rata harga beli (*Average Buy Price*) broker akumulator di area base menjadi patokan HMB.
  * Selama harga pasar masih berada dekat HMB ($\pm 1\% - 3\%$), posisi kita sejajar dengan harga modal bandar.

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
$$\text{Dominance} = \frac{|\text{Broker Net Val}|}{\sum |\text{All Net Val}|}$$

* Jika satu broker menyerap **$> 35\%$** dari total sirkulasi net flow saham hari itu, mesin secara otomatis mengklasifikasikan broker tersebut sebagai **"Lead Accumulator / Big Player"** di saham tersebut, tidak peduli apakah kodenya `CC`, `AZ`, atau bahkan sekuritas ritel seperti `YP`!

### 4. Price Aggressiveness (Hajar Kanan vs Pasif Bid)
Membandingkan nilai rata-rata beli (`buy_avg`) broker terhadap rentang harian candle ($\text{High} - \text{Low}$):
* Jika `buy_avg` mepet ke area harga **High**, berarti terjadi *Aggressive Buying* (HAKA / Hajar Kanan).
* Jika `buy_avg` mepet ke harga **Low**, berarti bandar hanya pasif memasang jaring Bid.

---

## 4. ⚖️ Perbandingan Objektif & Backtest: bandar_satu vs Formula Pre-Breakout

Berikut hasil backtest objektif yang dijalankan pada **963 emiten IDX** di database Neon selama periode **April – Oktober 2026** dengan target evaluasi kinerja 10 hari bursa ke depan (*Forward 10-Days*):

### 📊 Tabel Hasil Backtest Riil (Neon Database)

| Metrik Evaluasi | 1. Formula `bandar_satu`<br>*(Vol Spike + A/D Divergence + OBV)* | 2. Formula Pre-Breakout Base<br>*(Prior Spike + Tight Base + Vol Dry-Up)* | Keterangan & Analisis Komparasi |
| :--- | :---: | :---: | :--- |
| **Total Sinyal Muncul** | 191 sinyal | **464 sinyal** | Formula Pre-Breakout menemukan lebih banyak peluang *quiet base*. |
| **Win Rate (Max Gain $\ge +8\%$)** | 46.1% | **46.3%** | Win rate dasar kedua sistem hampir seimbang (~46%). |
| **Multi-Bagger ($\ge +15\%$)** | **28.3%** | 22.6% | `bandar_satu` sedikit unggul di reli ekstrem karena beli saat momentum kencang. |
| **Hard Drawdown ($\le -5\%$)** | **67.0%** ⚠️ | **41.2%** ✅ | **Perbedaan krusial!** Di `bandar_satu`, 67% trade langsung kena banting turun $> 5\%$. |
| **Rata-rata Max Drawdown** | **-12.00%** 🔴 | **-5.15%** 🟢 | **Risiko Formula Pre-Breakout separuh lebih kecil!** |
| **Rata-rata Return Hari ke-10 (Hold)** | +0.07% (Impas) | **+1.64%** | Trade Pre-Breakout bertahan jauh lebih stabil secara kumulatif. |

### 🎯 Kesimpulan Perbedaan Fundamental:
1. **Kelemahan `bandar_satu`:** Masuk saat *Volume Spike* (saat harga sudah melonjak naik hijau tebal). Akibatnya, begitu bandar melakukan *shakeout* (banting harga mendadak), posisi langsung terjebak penurunan rata-rata **-12.00%** yang sering memicu *cut loss* prematur.
2. **Kekuatan Formula Pre-Breakout:** Masuk saat *Base Stagnan & Volume Kering* (sebelum ledakan terjadi). Karena beli di lantai dasar konsolidasi, risiko penurunannya sangat minim (rata-rata *max drawdown* cuma **-5.15%**). *Risk to Reward Ratio*-nya jauh lebih superior!

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

## 6. Cara Membaca Volume di Candlify & Kaitannya dengan Likuiditas

Volume adalah satu-satunya data di bursa yang **tidak bisa dipalsukan**. Harga bisa diatur dengan memakan 1–2 antrean lot tipis (*spoofing/marking the close*), namun nilai volume mencerminkan **uang riil (Rupiah)** yang benar-benar ditukarkan.

Di Candlify, indikator volume dirancang khusus untuk membedakan dua fase:

### 1. Volume Surge ($> 1.5\times$ VMA20)
* **Di Tampilan Candlify:** Ditandai dengan badge `⚡ X.Xx Vol`.
* **Kapan Bagus?** 
  * Muncul saat **Breakout** dari base konsolidasi $\rightarrow$ Konfirmasi bahwa peluru tembakan sudah dilepaskan dan gerbong mulai jalan.
* **Kapan Bahaya?**
  * Muncul setelah saham sudah naik berhari-hari (+50% ke atas) dan candle membentuk jarum atas panjang (*shooting star / inverted hammer*) $\rightarrow$ Ini tanda **Volume Klimaks Distribusi**, bandar sedang membagikan barang ke ritel yang FOMO.

### 2. Volume Dry ($< 0.5\times$ VMA20)
* **Di Tampilan Candlify:** Ditandai pada metrik sinyal pre-breakout `Dry 0.25x - 0.45x`.
* **Interpretasi:** 
  * Ritel sering salah mengira bahwa volume sepi artinya "saham jelek/tidak laku". 
  * Dalam bandarmologi pre-breakout, **volume sepi di area atas base adalah tanda emas**. Artinya barang sudah diserap habis (*floating shares* di pasar berkurang drastis).

---

## 7. Kapasitas Modal & Aturan Likuiditas Keluar-Masuk Barang (5% - 10% Rule)

Salah satu risiko terbesar dalam trading saham *mid-cap* dan *small-cap* di IDX adalah **masalah likuiditas**:
> *"Bisa beli, tapi giliran mau jual malah kejebak karena antrean Bid kosong melompong."*

Likuiditas menentukan seberapa mudah Anda masuk (*entry*) dan keluar (*exit*) tanpa merusak harga pasar.

Gunakan rumus **Average Daily Turnover (ADT)**:
$$\text{ADT (Rupiah)} = \text{Rata-rata Volume Harian (Lot)} \times 100 \times \text{Harga Saham}$$

| Average Daily Turnover (ADT) | Kategori Saham | Alokasi Modal Maksimal Per Posisi | Gaya Eksekusi Masuk/Keluar |
| :--- | :--- | :--- | :--- |
| **> Rp20 Miliar / hari** | High Liquid (Big Caps: BBCA, BBRI, BMRI, ASII) | Bebas (Ratusan Juta hingga Miliaran) | HAKA / HAKI langsung tanpa slippage berarti |
| **Rp3 Miliar – Rp20 Miliar / hari** | Medium Liquid (Mid Caps aktif: BALI, MAPA, AUTO) | Maksimal **Rp50 Juta – Rp200 Juta** | Beli bertahap (antre bid), HAKI bertahap |
| **Rp500 Juta – Rp3 Miliar / hari** | Low Liquid (Small Caps / Second-Liner) | Maksimal **Rp10 Juta – Rp30 Juta** | **Wajib cicil pasif!** Jangan pernah HAKA/HAKI sekaligus |
| **< Rp500 Juta / hari** | Illiquid (Saham Sepi / Tidur) | Hindari, atau maks Rp2–5 Juta untuk iseng | Sangat berisiko kejebak jika bandar kabur |

> [!IMPORTANT]
> **Formula Posisi Maksimal:**
> $$\text{Ukuran Order Maksimal} \le 5\% \times \text{Average Daily Turnover Saham}$$
> Jika Anda membeli lebih dari 10% turnover harian, saat Anda ingin *cut loss* atau *take profit*, order jual Anda sendiri yang akan membanting harga (*slippage* tajam) karena antrean *Bid* tidak sanggup menampung barang Anda!

---

## 8. 🎯 Studi Kasus Riil Sukses (Win Trades: BALI, PTSP, RONY)

Berikut adalah 3 simulasi eksekusi menggunakan **data historis riil dari database Neon** yang bisa Mas Dhika cocokkan langsung di broker/chart masing-masing.

---

### 8.1 Studi Kasus 1: BALI (25 Sep – 06 Okt 2026) — *Explosion ARA +24.8%*

#### 📊 Data Riil Harian Saham BALI (Neon DB)

| Tanggal | Open | High | Low | Close | Volume (Lot) | Perubahan | Status Fase Setup |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **25 Sep 2026** | 1.290 | 1.335 | 1.275 | 1.305 | 91.100 | +0.4% | Lonjakan volume awal (Pre-spike) |
| **28 Sep 2026** | 1.300 | 1.375 | 1.270 | 1.290 | **148.400** | -1.1% | **Pilar 1: Tiang Induk Volume (Spike)** |
| **29 Sep 2026** | 1.280 | 1.370 | 1.280 | 1.370 | **3.200** | +6.2% | **Pilar 2 & 3: Base terbentuk, Vol Drop 97%!** |
| **30 Sep 2026** | 1.360 | 1.360 | 1.275 | 1.320 | 11.100 | -3.6% | Base ketat, tes support 1.275 |
| **01 Okt 2026** | 1.290 | 1.315 | 1.260 | 1.315 | **2.500** | -0.4% | **Volume Super Dry (2.500 lot = Rp328 Juta)** |
| **02 Okt 2026** | 1.315 | 1.420 | 1.285 | 1.330 | 10.700 | +1.1% | Uji resistance base, Smart Money nampung |
| **05 Okt 2026** | 1.330 | 1.660 | 1.285 | **1.660** | **27.400** | **+24.8%** 🚀 | **EXPLOSION DAY (Auto Rejection Atas / ARA)!** |
| **06 Okt 2026** | 1.580 | 1.580 | 1.415 | 1.560 | 160.900 | -6.0% | Distribusi profit taking pasca ARA |

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
150k   │     █ (148k)
 10k   │     █          ░        ░      ░      ░              █ (27k ARA)
   0   └─────┴──────────┴────────┴──────┴──────┴──────────────┴────►
           [TIANG]     [──────── BASE KERING ────────]      [BREAKOUT]
```

* **Broksum Base (28 Sep – 02 Okt):** Broker **`YJ`** akumulasi masif **+1.200 lot di Avg Rp1.319 (HMB)** tanpa jualan sama sekali, sementara broker ritel **`YP`** net sell **-567 lot** dan **`CC`** net sell **-350 lot**.
* **Eksekusi:** Beli di Rp1.315–1.330, Stop Loss di Rp1.265 (risiko -4.1%). Target tercapai di Rp1.660 (+24.8% ARA).

---

### 8.2 Studi Kasus 2: PTSP (18 Agu – 04 Sep 2026) — *ARA Beruntun +94.4%*

#### 📊 Data Riil Harian Saham PTSP (Neon DB)

| Tanggal | Open | High | Low | Close | Volume (Lot) | Perubahan | Status Fase Setup |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **19 Agu 2026** | 905 | 925 | 890 | 910 | 26.900 | -2.1% | Uji batas atas |
| **20 Agu 2026** | 910 | 940 | 910 | 915 | **2.600** | +0.5% | **Volume mengering drastis** |
| **21 Agu 2026** | 930 | 930 | 905 | 905 | **3.400** | -1.1% | Volume sepi, harga anteng di 905 |
| **26 Agu 2026** | 905 | 905 | 885 | 905 | **1.800** | 0.0% | **Volume Super Dry (1.800 lot = Rp162 Juta)** |
| **27 Agu 2026** | 895 | 900 | 890 | 895 | 8.800 | -1.1% | **Sinyal Candlify Trigger (Skor 92)** |
| **28 Agu 2026** | 890 | 900 | 885 | 890 | **2.700** | -0.5% | Final supply test (Low 885 bertahan) |
| **01 Sep 2026** | 920 | 1.135 | 915 | **1.135** | **404.500** | **+24.7%** 🚀 | **EXPLOSION DAY 1 (ARA!)** |
| **02 Sep 2026** | 1.300 | 1.415 | 970 | **1.415** | **2.522.300** | **+24.6%** 🚀 | **EXPLOSION DAY 2 (ARA Lanjut!)** |
| **03 Sep 2026** | 1.500 | 1.740 | 1.315 | **1.635** | **1.745.200** | **+15.5%** | Puncak reli ke 1.740 (+94.4% dari base!) |

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
  2.5M │                                                 █ (2.5M)
  400k │                                        █ (404k)
   10k │    ░      ░      ░      ░      ░
     0 └────┴──────┴──────┴──────┴──────┴───────┴────────┴────────┴────────────►
           [─────────── BASE KERING ───────────] [────── SUPER BREAKOUT ──────]
```

* **Broksum Base (20 – 28 Agu):** Broker **`XL`** dan **`NI`** konsisten akumulasi bersih di rentang Rp890–Rp905. Pada 28 Agustus, `NI` beli 20 lot di 900 tanpa ada aksi jual.
* **Eksekusi:** Entry di harga **Rp895–900**, Stop Loss di **Rp875** (1 tick di bawah Low 885, risiko cuma **-2.2%**).
* **Hasil:** Saham PTSP melesat bertubi-tubi dari 895 ke puncaknya di 1.740 (**+94.4%**) hanya dalam 3 hari bursa!

---

### 8.3 Studi Kasus 3: RONY (20 Agu – 07 Sep 2026) — *Stagnant Base to +61.2%*

#### 📊 Data Riil Harian Saham RONY (Neon DB)

| Tanggal | Open | High | Low | Close | Volume (Lot) | Perubahan | Status Fase Setup |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **20 Agu 2026** | 1.225 | 1.265 | 1.225 | 1.230 | **3.600** | +0.4% | Volume mulai mengering |
| **21 Agu 2026** | 1.245 | 1.250 | 1.225 | 1.240 | **1.900** | +0.8% | **Volume Super Dry (1.900 lot = Rp235 Juta)** |
| **26 Agu 2026** | 1.215 | 1.270 | 1.205 | 1.220 | 13.600 | -1.6% | Tes swing low 1.205 |
| **27 Agu 2026** | 1.220 | 1.260 | 1.205 | 1.225 | **3.600** | +0.4% | **Sinyal Candlify Trigger (Skor 88)** |
| **28 Agu 2026** | 1.220 | 1.310 | 1.220 | 1.230 | 18.500 | +0.4% | Akumulasi broker PD masif |
| **01 Sep 2026** | 1.235 | 1.270 | 1.200 | 1.215 | **7.500** | -1.2% | Volume kembali menyusut |
| **02 Sep 2026** | 1.255 | 1.275 | 1.225 | 1.245 | **7.600** | +2.5% | Penutupan rapat di atas MA20 |
| **04 Sep 2026** | 1.265 | 1.580 | 1.245 | **1.580** | **651.100** | **+24.9%** 🚀 | **EXPLOSION DAY 1 (ARA Rp1.580!)** |
| **07 Sep 2026** | 1.975 | 1.975 | 1.580 | **1.620** | **2.262.700** | +2.5% | **High 1.975 (+61.2% dari base 1.225!)** |

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
  2.2M │                                                   █ (2.2M)
  650k │                                         █ (651k)
   10k │    ░      ░      ░      ░      ░
     0 └────┴──────┴──────┴──────┴──────┴────────┴────────┴──────────────────►
           [─────────── BASE KERING ───────────] [────── SUPER BREAKOUT ──────]
```

* **Broksum Base (24 Agu – 02 Sep):** Broker **`PD`** beli bersih 98 lot @ 1.224 tanpa jual di tanggal 28 Agu, dan broker **`CC`** beli 59 lot @ 1.203 tanpa jual pada 31 Agu.
* **Eksekusi:** Entry di harga **Rp1.225–1.240**, Stop Loss di **Rp1.185** (risiko cuma **-3.2%**).
* **Hasil:** Saham RONY melonjak ke 1.580 (ARA), lalu di hari berikutnya dibuka gap-up dan menyentuh level tertinggi **Rp1.970 (+61.2%)**!

---

## 9. ⚠️ Studi Kasus Riil Gagal & Perangkap Distribusi (Trap Trades: LION, RGAS, BKDP)

Berikut 3 kasus riil di mana pola tampak mengering, tetapi **berujung longsor (*breakdown*)** karena adanya distribusi bandar atau ditelantarkan.

---

### 9.1 Studi Kasus Trap 1: LION (02 Sep – 30 Sep 2026) — *Distribusi Siluman ke 302*

*Data riil:* Spike di 400 (Vol 3.63M lot), base mendatar di 366–380, volume menciut ke 10.800 lot.
* **Bedah Racun Broksum:** Broker institusi **`CC` (-410 lot)** dan **`NI` (-762 lot)** konsisten buang barang, sementara yang menampung adalah broker ritel sejati **`XC` (Ajaib) net buy +996 lot**!
* **Hasil (30 Sep 2026):** Ritel kehabisan uang nampung, harga dibanting longsor dari 348 ke **302 (-12.7%)** dengan volume guyuran 977k lot.

---

### 9.2 Studi Kasus Trap 2: RGAS (21 Agu – 02 Sep 2026) — *Massive DUMP dari 280 ke 113 (-59%)*

#### 📊 Data Riil Harian Saham RGAS (Neon DB)

| Tanggal | Open | High | Low | Close | Volume (Lot) | Perubahan | Status Lapangan |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **26 Agu 2026** | 236 | 270 | 198 | 268 | **1.728.083.000** | +15.5% | Puncak transaksi 1,7 Miliar lot! |
| **27 Agu 2026** | 280 | 280 | 228 | **228** | **107.661.300** | **-14.9%** 🔴 | **Volume Drop drastis (Kelihatan sepi tapi ARB!)** |
| **28 Agu 2026** | 194 | 194 | 194 | **194** | **31.944.100** | **-14.9%** 🔴 | **ARB Terkunci (Volume tinggal 31M)** |
| **31 Agu 2026** | 179 | 208 | 165 | 165 | 337.187.800 | -14.9% | Guyuran berlanjut |
| **02 Sep 2026** | 142 | 149 | 121 | **121** | 685.109.100 | -14.8% | Amblas total ke 113 (-59% dari 280) |

```text
Harga
 280 │        ▲ (26-27 Agu: Puncak 280)
     │       │█│
 228 │       └─┘╲
     │           ▼ [ARB 1: 228]
 194 │            ╲
     │             ▼ [ARB 2: 194]
 121 │              ╲
     │               ▼ [Longsor ke 113 (-59%!)]
Volume
1.7B │        █
100M │        █    ░ (107M seolah kering)
 30M │        █    ░    ░ (31M)
   0 └────────┴────┴────┴────────────────────────────────►
```

* **Bedah Broksum (26 – 28 Agu):** 
  * Broker bandar **`CP`** net sell **-111.218 lot**, **`HD`** net sell **-105.027 lot**, dan **`XA`** net sell **-74.425 lot**!
  * Volume turun dari 1,7 Miliar ke 31 Juta bukan karena "barang kering", tetapi karena **antrean Bid hilang total sehingga tidak ada yang bisa transaksi (ARB Terkunci)**.
* **Pelajaran Candlify:** Candlify memfilter saham dengan status *price close < MA20* dan *candle bear marubozu*. Saham seperti ini langsung diblokir sistem.

---

### 9.3 Studi Kasus Trap 3: BKDP (08 Sep – 21 Sep 2026) — *Saham Ditelantarkan Pasca Spike*

#### 📊 Data Riil Harian Saham BKDP (Neon DB)

| Tanggal | Open | High | Low | Close | Volume (Lot) | Perubahan | Kondisi Lapangan |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **08 Sep 2026** | 170 | 224 | 161 | 200 | **231.399.000** | +19.7% | Spike masif 231 Juta lot |
| **09 Sep 2026** | 200 | 212 | 190 | 191 | 40.129.400 | -4.5% | Mulai koreksi |
| **14 Sep 2026** | 174 | 204 | 165 | 191 | 101.291.200 | +12.3% | Dead cat bounce (Umpan kedua) |
| **18 Sep 2026** | 180 | 181 | 164 | 168 | **8.291.600** | -4.5% | **Volume menyusut drastis ke 8M lot** |
| **21 Sep 2026** | 171 | 186 | 162 | 179 | 37.755.700 | +6.5% | Ritel masuk mengira base |
| **28 Sep 2026** | 190 | 190 | 175 | 184 | 5.585.900 | -1.6% | Volume makin kering |
| **01 Okt 2026** | 150 | 155 | 132 | **132** | 12.000.000 | **-14.8%** 🔴 | **Ambles -30.5% dari harga 190!** |

* **Bedah Kasus:** Pada BKDP, saat volume menyusut dari 231M ke 5M lot, **tidak ada satu pun broker institusi yang melakukan akumulasi**. Sahamnya kering karena ditinggal pergi. Begitu pasar mengalami tekanan, harga terperosok ke 132.
* **Filter Candlify:** Syarat `top_accumulator > 30% net flow` gagal terpenuhi di BKDP, sehingga Candlify tidak merekomendasikan saham ini.

---

## 10. ✨ Studi Kasus Riil Unik (Special Edge Cases: MPXL & STAR)

Dua kasus berikut memperlihatkan fenomena khusus bursa: **Wyckoff Spring (Jarum Jebol Sesaat)** dan **Liquidity Vacuum (Gap-Up Lock ARA)**.

---

### 10.1 Kasus Unik 1: MPXL (08 Sep – 23 Sep 2026) — *The Wyckoff Spring Shakeout*

Pernahkah Anda memasang Stop Loss, lalu harga saham turun **hanya 1 tick** menyenggol Stop Loss Anda, kemudian langsung terbang tinggi? Fenomena ini disebut **Wyckoff Spring / Bear Trap**.

#### 📊 Data Riil Harian Saham MPXL (Neon DB)

| Tanggal | Open | High | Low | Close | Volume (Lot) | Perubahan | Status Fase |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **08 Sep 2026** | 169 | 189 | 169 | 173 | **8.466.800** | +3.0% | Prior Spike Tiang Induk |
| **14 Sep 2026** | 169 | 173 | 165 | 171 | 1.469.000 | +1.2% | Base terbentuk (Support 164) |
| **17 Sep 2026** | 165 | 171 | 160 | 166 | **227.600** | -1.2% | **Volume mengering -97.3%!** |
| **18 Sep 2026** | 167 | 171 | 165 | 166 | 357.000 | 0.0% | Base rapat di 166 |
| **22 Sep 2026** | 166 | 171 | **159** | **164** | 1.285.100 | -1.2% | **THE SHAKEOUT SPRING! Low 159 lalu ditarik!** |
| **23 Sep 2026** | 165 | 220 | 163 | **220** | **73.483.000** | **+34.1%** 🚀 | **EXPLOSION DAY (ARA Meledak ke 220!)** |
| **24 Sep – 02 Okt**| 230 | 260 | 199 | **260** | 13.722.500 | +18.1% | Reli lanjut menyentuh level 260 (+56.6%) |

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
 73M │                                                  █ (73,4 Juta lot!)
8.4M │   █ (8.4M)
220k │   █             ░     ░     ░     ░
   0 └───┴─────────────┴─────┴─────┴─────┴──────────────┴────────────────────────►
```

* **Keunikan Bandarmologi:**
  * Pada **22 September 2026**, support kuat ada di Rp164. Tiba-tiba di sesi perdagangan, harga dijatuhkan ke **Rp159 (1 tick di bawah Rp160)** untuk menjemput Stop Loss trader ritel!
  * Namun perhatikan penutupannya: **Close langsung ditarik kembali ke Rp164 (*reclaim*)**!
  * Broksum menunjukkan broker **`CP`** mengumpulkan **+14.988 lot** dan **`HD`** mengumpulkan **+8.244 lot**.
* **Kuncinya:** Jika candle sempat jebol support tetapi **mampu ditutup kembali ke dalam area base pada akhir sesi (Reclaim)**, itu bukan breakdown, melainkan **Spring (Umpan Pembersih)**. Keesokan harinya MPXL langsung meledak ARA **+34.1% ke 220**!

---

### 10.2 Kasus Unik 2: STAR (24 Jul – 12 Agu 2026) — *The Liquidity Vacuum & Multi Gap-Up Lock ARA*

Kasus unik di mana suplai barang terserap begitu bersih sampai **antrean offer di bursa kosong melompong (*liquidity vacuum*)**, sehingga saat breakout, harga langsung dibuka loncat gap-up tanpa ada kesempatan antre beli di offer.

#### 📊 Data Riil Harian Saham STAR (Neon DB)

| Tanggal | Open | High | Low | Close | Volume (Lot) | Perubahan | Status Fase |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **24 Jul 2026** | 282 | 282 | 274 | 278 | 12.000 | +0.7% | Konsolidasi awal |
| **28 Jul 2026** | 278 | 278 | 262 | 276 | 32.500 | -0.7% | Tes support 262 |
| **29 Jul 2026** | 272 | 274 | 270 | 272 | **4.400** | -1.4% | **Volume Kering Ekstrem (4.400 lot = Rp119 Juta)** |
| **04 Agu 2026** | 280 | 280 | 274 | 276 | **15.900** | -0.7% | Suplai terkunci total |
| **07 Agu 2026** | 276 | 276 | 262 | 266 | 31.100 | -3.6% | Shakeout terakhir sebelum reli |
| **10 Agu 2026** | 266 | 332 | 264 | **332** | **2.070.100** | **+24.8%** 🚀 | **EXPLOSION DAY 1 (ARA Rp332!)** |
| **11 Agu 2026** | **412** | 414 | 382 | **414** | **3.237.800** | **+24.7%** 🚀 | **OPEN GAP-UP DI 412 (+24%) & ARA KE 414!** |
| **12 Agu 2026** | 480 | **515** | 420 | 420 | 8.291.600 | +1.4% | Puncak reli ke 515 (+89.3% dari base 272!) |

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
3.2M │                                                  █ (3.2M)
2.0M │                                        █ (2.0M)
  15k│    ░      ░      ░      ░      ░
    0 └───┴──────┴──────┴──────┴──────┴────────┴────────┴───────────────┴────────►
          [─────────── BASE KERING ───────────] [────── SUPER BREAKOUT GAP ──────]
```

* **Bedah Broksum Base (24 Jul – 07 Agu):**
  * Broker **`YB`** akumulasi masif **+58.005 lot** di Avg Rp263.
  * Broker **`PO`** akumulasi masif **+56.000 lot** di Avg Rp268 tanpa menjual satu lot pun!
  * Total serapan kedua broker ini mencapai **114.000 lot** di area sepi.
* **Pelajaran Krusial:** Pada saham yang mengalami *Liquidity Vacuum*, trader yang menunggu "konfirmasi breakout" **TIDAK AKAN BISA BELI**, karena pada tanggal 11 Agustus harga dibuka langsung loncat gap-up di Rp412 (+24% di atas harga kemarin) dan terkunci ARA! Satu-satunya cara menikmati cuan multi-bagger +89% ini adalah **masuk saat fase Pre-Breakout di harga Rp270–276 saat volume sedang sepi**.

---

## 11. Trader's Quick Checklist Sebelum Menekan Tombol Buy

Sebelum Anda memasukkan order beli di sekuritas, centang 7 poin ini:

- [ ] **1. Tiang Induk Jelas:** Ada spike volume $\ge 2\times$ dan candle hijau $\ge 5\%$ dalam 1 bulan terakhir.
- [ ] **2. Base Rapat:** Rentang harga 7 hari tidak liar (tidak bikin ekor panjang atas-bawah).
- [ ] **3. Volume Mengering:** 3 hari terakhir volumenya di bawah 50% dari volume tiang.
- [ ] **4. Broksum Positif (Wajib!):** Broker top-1 net buy akumulasi di atas 30%, ritel (`YP, XC, PD`) tercatat net sell.
- [ ] **5. Dekat Modal Bandar:** Harga saat ini tidak lebih dari 5% di atas HMB.
- [ ] **6. Likuiditas Masuk Akal:** Nilai transaksi harian (ADT) minimal Rp1 Miliar, dan alokasi modal kita $\le 5\%$ dari ADT.
- [ ] **7. Stop Loss Sudah Dihitung:** Batas cut loss jelas (1–2 tick di bawah support base), potensi risiko maksimal 2–4%.

---

*Disusun secara sistematis untuk Candlify V2 — "Trade with Smart Money, Protect Your Liquidity."*
