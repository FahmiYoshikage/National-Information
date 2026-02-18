"""
Konfigurasi Bot Berita Nasional Indonesia
Semua RSS Feed dari berbagai sumber berita terpercaya
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── Telegram Config ────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")  # e.g. @channelname atau -100xxxxxxxx

# ─── Interval Pengecekan RSS (dalam menit) ──────────────────────────────────
# Catatan: di Azure Functions, interval diatur via CRON di function_app.py
# Variabel ini dipakai hanya untuk mode lokal (bot.py)
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "15"))

# ─── Batas maksimal artikel per feed per siklus (agar tidak spam) ───────────
MAX_ARTICLES_PER_FEED = int(os.getenv("MAX_ARTICLES_PER_FEED", "3"))

# ─── Azure Storage (menggantikan SQLite) ─────────────────────────────────────
# Connection string dari portal Azure → Storage Account → Access keys
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
# Nama tabel di Azure Table Storage
TABLE_NAME = os.getenv("TABLE_NAME", "SentArticles")

# ─── Semua RSS Feed yang Dicakup ─────────────────────────────────────────────
RSS_FEEDS = {
    # ── ANTARA NEWS ──────────────────────────────────────────────────────────
    "🇮🇩 Antara - Top News":   "https://www.antaranews.com/rss/top-news.xml",
    "🏛️ Antara - Politik":     "https://www.antaranews.com/rss/politik.xml",
    "⚖️ Antara - Hukum":       "https://www.antaranews.com/rss/hukum.xml",
    "📰 Antara - Terkini":     "https://www.antaranews.com/rss/terkini.xml",
    "💻 Antara - Tekno":       "https://www.antaranews.com/rss/tekno.xml",
    "🎓 Antara - Humaniora":   "https://www.antaranews.com/rss/humaniora.xml",

    # ── CNN INDONESIA ─────────────────────────────────────────────────────────
    "🌐 CNN Indonesia - Nasional":   "https://www.cnnindonesia.com/nasional/rss",
    "💻 CNN Indonesia - Teknologi":  "https://www.cnnindonesia.com/teknologi/rss",

    # ── CNBC INDONESIA ───────────────────────────────────────────────────────
    "📊 CNBC Indonesia - News":    "https://www.cnbcindonesia.com/news/rss",
    "📈 CNBC Indonesia - Market":  "https://www.cnbcindonesia.com/market/rss/",
    "🔬 CNBC Indonesia - Tech":    "https://www.cnbcindonesia.com/tech/rss/",

    # ── TEMPO ─────────────────────────────────────────────────────────────────
    "⏰ Tempo - Nasional": "http://rss.tempo.co/nasional",

    # ── REPUBLIKA ────────────────────────────────────────────────────────────
    "📋 Republika - Nasional": "https://www.republika.co.id/rss/nasional/",

    # ── DETIK ────────────────────────────────────────────────────────────────
    "🔴 Detik - Berita Utama": "https://news.detik.com/berita/rss",

    # ── SUARA.COM ────────────────────────────────────────────────────────────
    "📱 Suara.com - Tekno": "https://www.suara.com/rss/tekno",

    # ── DAILYSOCIAL ──────────────────────────────────────────────────────────
    "🚀 DailySocial - Startup & Tech": "https://dailysocial.id/rss",

    # ── KONTAN ───────────────────────────────────────────────────────────────
    "💰 Kontan - Keuangan": "https://rss.kontan.co.id/news/keuangan",

    # ── OKEZONE ──────────────────────────────────────────────────────────────
    "🎓 Okezone - Edukasi": "https://edukasi.okezone.com/rss",
}
