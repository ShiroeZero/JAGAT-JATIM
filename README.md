# PNM — Polri Negative News Monitor

> **Polri Negative News Monitor (PNM)** adalah aplikasi web-based untuk membantu monitoring, klasifikasi, dan penyaringan pemberitaan yang berkaitan dengan Polri, khususnya berita mengenai anggota/oknum Polri serta pemberitaan terkait jajaran Polda Jawa Timur.

![Status](https://img.shields.io/badge/status-active-success)
![Platform](https://img.shields.io/badge/platform-GitHub%20Pages-121013)
![Automation](https://img.shields.io/badge/automation-GitHub%20Actions-2088FF)
![Python](https://img.shields.io/badge/Python-3.12-3776AB)
![License](https://img.shields.io/badge/license-GPL--3.0-blue)

---

## 📌 Overview

PNM dirancang sebagai **dashboard monitoring berita** yang mengumpulkan pemberitaan dari sumber berita melalui RSS/search feed, kemudian melakukan pemrosesan dan klasifikasi otomatis.

Sistem membantu pengguna untuk:

- Memantau pemberitaan terkait Polri.
- Membedakan berita mengenai **oknum/anggota Polri** dengan berita **pengungkapan kasus oleh Polri**.
- Memfilter berita berdasarkan **tanggal**.
- Memfilter pemberitaan berdasarkan **wilayah Jawa Timur**.
- Mengelompokkan berita berdasarkan **39 Polres jajaran**.
- Melihat tingkat prioritas pemberitaan.
- Melakukan pencarian berdasarkan judul, sumber, wilayah, Polres, dan kategori.
- Memperbarui data secara otomatis menggunakan GitHub Actions.
- Menampilkan data terbaru melalui GitHub Pages.

> **Catatan:** PNM merupakan alat bantu monitoring dan klasifikasi otomatis. Hasil klasifikasi tidak dapat dianggap sebagai verifikasi fakta, penetapan kesalahan, atau kesimpulan hukum.

---

# 🚀 Fitur Utama

## 1. Monitoring Berita Otomatis

Collector berjalan menggunakan **GitHub Actions** dan mengambil pemberitaan secara berkala.

Alur sistem:

```text
Sumber Berita
     │
     ▼
RSS / News Search
     │
     ▼
GitHub Actions
     │
     ├── Pengumpulan berita
     ├── Deduplicate
     ├── Deteksi wilayah
     ├── Deteksi Polres
     ├── Klasifikasi berita
     └── Penentuan prioritas
     │
     ▼
data/news.json
     │
     ▼
GitHub Pages
     │
     ▼
Dashboard PNM
