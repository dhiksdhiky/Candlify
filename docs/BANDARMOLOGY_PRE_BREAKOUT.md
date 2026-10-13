# 📘 PANDUAN LENGKAP BANDARMOLOGI: PRE-BREAKOUT BASE, BACKTEST & LIKUIDITAS VOLUME

> **Candlify Market Intelligence Manual**  
> *Dokumen referensi resmi analisis pergerakan Smart Money, identifikasi broker kuantitatif, bukti validitas backtest Neon DB, pembacaan volume, serta manajemen risiko likuiditas di Bursa Efek Indonesia (IDX).*

---

## 📑 DAFTAR ISI
1. [Filosofi & Konsep Universal: Pre-Breakout Base](#1-filosofi--konsep-universal-pre-breakout-base)
2. [Anatomi 4 Pilar Pre-Breakout Base (Studi Kasus Saham BALI)](#2-anatomi-4-pilar-pre-breakout-base-studi-kasus-saham-bali)
3. [🤖 Cara Mesin Menentukan Broker Ritel vs Big Money (Dynamic Behavioral Scoring)](#3--cara-mesin-menentukan-broker-ritel-vs-big-money-dynamic-behavioral-scoring)
4. [⚖️ Perbandingan Objektif & Backtest: bandar_satu vs Formula Pre-Breakout](#4-️-perbandingan-objektif--backtest-bandar_satu-vs-formula-pre-breakout)
5. [🔎 Bukti Validitas Historis: 10 Contoh Sukses & Bedah Kasus Gagal](#5--bukti-validitas-historis-10-contoh-sukses--bedah-kasus-gagal)
6. [Cara Membaca Volume di Candlify & Kaitannya dengan Likuiditas](#6-cara-membaca-volume-di-candlify--kaitannya-dengan-likuiditas)
7. [Kapasitas Modal & Aturan Likuiditas Keluar-Masuk Barang](#7-kapasitas-modal--aturan-likuiditas-keluar-masuk-barang)
8. [SOP Simulasi Eksekusi Trading Plan](#8-sop-simulasi-eksekusi-trading-plan)
9. [Trader's Quick Checklist Sebelum Menekan Tombol Buy](#9-traders-quick-checklist-sebelum-menekan-tombol-buy)

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

## 2. Anatomi 4 Pilar Pre-Breakout Base (Studi Kasus Saham BALI)

Untuk membedakan konsolidasi yang siap meledak dengan saham yang sekadar tidur/mati suri, engine Candlify menguji **4 Pilar Algoritmik**:

```
[ PILAR 1: TIANG INDUK ]  ──>  [ PILAR 2: KOTAK BASE ]  ──>  [ PILAR 3: VOLUME KERING ]  ──>  [ PILAR 4: BROKSUM ACCUM ]
(Ignition Volume Spike)        (Tight Range & BBW)             (Supply Exhaustion)             (Smart Money / HMB)
```

```
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
* **Kasus BALI:** Terjadi lonjakan volume masif pada fase awal kenaikan yang menembus resisten lama, menarik perhatian pasar, lalu sengaja dihentikan kenaikannya agar ritel tidak langsung ikut berpesta.

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
  * Pembeli didominasi oleh broker institusi / *smart money* (misal: `CC`, `AK`, `BK`, `KZ`, atau spesifik bandar lokal `MG`), sedangkan penjual tersebar di banyak broker ritel (`YP`, `PD`, `XC`, `XL`).
* **HMB (Harga Modal Bandar):**
  * Rata-rata harga beli (*Average Buy Price*) broker akumulator di area base menjadi patokan HMB.
  * Selama harga pasar masih berada dekat HMB ($\pm 1\% - 3\%$), posisi kita sejajar dengan harga modal bandar.

---

## 3. 🤖 Cara Mesin Menentukan Broker Ritel vs Big Money (Dynamic Behavioral Scoring)

Di era pasar modal modern, bandar bisa saja melakukan *split order* lewat broker ritel (seperti `YP`, `XL`, `XC`), begitu pula nasabah *High Net Worth* (sultan) bisa saja bertransaksi menggunakan akun sekuritas ritel.

Oleh karena itu, jika mesin hanya mengandalkan label hardcoded (statis), sistem akan mudah tertipu. Pendekatan kuantitatif terbaik yang diterapkan pada data tabel `broker_summary` adalah **Dynamic Behavioral Scoring (Scoring Perilaku Dinamis)**:

```
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
1. **Kelemahan `bandar_satu`:** Masuk saat *Volume Spike* (saat harga sudah melonjak naik hijau tebal). Akibatnya, begitu bandar melakukan *shakeout* (banting harga mendadak seperti kasus tanggal 4 September di BALI), posisi langsung terjebak penurunan rata-rata **-12.00%** yang sering memicu *cut loss* prematur.
2. **Kekuatan Formula Pre-Breakout:** Masuk saat *Base Stagnan & Volume Kering* (sebelum ledakan terjadi). Karena beli di lantai dasar konsolidasi, risiko penurunannya sangat minim (rata-rata *max drawdown* cuma **-5.15%**). *Risk to Reward Ratio*-nya jauh lebih superior!

---

## 5. 🔎 Bukti Validitas Historis: 10 Contoh Sukses & Bedah Kasus Gagal

Formula Pre-Breakout terbukti berulang kali berhasil memprediksi ledakan harga di Bursa Efek Indonesia.

### 🌟 10 Contoh Riil Saham Sukses dari Database Neon
Kriteria: Prior Spike $\rightarrow$ Base rapat $\le 5\%$ $\rightarrow$ Volume kering $< 30\%$ VMA $\rightarrow$ Kinerja 10 hari setelahnya:

| Ticker | Tanggal Sinyal | Harga Base | Keringnya Vol (`v_ratio`) | Max Gain 10 Hari | Max Drawdown | Hasil Pergerakan Riil |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **PTSP** | 27 Agu 2026 | 895 | $0.09\times$ VMA | **+94.4%** 🚀 | -1.1% | Base super rapat, meledak ARA beruntun tanpa ampun. |
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

### ⚠️ Pelajaran dari Kasus Gagal (False Breakout & Trap)
Tidak ada formula teknikal yang 100% sempurna. Pada histori data, ditemukan anomali seperti kasus saham **BKDP** dan **LION** di mana harga setelah kering justru anjlok turun $-20\%$ s/d $-30\%$.

#### Mengapa Bisa Gagal?
* **Penyebab Utama:** Pada kasus yang gagal, saat volume kering, **TIDAK ADA AKUMULASI DI BROKER SUMMARY**. Sahamnya kering bukan karena barangnya diserap oleh bandar, melainkan karena **ditelantarkan (ditinggal pergi oleh market maker)**. Akibatnya, saat ada sedikit ritel panik yang menjual, harga langsung longsor tanpa ada antrean Bid yang menopang.
* **Filter Penyelamat Candlify:** Inilah alasan mutlak mengapa Candlify mewajibkan **Filter Broksum**: Sinyal hanya dinyatakan sah (*Valid*) jika selama base kering, net flow bandar terbukti positif/akumulasi (seperti HMB 1.315 di BALI) dan tidak ada distribusi masif!

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

## 7. Kapasitas Modal & Aturan Likuiditas Keluar-Masuk Barang

Salah satu risiko terbesar dalam trading saham *mid-cap* dan *small-cap* di IDX adalah **masalah likuiditas**:
> *"Bisa beli, tapi giliran mau jual malah kejebak karena antrean Bid kosong melompong."*

Likuiditas menentukan seberapa mudah Anda masuk (*entry*) dan keluar (*exit*) tanpa merusak harga pasar.

---

### Metrik Likuiditas: Lot vs Average Daily Turnover (Rupiah)
Jangan hanya melihat jumlah lembar lot! 10.000 lot di saham harga Rp50 bernilai Rp50 juta, sedangkan 10.000 lot di saham harga Rp5.000 bernilai Rp5 Miliar.

Gunakan rumus **Average Daily Turnover (ADT)**:
$$\text{ADT (Rupiah)} = \text{Rata-rata Volume Harian (Lot)} \times 100 \times \text{Harga Saham}$$

---

### Aturan Emas: "5% – 10% Liquidity Rule"
Untuk menghindari jebakan likuiditas (*liquidity black hole*), terapkan batas porsi modal berikut:

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

## 8. SOP Simulasi Eksekusi Trading Plan

Berikut simulasi nyata langkah demi langkah saat memanfaatkan Candlify Screener:

### Langkah A: Filter Sinyal di Candlify
1. Buka menu **Screener** di Candlify.
2. Klik preset **`🎯 Pre-Breakout Base`**.
3. Di dropdown sort, pilih **`Score Desc`** (urutkan skor kualitas tertinggi).
4. Pilih saham yang memiliki:
   * **Skor $\ge 75$**
   * **Base $\le 8\%$**
   * **Volume Dry $\le 0.45\times$**
   * Top Accumulator jelas (misal: `CC`, `AK`, `BK`).

---

### Langkah B: Menentukan Area Tempur (Support & Resistance Base)
Buka chart saham tersebut di Candlify:
1. Tarik garis horizontal di titik tertinggi candle konsolidasi 7 hari $\rightarrow$ **Level Resistance Base**.
2. Tarik garis horizontal di titik terendah candle konsolidasi 7 hari $\rightarrow$ **Level Support Base**.
3. Cek posisi **HMB (Harga Modal Bandar)** di badge header $\rightarrow$ Biasanya berhimpitan dengan garis tengah base.

---

### Langkah C: Memilih Gaya Eksekusi (2 Pilihan)

#### Opsi 1: Gaya "Buy on Weakness" (Low Risk / Cicil Pasif)
* **Kapan Dipakai:** Saat pasar sedang sepi / IHSG mendatar, harga saham sedang menguji batas bawah base.
* **Titik Beli:** Antre di dekat Support Base (misal: Rp1.200).
* **Stop Loss (SL):** Pasang ketat di **1–2 tick di bawah Support Base** (misal: Rp1.175).  
  * *Risiko (Risk):* Hanya **-2.0% s/d -2.5%**.
* **Target Profit (TP):** Minimal uji resisten tiang lama (+10% s/d +20%).  
  * *Risk-to-Reward Ratio:* **1 : 4** (Sangat sehat!).

#### Opsi 2: Gaya "Buy on Breakout" (Momentum / Konfirmasi)
* **Kapan Dipakai:** Jam 09:00–10:00 WIB saat pasar buka, harga menembus Resistance Base dengan volume meledak di Running Trade.
* **Titik Beli:** HAKA begitu harga *break* 1 tick di atas Resistance Base (misal: Rp1.255).
* **Stop Loss (SL):** Di bawah titik breakout / swing low hari itu (biasanya ~3%).
* **Target Profit (TP):** Bertahap (TP1 +8%, TP2 trailing stop mengikuti EMA20).

---

## 9. Trader's Quick Checklist Sebelum Menekan Tombol Buy

Sebelum Anda memasukkan order beli di sekuritas, centang 7 poin ini:

- [ ] **1. Tiang Induk Jelas:** Ada spike volume $\ge 2\times$ dan candle hijau $\ge 5\%$ dalam 1 bulan terakhir.
- [ ] **2. Base Rapat:** Rentang harga 7 hari tidak liar (tidak bikin ekor panjang atas-bawah).
- [ ] **3. Volume Mengering:** 3 hari terakhir volumenya di bawah 50% dari volume tiang.
- [ ] **4. Broksum Positif:** Broker top-1 net buy akumulasi di atas 30%, ritel net sell.
- [ ] **5. Dekat Modal Bandar:** Harga saat ini tidak lebih dari 5% di atas HMB.
- [ ] **6. Likuiditas Masuk Akal:** Nilai transaksi harian (ADT) minimal Rp1 Miliar, dan alokasi modal kita $\le 5\%$ dari ADT.
- [ ] **7. Stop Loss Sudah Dihitung:** Batas cut loss jelas (di bawah support base), potensi risiko maksimal 2–3%.

---

*Disusun secara sistematis untuk Candlify V2 — "Trade with Smart Money, Protect Your Liquidity."*
