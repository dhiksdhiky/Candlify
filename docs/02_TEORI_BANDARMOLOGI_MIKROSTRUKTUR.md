# 🕵️ TEORI BANDARMOLOGI & MIKROSTRUKTUR PASAR SAHAM

> **Candlify Market Intelligence Manual — Modul 2: Teori Fundamental Smart Money**  
> *Prinsip kerja bandar di Bursa Efek Indonesia (IDX), Dynamic Behavioral Scoring broker ritel vs institusi, perhitungan Harga Modal Bandar (HMB Net-Inventory), mikrostruktur volume, serta mekanisme papan perdagangan FCA.*

---

## 📑 DAFTAR ISI
1. [Filosofi Pasar: Smart Money vs Ritel](#1-filosofi-pasar-smart-money-vs-ritel)
2. [🤖 Dynamic Behavioral Scoring (Deteksi Broker Ritel vs Big Money)](#2--dynamic-behavioral-scoring-deteksi-broker-ritel-vs-big-money)
3. [Perhitungan HMB: Net-Inventory Weighted vs Gross Buy](#3-perhitungan-hmb-net-inventory-weighted-vs-gross-buy)
4. [Mikrostruktur Volume: Surge, Dry-Up, Asimetri & CLV](#4-mikrostruktur-volume-surge-dry-up-asimetri--clv)
5. [Paradoks Likuiditas & Aturan Papan Bursa (Reguler vs FCA)](#5-paradoks-likuiditas--aturan-papan-bursa-reguler-vs-fca)

---

## 1. Filosofi Pasar: Smart Money vs Ritel

Di pasar modal, pergerakan harga saham tidak pernah terjadi secara kebetulan atau acak murni (*random walk*). Di balik setiap tren kenaikan yang signifikan, selalu ada aktor bermodal raksasa yang disebut sebagai **Smart Money**, **Market Maker**, atau secara populer di Indonesia dikenal sebagai **Bandar**.

### Perbedaan Mendasar Ritel vs Smart Money:
* **Trader Ritel**:
  * Bertransaksi dengan emosi (FOMO saat harga hijau tinggi, panik saat harga merah turun).
  * Memiliki modal kecil dan bergerak secara terpecah-pecah tanpa koordinasi (*fragmented*).
  * Menjadi penyedia likuiditas keluar (*exit liquidity*) bagi bandar ketika membeli di pucuk.
* **Smart Money (Bandar)**:
  * Memiliki modal puluhan hingga ratusan miliar rupiah dan akses informasi lebih awal.
  * Membutuhkan waktu berhari-hari atau berminggu-minggu untuk mengumpulkan barang secara rapi (*silent accumulation*) tanpa membuat harga terbang sebelum waktunya.
  * Selalu mengontrol suplai pasar sebelum menaikkan harga (*markup phase*).

> **Kaidah Emas Bandarmologi:**  
> *"Kita tidak bisa melawan bandar, tetapi kita bisa membaca jejak transaksinya dan menumpang kereta saat mereka mulai berangkat."*

---

## 2. 🤖 Dynamic Behavioral Scoring (Deteksi Broker Ritel vs Big Money)

Di era pasar modal modern, bandar tidak lagi hanya memakai kode broker institusi besar (seperti `AK`, `BK`, `KZ`, `CC`). Sering kali bandar melakukan pemecahan transaksi (*split order*) menggunakan broker ritel populer (seperti `YP`, `PD`, `XC`, `XL`) agar tidak dicurigai. Sebaliknya, investor sultan (*High Net Worth Individuals*) juga bisa bertransaksi menggunakan akun ritel.

Oleh karena itu, sistem kuantitatif Candlify **tidak menggunakan label statis (hardcoded)**, melainkan menerapkan **Dynamic Behavioral Scoring (Scoring Perilaku Dinamis)** berbasis 4 parameter perilaku transaksi:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   4 PARAMETER KUANTITATIF MESIN                        │
├───────────────────────────────┬────────────────────────────────────────┤
│ 1. Directional Conviction     │ Mengukur tektokan vs akumulasi 1 arah  │
│ 2. Dominance Ratio            │ Konsentrasi penguasaan barang di base  │
│ 3. Value Size Tier            │ Bobot modal riil (Big vs Small Money)  │
│ 4. Price Impact (CLV & HMB)   │ Efisiensi serapan terhadap arah candle │
└───────────────────────────────┴────────────────────────────────────────┘
```

### 1. Directional Conviction (Konsistensi Arah)
$$\text{Conviction} = \left| \frac{\text{Net Value}}{\text{Gross Value}} \right| = \left| \frac{\text{Buy Value} - \text{Sell Value}}{\text{Buy Value} + \text{Sell Value}} \right|$$
* **Nilai Mendekati 0.0 (Tektokan Ritel/Scalper)**: Misal broker `YP` beli Rp 10 Miliar dan jual Rp 9.8 Miliar ($\text{Net} = \text{Rp } 200 \text{ Juta}$, Conviction = 0.01). Ini adalah aktivitas scalper/day trader yang tidak mengunci barang.
* **Nilai Mendekati 1.0 (Akumulasi Tulen Smart Money)**: Misal broker `CC` beli Rp 5 Miliar dan jual Rp 0 ($\text{Net} = \text{Rp } 5 \text{ Miliar}$, Conviction = 1.00). Ini membuktikan keyakinan mutlak (*high conviction*) untuk menimbun barang tanpa berniat keluar hari itu.

### 2. Dominance Ratio (Rasio Penguasaan)
$$\text{Dominance} = \frac{\text{Net Value Top 1 Buyer}}{\sum \text{Net Value All Buyers}}$$
* Mengukur seberapa dominan pembeli utama menguasai barang di pasar. Jika satu broker menyerap $> 40\%$ dari total net buy seluruh bursa pada saham tersebut, pasar berada dalam monopoli kendali (*tight control*).

### 3. Value Size Tier (Skala Nominal Modal)
Mesin mengelompokkan nilai transaksi harian ke dalam skala logaritmik:
* **Mega Accumulation**: Net buy $> \text{Rp } 5 \text{ Miliar}$.
* **Significant Accumulation**: Net buy $\text{Rp } 1 \text{ Miliar} - \text{Rp } 5 \text{ Miliar}$.
* **Moderate Accumulation**: Net buy $\text{Rp } 250 \text{ Juta} - \text{Rp } 1 \text{ Miliar}$.
* **Noise / Retail Trifle**: Net buy $< \text{Rp } 250 \text{ Juta}$.

---

## 3. Perhitungan HMB: Net-Inventory Weighted vs Gross Buy

Banyak analis ritel salah menghitung modal bandar dengan merata-ratakan harga *Gross Buy* (total pembelian kotor). Padahal, jika bandar membeli di Rp 500 dan sempat menjual sebagian di Rp 550, modal riil sisa barang yang mereka simpan (*inventory*) bukan lagi di Rp 500.

### Rumus Net-Inventory Weighted HMB:
$$\text{HMB} = \frac{\sum_{i \in \text{Top Buyers}} \text{Net Value}_i}{\sum_{i \in \text{Top Buyers}} (\text{Net Volume}_i \times 100)}$$

Di mana:
* $\text{Net Value}_i = \text{Buy Value}_i - \text{Sell Value}_i$ (Rupiah bersih yang tertahan).
* $\text{Net Volume}_i = \text{Buy Lot}_i - \text{Sell Lot}_i$ (Sisa lembar saham fisik yang dikuasai).

### Mengapa Pendekatan Ini Lebih Akurat?
1. **Menghilangkan Efek Cuci Saham (*Wash Trading*)**: Transaksi semu tukar barang antar rekening yang dibuat bandar untuk memancing keramaian (*running trade*) otomatis tereliminasi karena nilai beli dan jualnya saling menghapus pada posisi net.
2. **Menemukan Titik Pertahanan Terakhir (*Bandar Defense Level*)**: Bandar akan mempertahankan harga saham agar tidak turun jauh di bawah HMB mereka, karena jika turun terlalu dalam, portofolio mereka sendiri yang akan mengalami *unrealized loss* besar.

---

## 4. Mikrostruktur Volume: Surge, Dry-Up, Asimetri & CLV

Volume adalah bahan bakar pergerakan harga. Tanpa volume, harga tidak dapat bergerak jauh. Namun, dalam bandarmologi, volume dibaca secara berlawanan pada fase tertentu:

### A. Volume Surge (Tiang Lonjakan Awal)
* Terjadi saat bandar pertama kali menyuntikkan likuiditas ke saham yang sedang tidur.
* Volume melonjak $\ge 2.0\times$ hingga $5.0\times$ Volume MA20 dengan candle hijau panjang.
* Ini adalah pengumuman tak resmi bahwa *Smart Money* telah masuk dan saham tersebut resmi masuk radar pengamatan.

### B. Volume Dry-Up (Suplai Kering Kerontang)
* Setelah tiang awal, saham masuk ke fase konsolidasi (*base*). Pada fase ini, volume harian harus **menciut drastis** ($\le 40\% - 50\%$ dari rata-rata).
* **Makna:** Volume kering membuktikan bahwa **penjual sudah habis (*supply exhaustion*)**. Ritel yang memegang saham sudah tidak mau menjual rugi, dan bandar tidak sedang membuang barang.

### C. Asimetri Volume (Volume Hijau vs Merah)
$$\overline{\text{Vol}}_{\text{Candle Merah}} \ll \overline{\text{Vol}}_{\text{Candle Hijau}}$$
* Ketika candle merah (harga turun sedikit), volumenya sangat kerdil.
* Namun ketika candle hijau (harga naik sedikit), volumenya membesar.
* Ini bukti tak terbantahkan bahwa penurunan harga hanya rekayasa tanpa tekanan jual riil (*no selling pressure*).

### D. Close Location Value (CLV)
$$\text{CLV} = \frac{\text{Close} - \text{Low}}{\text{High} - \text{Low}}$$
* Nilai CLV berkisar antara $0.0$ (tutup di titik terendah) hingga $1.0$ (tutup di titik tertinggi).
* Nilai $\text{CLV} \ge 0.50$ (ideal $> 0.70$) menandakan bahwa ada aksi beli serap menjelang penutupan bursa (*pre-closing absorption*), mencegah terbentuknya jarum atas (*bearish wick*).

---

## 5. Paradoks Likuiditas & Aturan Papan Bursa (Reguler vs FCA)

Bursa Efek Indonesia membagi saham ke dalam beberapa papan pencatatan:
1. **Papan Utama & Pengembangan (Perdagangan Reguler)**:
   * Mekanisme order book standar (*Continuous Auction*).
   * Auto Rejection Atas/Bawah (ARA/ARB) simetris $\pm 20\% - 35\%$ tergantung fraksi harga.
2. **Papan Pemantauan Khusus (FCA / Full Call Auction)**:
   * Menggunakan lelang berkala tanpa order book real-time transparan.
   * Fraksi harga Rp 1 dengan batasan ARB/ARA maksimal $\pm 10\%$.
   * Volatilitas bisa sangat ekstrim saat jam penutupan sesi lelang (15:55 WIB).

### Paradoks Likuiditas:
> *"Saham yang paling bagus untuk dibeli secara swing adalah saham yang likuiditasnya sedang tampak kering di mata ritel, tetapi memiliki cadangan penyerapan bandar yang besar."*

Jika trader membeli saham saat running trade sedang sangat ramai dan likuiditas melimpah di antrean offer, 80% kemungkinan saham tersebut sedang berada di tahap distribusi akhir. Candlify memandu Anda membeli saat likuiditas sedang tenang dan bersiap meledak.

---
*Modul selanjutnya: Baca [03_SOP_STRATEGI_PRE_BREAKOUT.md](03_SOP_STRATEGI_PRE_BREAKOUT.md) untuk panduan aturan teknikal 4 pilar, manajemen stop loss, dan studi kasus historis.*
