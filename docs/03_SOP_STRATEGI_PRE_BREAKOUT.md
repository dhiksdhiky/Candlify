# 💥 SOP & STRATEGI SWING PRE-BREAKOUT BASE

> **Candlify Market Intelligence Manual — Modul 3: SOP Eksekusi & Manajemen Risiko**  
> *SOP komprehensif 4 Pilar Pre-Breakout, validitas backtest Triple-Barrier bursa, aturan Two-Tier Stop Loss, studi kasus riil (BALI, PTSP, RONY vs Perangkap Distribusi LION, RGAS, BKDP & Jebakan Crossing/Repo BINA), serta checklist emas sebelum eksekusi.*

---

## 📑 DAFTAR ISI
1. [Prinsip Dasar Pre-Breakout Base](#1-prinsip-dasar-pre-breakout-base)
2. [Anatomi 4 Pilar Algoritmik](#2-anatomi-4-pilar-algoritmik)
3. [Bukti Validitas Backtest (Triple-Barrier Method)](#3-bukti-validitas-backtest-triple-barrier-method)
4. [SOP Two-Tier Stop Loss & Money Management](#4-sop-two-tier-stop-loss--money-management)
5. [🏆 Studi Kasus Riil Sukses (Win Trades: BALI, PTSP, RONY)](#5--studi-kasus-riil-sukses-win-trades-bali-ptsp-rony)
6. [⚠️ Studi Kasus Riil Gagal, Perangkap Distribusi & Jebakan Crossing (LION, RGAS, BKDP, BINA)](#6-️-studi-kasus-riil-gagal-perangkap-distribusi--jebakan-crossing-lion-rgas-bkdp-bina)
7. [Trader's Quick Checklist Sebelum Menekan Tombol Buy (9 Poin Emas)](#7-traders-quick-checklist-sebelum-menekan-tombol-buy-9-poin-emas)

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

## 6. ⚠️ Studi Kasus Riil Gagal, Perangkap Distribusi & Jebakan Crossing (LION, RGAS, BKDP, BINA)

Tidak semua konsolidasi adalah akumulasi. Anda harus waspada terhadap **Perangkap Distribusi** maupun **Jebakan Akumulasi Semu (*Crossing* / Repo)**:

### A. Pola Jebakan Distribusi (Distribution Trap — LION, RGAS, BKDP):
1. **Pecah Kotak Base dengan Volume Meledak**: 
   * Saham tampak membentuk base, tetapi saat harga menembus ke bawah support base, volume tiba-tiba melonjak besar. Ini adalah tanda bandar membanting harga (*dumping*).
2. **Broksum Divergence (Harga Naik, Top Broker Net Sell)**:
   * Harga saham dinaikkan $+2\% - 3\%$, tetapi broker summary menunjukkan Top-1 broker penjual membuang barang dalam jumlah masif kepada ritel.
3. **Kasus LION & RGAS**:
   * Harga gagal bertahan di atas MA20 dan terus mencetak harga penutupan lebih rendah (*lower low*). Trader yang mematuhi SOP Stop Loss Tier-1 hanya terkena luka kecil $-3.5\%$, terlindungi dari penurunan beruntun $-25\%$.
4. **Kasus BKDP (Saham Ditelantarkan Pasca Spike)**:
   * Volume menyusut drastis dari 2,31 Juta lot menjadi 27 Ribu lot, tetapi **tidak ada satu pun broker institusi yang melakukan akumulasi**. Saham kering karena ditinggal pergi bandarnya (*abandoned*).

---

### B. Kasus BINA: Jebakan Akumulasi Semu (*Crossing* Pasar Nego, *Standby Repo* & *Window Dressing* Akhir Bulan)

Pada Oktober 2026, saham **BINA (`PT Bank Ina Perdana Tbk.`)** sempat masuk ke dalam radar **Pre-Breakout Base** dengan metrik yang sekilas tampak sangat ideal: **Skor 72 • Acc RS (49% Dom) • HMB Rp 3.978,5 • Base 3.08% • Dry 0.27x**. Namun, hasil audit forensik terhadap database Neon membuktikan bahwa akumulasi broker **RS** di BINA **bukan akumulasi *Smart Money* untuk *mark-up* harga**, melainkan kombinasi transaksi **Crossing Pasar Nego** dan **Penjaga Likuiditas Pasif (*Standby Buyer / Repo*)**.

#### 1. Bukti Forensik Database: Kontaminasi Pasar Nego vs Pasar Reguler
Karena data ringkasan broker (*All Market*) menggabungkan transaksi Pasar Reguler, Pasar Negosiasi, dan Pasar Tunai, perpindahan barang tutup sendiri (*crossing*) antar-institusi di Pasar Nego ikut tercatat sebagai volume akumulasi/distribusi broker:

| Tanggal | Vol Pasar Reguler (`harga_saham`) | Vol Pasar Nego (`non_regular_volume`) | Total Broksum (`broker_summary`) | Fakta Transaksi di Balik Layar (Data DB Neon) |
| :--- | :--- | :--- | :--- | :--- |
| **30 Sep 2026** | **61.285 Lot** (Rp 26,35 M) | **250.000 Lot (Rp 102,50 M)** | **309.385 Lot** (Rp 128,01 M) | Broker **RB** *crossing* (jual di Pasar Nego) **250.000 Lot (Rp 102,5 M)** langsung ditampung oleh **RS**! Hari itu RS tercatat Net Buy **297.461 Lot (Rp 123,1 M)**. |
| **01 Okt 2026** | **8.534 Lot** (Rp 3,48 M) | **125.000 Lot (Rp 51,25 M)** | **132.641 Lot** (Rp 54,45 M) | Broker **RB** *crossing* tutup sendiri (Beli 125.508 Lot, Jual 125.000 Lot senilai Rp 51,3 M). |
| **28 Sep 2026** | **9.851 Lot** (Rp 3,94 M) | **40.000 Lot (Rp 20,00 M)** | **49.087 Lot** (Rp 23,64 M) | Broker **RF** *crossing* tutup sendiri **40.000 Lot (Rp 20 M)**. |
| **18 Sep 2026** | **5.055 Lot** (~Rp 2,05 M) | *(Crossing Nego)* | **1.804.850 Lot (Rp 739,96 M)** | Broker **RB** *crossing* tutup sendiri **1.800.000 Lot (Rp 738 Miliar)**! |
| **30 Jun 2026** | **120.892 Lot** | *(Crossing Kuartal II)* | **120.892 Lot** | Broker **RB** jual **88.608 Lot (Rp 35 M)** langsung ditampung **RS** (**+106.080 Lot / Rp 42,6 M**). |

#### 2. Mengapa Sinyal Pre-Breakout Bisa Terkecoh oleh Pola *Standby Buyer*?
Selama 6 bulan penuh (133 hari bursa), broker **RS** tercatat membeli bersih **517.989 Lot (Rp 214,1 Miliar)** dengan **`sell_vol = 0` hampir setiap hari**:
1. **Hari Biasa (Tengah Bulan)**: Transaksi Pasar Reguler BINA sebenarnya sangat sepi ritel (frekuensi hanya **50–90 kali transaksi/hari**, volume reguler hanya **1.500–3.400 lot/hari**). Setiap hari RS hanya memasang *bid* pasif menampung **500–1.200 lot** dari broker tertentu yang rutin mencicil jual (**SA, AZ, OD, SS**).
2. **Anomali Akhir Bulan (*Window Dressing*)**: Tepat pada **tanggal bursa terakhir setiap bulan** (**29 Mei, 30 Juni, 31 Juli, 31 Agustus, dan 30 September**), selalu terjadi lonjakan volume besar dan pengangkatan harga penutupan (*window dressing* kuartal/bulanan + *crossing* RS).
3. **Efek Ilusi Algoritmik**:
   * Lonjakan tanggal **30 September** ($+6.3\%$ ke Rp 4.350) terbaca oleh mesin sebagai **Pilar 1: Prior Ignition Spike**.
   * Saat memasuki bulan Oktober, volume BINA kembali ke kondisi aslinya yang sepi ($1.700 - 3.400$ lot/hari). Karena rata-rata volume 20 hari (VMA20) membengkak akibat lonjakan 30 September, volume sepi di bulan Oktober terbaca sebagai **Pilar 3: Volume Dry-Up (`Dry 0.27x`)**.
   * Harga BINA yang memang dijaga statis (*pegged*) di Rp 3.900–4.020 terbaca sebagai **Pilar 2: Tight Base (`Base 3.08%`)**, dan tampungan harian RS terbaca sebagai **Pilar 4: Silent Accumulation (`Acc RS 49% Dom`)**.

---

### 🛡️ C. SOP Mitigasi 30 Detik Menggunakan 4 Menu Candlify (Deteksi Crossing & Repo)

Agar Anda tidak terjebak membeli saham *repo / crossing / pegged* yang tidak akan di-*mark-up* dalam waktu dekat, gunakan **4 Menu Verifikasi** yang sudah tersedia di dalam laci **Order Flow & Broker Summary** Candlify*(dibuka dengan mengklik badge **🟢 Akumulasi / HMB** di kanan atas layar Chart)*:

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                4 MENU DETEKSI CROSSING & REPO DI CANDLIFY                    │
├──────────────────────────┬───────────────────────────────────────────────────┤
│ 1. 📅 Daily Activity     │ Cek pola "Hijau 100% Tanpa Jual" & Ledakan Akhir  │
│    (Kalender Broker)     │ Bulan (Ciri khas Standby Buyer / Penampung Repo). │
├──────────────────────────┼───────────────────────────────────────────────────┤
│ 2. 📈 Broker Flow        │ Cek pola "Bayangan Cermin 1-Lawan-1" (1 garis     │
│    (Grafik Kumulatif)    │ loncat vertikal = 1 garis terjun vertikal).       │
├──────────────────────────┼───────────────────────────────────────────────────┤
│ 3. 🐳 Trade Size & Nego  │ Cek peringatan ⚠️ Crossing Pasar Nego & anomali   │
│    (Kartu Intelligence)  │ Foreign Outflow (Net 5D / 20D merah).             │
├──────────────────────────┼───────────────────────────────────────────────────┤
│ 4. 📜 History Data       │ Bandingkan rata-rata Value harian reguler (sepi)  │
│    (Tabel Historis)      │ terhadap lonjakan semu di tanggal akhir bulan.    │
└──────────────────────────┴───────────────────────────────────────────────────┘
```

1. **📍 Menu 1: Tab `📅 Daily Activity` (Deteksi Pola Robot / Akhir Bulan)**
   * **Cara Akses**: Buka laci Broksum $\rightarrow$ klik tab ke-4 **`📅 Daily Activity`** $\rightarrow$ klik chip broker akumulator utama (misal **`RS`**) $\rightarrow$ geser bulan mundur menggunakan tombol `◀`.
   * **Indikasi Bahaya**: Jika kalender broker tersebut **100% berwarna HIJAU (`BUY`) setiap hari selama berbulan-bulan tanpa pernah ada hari `SELL`**, dengan lot harian kecil yang seragam (`+500` s/d `+1.2K` lot), lalu **meledak ratusan ribu lot tepat di tanggal terakhir setiap bulan**, itu adalah **Broker Penampung Repo / Penjaga Harga Pasif**, bukan bandar *swing* yang sedang bersiap melakukan *mark-up*.
2. **📍 Menu 2: Tab `📈 Broker Flow` (Deteksi "Tukar Baju / Crossing 1-Lawan-1")**
   * **Cara Akses**: Buka laci Broksum $\rightarrow$ klik tab ke-3 **`📈 Broker Flow`** $\rightarrow$ pilih rentang waktu **`1M`** atau **`3M`**.
   * **Indikasi Bahaya**: Perhatikan bentuk kurva pembeli tertinggi vs penjual tertinggi.
     * **Akumulasi Asli (*Valid*)**: Kurva 1–2 broker bandar menanjak bertahap sambil menyerap kurva banyak broker ritel (`YP`, `XL`, `PD`, `XC`) yang turun menyebar.
     * **Crossing / Tukar Baju (*Invalid*)**: Kurva 1 broker (misal `RS`) melonjak tegak lurus ke atas **persis membentuk bayangan cermin simetris 1-lawan-1** dengan kurva 1 broker lain (misal `RB`) yang terjun tegak lurus di tanggal yang sama.
3. **📍 Menu 3: Kartu `🐳 Trade Size & Nego` + `🌐 Foreign (Asing)` (Tab `🏦 Broksum`)**
   * **Cara Akses**: Buka laci Broksum $\rightarrow$ lihat dua kartu Market Intelligence di bawah bar rasio Buy/Sell, atau arahkan pemilih tanggal ke hari terjadinya *Tiang Spike*.
   * **Indikasi Bahaya**: Kartu Nego memunculkan peringatan **`⚠️ Crossing: Transaksi Nego Besar`** ($\ge \text{Rp } 10\text{ Miliar}$ atau $\ge 1\%$ saham beredar), sementara kartu Foreign menunjukkan **`Net 5D` dan `Net 20D` Outflow (Merah)**.
4. **📍 Menu 4: Tab `📜 History Data` (Audit Likuiditas Harian Murni)**
   * **Cara Akses**: Buka laci Broksum $\rightarrow$ klik tab ke-2 **`📜 History Data`** $\rightarrow$ pilih **`Daily`**.
   * **Indikasi Bahaya**: Nilai transaksi (*Value*) sehari-hari sangat tipis (misal hanya Rp 0,5 M – Rp 1,5 M untuk saham berkapitalisasi puluhan triliun), dan hanya ramai sesaat pada tanggal penutupan kuartal/akhir bulan.

---

## 7. Trader's Quick Checklist Sebelum Menekan Tombol Buy (9 Poin Emas)

Sebelum Anda menekan tombol buy di aplikasi sekuritas Anda, lakukan verifikasi cepat pada 9 poin berikut:

1. [ ] **Apakah ada Tiang Induk hijau kuat dalam 4 - 28 hari terakhir (dan bukan sekadar lonjakan *window dressing* tanggal terakhir bulan)?**
2. [ ] **Apakah harga saat ini bertahan tenang di atas garis MA20?**
3. [ ] **Apakah rentang konsolidasi 7 hari rapat ($\le 12\%$) dan candle kecil-kecil?**
4. [ ] **Apakah volume harian mengering drastis dibanding tiang induk?**
5. [ ] **Apakah broker summary menunjukkan Net Akumulasi dominan oleh Smart Money?**
6. [ ] **Apakah sudah dicek di tab `📅 Daily Activity` & `📈 Broker Flow` bahwa akumulasi tersebut BUKAN transaksi *Crossing* Pasar Nego (bayangan cermin 1-lawan-1) atau *Standby Repo*?**
7. [ ] **Apakah harga beli dekat dengan HMB (Harga Modal Bandar)?**
8. [ ] **Apakah level Stop Loss (di bawah support base) sudah ditentukan dengan pasti?**
9. [ ] **Apakah jumlah lot sudah dihitung menggunakan kalkulator Trading Plan Candlify sesuai modal risiko Anda?**

> **Jika ke-9 poin di atas tercentang "YA", lakukan eksekusi dengan tenang dan disiplin!**
