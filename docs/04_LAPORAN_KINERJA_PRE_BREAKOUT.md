# 📊 Laporan Kinerja & Evaluasi Pre-Breakout

> Scorecard performa historis sinyal Pre-Breakout (Live Neon DB), perbandingan formula V1 vs V2, dan log pembelajaran strategi

<!-- FORENSIC_NOTES_START
2026-10-02|DKHH: Multi-bagger T+2 (+84.1%), base kering di Rp 69 reli 3 hari ke Rp 127.
2026-10-02|BALI: Explosion ARA T+1 (+24.8%), akumulasi YJ masif & ritel net sell.
2026-10-13|RSGK: Explosion T+2 (+32.2%), tiang induk kuat & base konsolidasi tertib.
2026-10-14|RSGK: Konfirmasi pocket pivot, lanjut reli T+1 (+23.6%) ke Rp 1.335.
2026-10-13|IGAR: Setup sangat bersih (DD 0.0%), mulus mencapai target +10.2% di T+3.
2026-10-14|IGAR: Konfirmasi pocket pivot (DD 0.0%), lanjut naik +9.7% ke Rp 520.
2026-10-02|ABDA: [Era V1] Jebakan saham tidur illiquid (ADT Rp 72 Juta), skor 90/100 lalu longsor -24.6%.
2026-10-09|ABDA: [Era V1] Saham tidur tanpa tiang induk & Dominance 0%, tereliminasi total di V2.
2026-10-02|PGUN: [Era V1] Tanpa dominasi bandar (Dom 0%), jebol support -26.7%.
FORENSIC_NOTES_END -->

---

## 1. 📈 Scorecard Live Evaluasi Sinyal (Otomatis dari Neon DB)

> **Metodologi Evaluasi ($T+1$ s/d $T+10$ Hari Bursa):**
> * 🎯 **HIT (SUPER):** High intraday menyentuh $\ge +15\%$ sebelum menyentuh Stop Loss ($-4\%$).
> * 🎯 **HIT:** High intraday menyentuh $\ge +8\%$ sebelum menyentuh Stop Loss ($-4\%$).
> * 🛑 **STOP OUT:** Low intraday menyentuh $\le -4\%$ sebelum target $+8\%$ tercapai.
> * ⏳ **RUNNING:** Umur sinyal $< 10$ hari bursa & harga masih berada di rentang $-4\%$ s/d $+8\%$ *(kolom evaluasi dibiarkan `—` sampai analisis berkala)*.
> * ⚪ **EXPIRED:** Sudah lewat 10 hari bursa tanpa menyentuh target maupun Stop Loss.

<!-- LIVE_PRE_BREAKOUT_SCORECARD -->

---

## 2. ⚖️ Perbandingan Menyeluruh Formula V1 vs V2

Evaluasi forensik terhadap **134 sinyal uji coba (Oktober 2026)** menunjukkan mengapa pengetatan 4 pilar institusional di V2 sangat krusial:

### A. Perbandingan Kinerja Kuantitatif

| Parameter Kinerja | ⚠️ Versi 1 (V1 - Formula Lama) | 🚀 Versi 2 (V2 - Formula 4 Pilar) | Dampak Perubahan |
| :--- | :---: | :---: | :--- |
| **Beban Sinyal Harian** | **20 – 32 saham / hari** | **1 – 4 saham / hari** | **Noise terpangkas $\sim 90\%$** *(Ultra-selektif)* |
| **Tingkat Stop Out ($\le -4\%$)** | **$85.1\%$** *(114 dari 134 sinyal)* | **Terkoreksi drastis** | Saham tidur & *bear flag* dibabat habis |
| **Win Rate / Hit Rate ($\ge +8\%$)** | **$11.9\%$** *(16 sinyal)* | **Fokus setup kualitas tinggi** | Kualitas sinyal jauh lebih bersih |
| **Rata-rata Drawdown Saham Gagal** | **$-17.0\%$** | **Terkontrol ($\sim -4\%$)** | Terlindungi *support base* & MA20 |
| **Rata-rata Gain Saham Hit** | **$+18.9\%$** *(Max $+84.1\%$)* | **$+15\%$ s/d $+32\%+$** | Saham juara (`RSGK`, `BALI`, `IGAR`) tetap tertangkap |

### B. Perbedaan Logika & Aturan (Rule-by-Rule)

| Komponen Formula | ⚠️ Versi 1 (V1) | 🚀 Versi 2 (V2) | Alasan Evolusi |
| :--- | :--- | :--- | :--- |
| **1. Tiang Induk (*Ignition*)** | ❌ Tidak wajib | ✅ Wajib candle $\ge +5\%$ & Vol $\ge 2\times$ (4–28 hari) | Gugurkan saham tidur & *downtrend*. |
| **2. Volume Kering (*Dry-Up*)** | ⚠️ Hanya `Vol / VMA20 <= 0.45x` | ✅ `Vol <= 0.40x` + **`Up/Down Vol >= 1.15`** | Bedakan volume diserap bandar vs ditinggal mati. |
| **3. Serapan Harga (*CLV*)** | ❌ Tidak ada | ✅ **`CLV >= 0.50`** | Pastikan penutupan di paruh atas candle. |
| **4. Dominasi Broker Bandar** | ⚠️ Opsional (Dom 0% bisa lolos) | ✅ **Dominance $> 30\%$** | Eliminasi *retail churning*. |
| **5. Asimetri Order Flow** | ❌ Tidak ada | ✅ **`AAR >= 1.5` (via HHI)** | Deteksi sindikat pecah akun multi-broker. |
| **6. Verifikasi Pasar Nego** | ❌ Buta terhadap crossing | ✅ **Alert Crossing ($\ge$ Rp 10 B / $\ge 1\%$ saham)** | Mitigasi jebakan *standby buyer repo* (kasus `BINA`). |

### C. Tiga Pembelajaran Kunci dari Audit Forensik
1. **Jebakan Saham Tidur (`ABDA`):** Di V1, saham tidak likuid (ADT Rp 72 Juta) bisa mencetak Skor 100 karena candle kecil (`range_7 <= 3%`) dan volume nyaris nol (`vol_dry <= 0.15x`), lalu langsung longsor $-24.6\%$ saat ada ritel buang barang.
2. **Jebakan Crossing & Repo (`BINA`):** Akumulasi masif broker `RS` ternyata didominasi transaksi tutup sendiri (*crossing*) di Pasar Nego Rp 102,5 Miliar dengan pola beli satu arah (*standby buyer repo*). Solusi Candlify: tetap jaga rumus inti murni tanpa bias, tetapi sajikan alert transparan lewat pop-up **Trade Size & Pasar Nego** serta SOP 4-menu.
3. **Kualitas Setup Murni (`IGAR`, `RSGK`, `BALI`, `DKHH`):** Saham dengan kombinasi tiang induk jelas, base kering di atas MA20, dan akumulasi bersih reguler mampu mencetak reli cepat $+10\%$ hingga $+84\%$ dalam hitungan $T+1$ s/d $T+3$.

---

## 3. 🧠 Log Evolusi Formula & Panduan Audit Berkala

### Catatan Pembelajaran Berjalan:
* **Oktober 2026 (Upgrade V1 $\rightarrow$ V2):** Penambahan pilar `AAR`, `Dominance`, `Up/Down Vol Ratio`, `CLV 3D`, dan `Pocket Pivot` berhasil menyaring noise dari 20–32 saham/hari menjadi 2–4 saham super selektif.
* **Oktober 2026 (Integritas Pasar Nego):** Penambahan deteksi crossing non-reguler & modal *Market Intelligence* tanpa mengubah aturan inti screener untuk mencegah *overfitting*.

### 📋 Template Prompt Audit Berkala (Untuk Sesi Baru)
Gunakan prompt berikut saat ingin mengevaluasi sinyal terbaru dan memperbarui catatan forensik di blok `FORENSIC_NOTES`:

```text
Halo Lin, tolong lakukan evaluasi dan update berkala untuk laporan kinerja Pre-Breakout kita:
1. Baca `docs/04_LAPORAN_KINERJA_PRE_BREAKOUT.md` dan cek sinyal yang statusnya sudah selesai (HIT / STOP OUT / EXPIRED) tapi belum punya catatan forensik di blok FORENSIC_NOTES.
2. Sambungkan ke database Neon PostgreSQL, tarik data `harga_saham` dan `broker_summary` untuk saham-saham tersebut dari tanggal sinyal hingga hari bursa terakhir.
3. Periksa anatomi pergerakannya: apakah akumulasi reguler Smart Money murni, atau ada anomali (crossing Pasar Nego, repo standby buyer, retail churning, atau koreksi makro IHSG).
4. Tambahkan catatan singkat & tajam ke blok `FORENSIC_NOTES` di `docs/04_LAPORAN_KINERJA_PRE_BREAKOUT.md` dan catat poin pembelajaran baru di bagian Log Evolusi Formula, lalu test, commit, dan push ke GitHub.
```
