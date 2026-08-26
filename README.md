# PNM — Polri Negative News Monitor

## Akun demo
- Email: `admin@propam-jatim.go.id`
- Password: `PropamJatim2026!`

## Deploy ke GitHub Pages
1. Buat repository GitHub baru.
2. Upload seluruh isi folder ini.
3. Masuk **Settings → Pages**.
4. Pilih **GitHub Actions** sebagai source.
5. Push ke branch `main`. Workflow Pages akan melakukan build/deploy.

## Monitoring berita
Workflow `monitor.yml` menjalankan `scripts/fetch_news.py` secara berkala dan memperbarui `data/news.json`. Data dapat difilter menjadi Jawa Timur dari dashboard.

## PENTING — keamanan
Versi ini memakai login **frontend/static** agar langsung dapat dicoba di GitHub Pages tanpa membuat akun Supabase. Email/password berada di JavaScript frontend sehingga **bukan mekanisme keamanan untuk data rahasia**. Jangan gunakan kredensial ini sebagai proteksi data sensitif.

Untuk versi produksi internal, gunakan Supabase Auth atau backend/API dengan Row Level Security dan jangan menyimpan secret/service-role key di frontend.
