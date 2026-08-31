# JAGAT — Jejaring Analisis & Garda Atensi Terpadu

JAGAT adalah sistem pemantauan informasi yang berfokus pada pemberitaan terkait Jawa Timur, pengelompokan insiden, skala atensi, pemetaan wilayah, snapshot harian, dan arsip.

## Fondasi V6.7.0

- Jawa Timur adalah wilayah fokus utama.
- 39 Polres/Polresta Jawa Timur tetap menjadi entitas kewilayahan utama.
- Polda Jawa Timur dan unit Polda (misalnya Bidpropam, Satbrimob, Ditreskrimum, Ditreskrimsus, Ditresnarkoba, Ditres Siber, dan Ditres PPA) ditampilkan sebagai area `Polda Jatim` di dalam induk Jawa Timur; Polda bukan Polres ke-40.
- Lokasi utama diturunkan dari judul berita. Nama media/publisher tidak dipakai sebagai bukti lokasi.
- Status lokasi: `Jawa Timur`, `LUAR JATIM`, atau `BELUM TERPETAKAN`.
- `Jawa Timur` pada filter adalah induk yang mencakup seluruh area/Polres Jatim serta area Polda Jatim.
- Dashboard menampilkan keadaan Jawa Timur pada hari pemantauan; Monitoring adalah penjelajah data lintas periode; Arsip adalah snapshot historis.
- `collected_at` adalah tanggal deteksi monitoring; `published_at` adalah tanggal terbit artikel.
- Case tetap menyimpan prioritasnya lintas hari; Case hanya dihitung sebagai aktivitas hari ini apabila mempunyai artikel yang terdeteksi hari itu.
- Skala atensi utama 0–100 dengan tiga tingkat operasional: Rendah (0–39), Sedang (40–69), dan Tinggi (70–100). Field `priority` tetap dipertahankan untuk kompatibilitas.
- Artikel dan Case mempertahankan relasi satu artikel dapat berada pada satu Case dan satu Case dapat memiliki banyak sumber.
- Filter dibangun secara dinamis dari dataset aktif dan tidak menambahkan filter Satker terpisah.

## Alur kerja

`Collect → Normalize/Classify → Case Engine → Snapshot → Validate → Frontend → Commit → GitHub Pages`

Workflow tunggal berada di `.github/workflows/collect.yml`. Secret `YOUTUBE_API_KEY` tetap digunakan untuk pemantauan YouTube.

## UI

Dashboard menggunakan layout dark command-center yang terinspirasi bahasa visual monitor operasional: KPI ringkas, peta Jawa Timur sebagai fokus utama, serta rincian 40 area Jatim (Polda + 39 Polres/Polresta) dengan pencarian dan status atensi. Monitoring, drawer detail, filter, tombol Salin, dan tombol Buka sumber tetap memakai core UI yang sudah ada.
