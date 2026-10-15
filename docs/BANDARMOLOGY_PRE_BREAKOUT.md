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
8. [🎯 Simulasi Riil Langkah-demi-Langkah (Studi Kasus Sukses: BALI)](#8--simulasi-riil-langkah-demi-langkah-studi-kasus-sukses-bali)
9. [⚠️ Simulasi Riil Kasus Gagal & Perangkap Distribusi (Studi Kasus Trap: LION)](#9-️-simulasi-riil-kasus-gagal--perangkap-distribusi-studi-kasus-trap-lion)
10. [Trader's Quick Checklist Sebelum Menekan Tombol Buy](#10-traders-quick-checklist-sebelum-menekan-tombol-buy)

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

## 8. 🎯 Simulasi Riil Langkah-demi-Langkah (Studi Kasus Sukses: BALI)

Berikut adalah simulasi eksekusi menggunakan **data historis riil saham PT Bali Towerindo Sentra Tbk. (BALI)** yang tersimpan di Neon Database (periode 25 September – 06 Oktober 2026). Mas Dhika bisa langsung membuka chart sekuritas (Stockbit/IPOT) untuk mencocokkan setiap baris angka ini.

### 📊 Data Riil Harian Saham BALI (Neon DB)

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

---

### 🎨 Visualisasi Chart & Langkah Eksekusi BALI

```text
Harga
 1.700 │                                                 [C=1.660 ARA!]
       │                                                       ▲
 1.600 │                                                       │
       │                                                       │
 1.500 │
       │
 1.400 │              ┌─────────── Resistance Base: 1.370 ────┬┘
       │     ▲        │  ┌─┐                                  │
 1.300 │    │█│       │  │ │    ┌─┐    ┌─┐    ┌─┐             │
       │    │█│       │  └─┘    │█│    │ │    │ │             │
 1.200 │  ──┴─┴───────┴─────────└─┴────┴─┴────┴─┴─────────────┴─  <-- Support Base: 1.275
       │   28 Sep     29 Sep   30 Sep 01 Okt 02 Okt         05 Okt
Volume │
150k   │     █ (148k)
       │     █
 10k   │     █          ░        ░      ░      ░              █ (27k ARA)
   0   └─────┴──────────┴────────┴──────┴──────┴──────────────┴────►
           [TIANG]     [──────── BASE KERING ────────]      [BREAKOUT]
```

---

### Langkah 1: Deteksi Tiang Induk (28 September 2026)
* **Kondisi:** Saham BALI mencetak volume **148.400 lot** (senilai ~Rp19,5 Miliar), menembus rata-rata volume hariannya yang biasanya hanya 5.000–10.000 lot.
* **Tindakan Trader:** Jangan FOMO langsung HAKA! Masukkan ticker BALI ke dalam **Watchlist Radar**.

---

### Langkah 2: Mengamati Pengeringan Volume & Base (29 Sep – 02 Okt 2026)
* **Kondisi:** 
  * Volume 29 September anjlok drastis ke **3.200 lot** (turun $-97.8\%$ dari volume tiang!).
  * Volume 01 Oktober bahkan menyusut ke **2.500 lot**!
  * Harga bergerak sangat tenang di dalam kotak: **Support Base Rp1.275** dan **Resistance Base Rp1.370** (Rentang sempit $\le 7.4\%$).
* **Makna Bandarmologi:** Penjual sudah habis (*exhausted*). Tidak ada yang mau melepas barang di bawah Rp1.275.

---

### Langkah 3: Verifikasi Broker Summary (Neon DB Broksum 28 Sep – 02 Okt)
Buka tab Broksum di Candlify untuk rentang tanggal base:

| Kode Broker | Kategori Broker | Total Beli (Lot) | Buy Avg | Total Jual (Lot) | Sell Avg | Net Flow (Lot) | Status Bandarmologi |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`YJ`** | Bandar / Institusi | 1.200 | Rp1.319 | 0 | - | **+1.200 lot** | **Lead Accumulator (HMB Rp1.319)** |
| **`YU`** | Institusi | 150 | Rp1.333 | 150 | Rp1.300 | Netral | Tektokan penyeimbang |
| **`NI`** | Institusi | 127 | Rp1.307 | 198 | Rp1.328 | -71 lot | Distribusi kecil |
| **`YP`** | **Ritel Sejati** | 3 | Rp1.280 | 570 | Rp1.310 | **-567 lot** | **Ritel Buang Barang (Net Sell)** |
| **`CC`** | Campuran / Ritel | 26 | Rp1.323 | 376 | Rp1.324 | **-350 lot** | Ritel Cut Loss / Exit |

> [!NOTE]
> **Kesimpulan Broksum:** Jelas sekali terjadi **akumulasi bersih oleh broker `YJ`** di harga rata-rata **Rp1.319 (HMB)**, sementara broker ritel `YP` dan `CC` ramai-ramai buang barang karena bosan melihat harga stagnan!

---

### Langkah 4: Eksekusi Trading Plan (02 Oktober 2026 Sore)
* **Area Beli (Entry):** Antre beli di harga **Rp1.315 – Rp1.330** (sejajar dengan HMB bandar Rp1.319).
* **Stop Loss (SL):** Pasang ketat di **Rp1.265** (2 tick di bawah Support Base Rp1.275).  
  $$\text{Risiko Kerugian (Risk)} = \frac{1.320 - 1.265}{1.320} = \mathbf{-4.1\%}$$
* **Target Profit (TP):** Minimal menguji titik tertinggi tiang sebelumnya di **Rp1.550 – Rp1.660** ($+17\% \text{ s/d } +25\%$).  
  $$\text{Risk to Reward Ratio} = \frac{+25\%}{4.1\%} = \mathbf{1 : 6.1} \quad (\text{Super Menjanjikan!})$$

---

### Langkah 5: Panen Hasil (05 Oktober 2026)
Pada hari Senin 05 Oktober 2026, bandar hanya butuh volume kecil (27.400 lot) untuk mengunci harga saham BALI langsung **Auto Rejection Atas (ARA) di Rp1.660 (+24.8%)**! 
* Trader yang masuk di Rp1.320 membukukan profit bersih **+25.7%** hanya dalam 1 hari bursa dengan risiko awal yang sangat terkontrol.

---

## 9. ⚠️ Simulasi Riil Kasus Gagal & Perangkap Distribusi (Studi Kasus Trap: LION)

Agar seimbang dan objektif, mari bedah kasus di mana saham tampak membentuk *base sempit dan volume kering*, tetapi akhirnya **gagal (*breakdown*)**. Ini adalah data riil saham **PT Lion Metal Works Tbk. (LION)** periode September 2026.

### 📊 Data Riil Harian Saham LION (Neon DB)

| Tanggal | Open | High | Low | Close | Volume (Lot) | Perubahan | Kondisi Lapangan |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **02 Sep 2026** | 360 | 442 | 352 | 400 | **3.639.600** | +13.6% | Volume Spike raksasa (Umpan awal) |
| **07 Sep 2026** | 386 | 460 | 380 | 382 | 1.552.800 | -1.0% | Jarum atas panjang (Upper shadow rejection) |
| **15 Sep 2026** | 366 | 374 | 366 | 368 | **10.800** | +0.5% | Volume anjlok 99% (Kelihatan seperti volume dry) |
| **21 Sep 2026** | 370 | 380 | 364 | 378 | 91.300 | +2.1% | Tampak konsolidasi rapi di 364 - 380 |
| **28 Sep 2026** | 366 | 366 | 330 | 344 | **26.400** | -6.0% | Support 358 mulai dijebol tipis |
| **29 Sep 2026** | 344 | 348 | 344 | 346 | **26.000** | +0.5% | Pantulan lemah (Dead cat bounce) |
| **30 Sep 2026** | 348 | 362 | 300 | **302** | **977.300** | **-12.7%** 🔴 | **COLLAPSE! Longsor dijebol ke bawah!** |

---

### 🎨 Visualisasi Jebakan Distribusi LION

```text
Harga
 460 │                ▲
     │               │█│ (Upper shadow panjang - 07 Sep)
 400 │    ▲          └─┘
     │   │█│
 380 │   │█│   ┌──────────────┐  <-- Base Semu (Harga mendatar seolah aman)
     │   │█│   │ ░ ░ ░ ░ ░ ░  │
 350 │  ─┴─┴───┴──────────────┴──  <-- Support Base Krusial (358)
     │                             ╲
 300 │                              ▼ [C=302 LONGSOR JEBOL!] (30 Sep)
Volume
3.6M │    █
     │    █
 20k │    █       ░   ░   ░   ░     █ (977k Guyuran)
   0 └────┴───────┴───┴───┴───┴─────┴────────────────────────►
        [SPIKE]   [BASE JEBAKAN]   [BREAKDOWN]
```

---

### 🔍 Bedah Racun: Kenapa Saham LION Gagal?
Bagi trader yang hanya membaca chart teknikal tanpa Bandarmologi, LION pada tanggal 15–25 September tampak seperti setup sempurna: *Ada spike $\rightarrow$ Harga mendatar $\rightarrow$ Volume mengering*.

Namun, mari kita bongkar **Data Broker Summary LION** pada tanggal 21–23 September 2026 dari Neon DB:

| Kode Broker | Peran Broker | Total Beli | Total Jual | Net Flow | Analisis Perilaku (*Behavioral Analysis*) |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **`CC`** | Bandar / Institusi | 176 lot | 586 lot | **-410 lot (NET SELL)** | **Bandar buang barang diam-diam!** |
| **`NI`** | Bandar / Institusi | 100 lot | 862 lot | **-762 lot (NET SELL)** | **Bandar distribusi besar-besaran!** |
| **`XL`** | Sekuritas Ritel/Campuran | 97 lot | 527 lot | **-430 lot (NET SELL)** | Distribusi lanjutan |
| **`XC`** | **Ritel Sejati (Ajaib)** | 1.039 lot | 43 lot | **+996 lot (NET BUY)** | **Ritel menampung guyuran bandar!** |

> [!WARNING]
> **Kebenaran yang Terungkap:**
> Volume di saham LION mengering **BUKAN karena barang diserap bandar**, melainkan karena **sahamnya DITELANTARKAN (*abandoned*)** setelah bandar selesai jualan ke ritel (`XC`). Ketika ritel kehabisan uang untuk menampung, pada tanggal 30 September harga langsung dijatuhkan dari 348 ke 302 (-12.7%)!

---

### 🛡️ Bagaimana Candlify Menyelamatkan Portofolio Anda?

1. **Filter Broksum Candlify Menolak Sinyal LION:**  
   Algoritma Candlify di `scanner_bali.py` memeriksa pilar akumulasi. Karena top buyer di LION adalah broker ritel (`XC`) dan institusi justru *net sell*, skor sinyal LION langsung di-drop menjadi **< 40**, sehingga saham ini **TIDAK AKAN PERNAH LOLOS** ke dalam rekomendasi Screener Candlify.
2. **Disiplin Cut Loss Membatasi Kerugian:**  
   Seandainya trader tetap nekat masuk di harga Rp366:
   * Level Support Base adalah **Rp358**.
   * Ketika pada tanggal 28 September harga ditutup di Rp344 (jebol support), SOP Candlify mewajibkan **Cut Loss langsung**.
   * Kerugian yang dialami hanya **-3.5%**. Trader terhindar dari malapetaka longsor ke harga Rp302 (-17.5% kerugian lebih dalam).

---

## 10. Trader's Quick Checklist Sebelum Menekan Tombol Buy

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
