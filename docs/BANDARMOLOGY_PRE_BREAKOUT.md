# 📘 PANDUAN LENGKAP BANDARMOLOGI: PRE-BREAKOUT BASE & ANALISA VOLUME LIKUIDITAS

> **Candlify Market Intelligence Manual**  
> *Dokumen referensi resmi untuk analisis pergerakan Smart Money, struktur konsolidasi ketat, pembacaan volume, serta manajemen risiko likuiditas di Bursa Efek Indonesia (IDX).*

---

## 📑 DAFTAR ISI
1. [Filosofi & Konsep Universal: Pre-Breakout Base](#1-filosofi--konsep-universal-pre-breakout-base)
2. [Anatomi 4 Pilar Pre-Breakout Base (Studi Kasus Saham BALI)](#2-anatomi-4-pilar-pre-breakout-base-studi-kasus-saham-bali)
3. [Cara Membaca Volume di Candlify & Kaitannya dengan Likuiditas](#3-cara-membaca-volume-di-candlify--kaitannya-dengan-likuiditas)
4. [Kapasitas Modal & Aturan Likuiditas Keluar-Masuk Barang](#4-kapasitas-modal--aturan-likuiditas-keluar-masuk-barang)
5. [SOP Simulasi Eksekusi Trading Plan](#5-sop-simulasi-eksekusi-trading-plan)
6. [Trader's Quick Checklist Sebelum Menekan Tombol Buy](#6-traders-quick-checklist-sebelum-menekan-tombol-buy)

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

---

### Pilar 1: Prior Ignition Spike (Tiang Induk)
* **Karakteristik:** Terjadi 4 sampai 28 hari bursa sebelumnya. Ditandai oleh candle hijau solid ($\ge +5\%$) dengan lonjakan volume $\ge 2.0\times$ Volume MA20.
* **Makna Bandarmologi:** Ini adalah **jejak modal pertama (*liquidity injection*)**. Bandar menunjukkan taringnya bahwa mereka telah menyuntikkan likuiditas dan memiliki kepentingan di saham ini.
* **Kasus BALI:** Terjadi lonjakan volume masif pada fase awal kenaikan yang menembus resisten lama, menarik perhatian pasar, lalu sengaja dihentikan kenaikannya agar ritel tidak langsung ikut berpesta.

---

### Pilar 2: Volatility Contraction / Tight Base (Kotak Base)
* **Karakteristik:** 
  * Rentang harga 7 hari bursa (`range_7`) sangat rapat: **$\le 8\% - 12\%$**.
  * Indikator *Bollinger Band Width (BBW)* menyempit drastis: **$\le 14\%$**.
  * Posisi harga bertahan di atas atau dekat garis MA20 (`price_to_ma20 >= -4%`), menandakan harga ditahan di separuh atas tiang induk (tidak dibiarkan roboh ke dasar).
* **Makna Bandarmologi:** Volatilitas yang menurun tajam membuktikan bahwa pertarungan harga sudah terkontrol. Bandar sengaja menjaga rentang harga sempit (*range-bound*) agar ritel yang tidak sabar merasa bosan lalu menjual sahamnya.

---

### Pilar 3: Volume Dry-Up (Volume Mengering)
* **Karakteristik:** 
  * Volume harian saat konsolidasi menciut menjadi **$\le 0.40\times - 0.50\times$** dari volume rata-rata atau tiang induk.
* **Makna Bandarmologi:** Ini adalah pilar paling krusial!
  * **Volume Kering = Tidak Ada Tekanan Jual (*Supply Depleted*)**. 
  * Jika bandar mau buang barang (*distribusi*), volume pasti besar dan harga rontok. 
  * Namun, jika harga diam mendatar DAN volume sepi seperti kuburan, artinya **barang sudah terkunci di tangan bandar** dan tidak ada lagi ritel yang bersedia menjual murah. Untuk menaikkan harga nanti, bandar hanya butuh sedikit tenaga beli (*low effort, big result*).

---

### Pilar 4: Silent Accumulation Broksum (Deteksi Smart Money & HMB)
* **Karakteristik:** 
  * Di balik volume yang sepi tersebut, broker summary harian menunjukkan **Net Akumulasi Top-1 Buyer $> 30\%$** dari total nilai transaksi.
  * Pembeli didominasi oleh broker institusi / *smart money* (misal: `CC`, `AK`, `BK`, `KZ`, atau spesifik bandar lokal `MG`), sedangkan penjual tersebar di banyak broker ritel (`YP`, `PD`, `XC`, `XL`).
* **HMB (Harga Modal Bandar):**
  * Rata-rata harga beli (*Average Buy Price*) broker akumulator di area base menjadi patokan HMB.
  * Selama harga pasar masih berada dekat HMB ($\pm 1\% - 3\%$), posisi kita sejajar dengan harga modal bandar.

---

## 3. Cara Membaca Volume di Candlify & Kaitannya dengan Likuiditas

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

## 4. Kapasitas Modal & Aturan Likuiditas Keluar-Masuk Barang

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

## 5. SOP Simulasi Eksekusi Trading Plan

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

## 6. Trader's Quick Checklist Sebelum Menekan Tombol Buy

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
