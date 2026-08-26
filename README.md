# PNM — Polri Negative News Monitor

Versi ini dirancang agar benar-benar berjalan di GitHub Pages + GitHub Actions.

## Login demo
- Email: `admin@propam-jatim.go.id`
- Password: `PropamJatim2026!`

> Login frontend ini hanya untuk demo. Password dapat terlihat oleh orang yang memeriksa source JavaScript. Untuk penggunaan internal/produksi, pindahkan autentikasi ke Supabase Auth atau backend.

## Cara deploy

1. Buat repository GitHub baru.
2. Upload seluruh isi folder ini ke branch `main`.
3. Buka **Settings → Actions → General** dan pastikan Actions diizinkan.
4. Buka **Settings → Pages** dan pilih **GitHub Actions** sebagai source.
5. Setelah push, workflow `Deploy PNM to GitHub Pages` akan membuat situs.
6. Workflow `Collect Negative News` berjalan setiap jam dan juga dapat dijalankan manual melalui **Actions → Collect Negative News → Run workflow**.

## Cara kerja collector

GitHub Actions menjalankan `scripts/fetch_news.py`.
Collector mengambil RSS Google News dengan banyak query, menghapus duplikasi, mengklasifikasikan kategori/prioritas, mendeteksi indikasi Jawa Timur, lalu menyimpan hasil ke `data/news.json`.

Dashboard GitHub Pages hanya membaca `data/news.json`; browser tidak bertanggung jawab mengoleksi berita.

## Catatan penting

Google News RSS adalah sumber agregasi. Ini bukan jaminan seluruh berita internet akan terambil. Untuk sistem produksi, tambahkan sumber resmi/media yang relevan dan mekanisme arsip/validasi.

Label "negatif", prioritas, kategori, dan deteksi Jawa Timur adalah klasifikasi otomatis; bukan kesimpulan bahwa seseorang bersalah. Artikel perlu diverifikasi sebelum menjadi bahan resmi.
