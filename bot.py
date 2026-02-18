"""
Bot Berita Nasional Indonesia
Mengirim berita terbaru dari 17 sumber RSS ke channel/group Telegram

Jalankan: python bot.py
"""

import asyncio
import logging
import schedule
import time
from datetime import datetime, date as date_type
from threading import Thread
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHANNEL_ID,
    CHECK_INTERVAL_MINUTES,
)
from database import init_db, is_sent, mark_sent, cleanup_old_articles
from fetcher import fetch_all_feeds, Article

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ─── Format Pesan Telegram ────────────────────────────────────────────────────
def format_message(article: Article) -> str:
    """Buat teks pesan HTML untuk Telegram."""
    lines = [
        f"<b>{article.source}</b>",
        "",
        f"📌 <b>{article.title}</b>",
    ]

    if article.published:
        lines.append(f"🕒 {article.published}")

    if article.summary:
        lines.append("")
        lines.append(article.summary)

    lines.append("")
    lines.append(f'🔗 <a href="{article.url}">Baca selengkapnya</a>')

    return "\n".join(lines)


# ─── Kirim Artikel ke Telegram ────────────────────────────────────────────────
async def send_article(bot: Bot, article: Article) -> bool:
    """Kirim satu artikel; kembalikan True jika berhasil."""
    text = format_message(article)
    try:
        if article.image_url:
            await bot.send_photo(
                chat_id=TELEGRAM_CHANNEL_ID,
                photo=article.image_url,
                caption=text,
                parse_mode=ParseMode.HTML,
            )
        else:
            await bot.send_message(
                chat_id=TELEGRAM_CHANNEL_ID,
                text=text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=False,
            )
        return True
    except TelegramError as e:
        # Jika foto gagal (link rusak), coba kirim teks saja
        if article.image_url and "Wrong file" in str(e):
            try:
                await bot.send_message(
                    chat_id=TELEGRAM_CHANNEL_ID,
                    text=text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=False,
                )
                return True
            except TelegramError as e2:
                logger.error("Gagal kirim teks saja [%s]: %s", article.url, e2)
        else:
            logger.error("Gagal kirim artikel [%s]: %s", article.url, e)
        return False


# ─── Siklus Pengecekan Utama ──────────────────────────────────────────────────
async def check_and_send(bot: Bot) -> None:
    """Ambil semua feed, filter duplikat, dan kirim yang baru."""
    logger.info("== Mulai pengecekan berita terbaru ==")
    articles = fetch_all_feeds()
    logger.info("Total artikel dari semua feed: %d", len(articles))

    sent_count = 0
    skip_count = 0

    for article in articles:
        if is_sent(article.url):
            skip_count += 1
            continue

        success = await send_article(bot, article)
        if success:
            mark_sent(article.url)
            sent_count += 1
            # Delay antar pesan agar tidak kena rate-limit Telegram
            await asyncio.sleep(1.5)

    logger.info(
        "== Selesai. Terkirim: %d | Dilewati (duplikat): %d ==",
        sent_count, skip_count,
    )


# ─── Scheduler ───────────────────────────────────────────────────────────────
def run_scheduler(bot: Bot, loop: asyncio.AbstractEventLoop) -> None:
    """Jalankan scheduler di thread terpisah."""
    last_cleanup: date_type = date_type.today()

    def job():
        nonlocal last_cleanup
        asyncio.run_coroutine_threadsafe(check_and_send(bot), loop).result()

        # Cleanup DB sekali sehari
        today = date_type.today()
        if today != last_cleanup:
            cleanup_old_articles(days=30)
            last_cleanup = today

    # Jalankan langsung saat bot pertama kali start
    job()

    # Jadwalkan sesuai interval
    schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(job)
    logger.info(
        "Scheduler aktif: pengecekan setiap %d menit.", CHECK_INTERVAL_MINUTES
    )

    while True:
        schedule.run_pending()
        time.sleep(10)


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────
async def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.critical("TELEGRAM_BOT_TOKEN belum diset di file .env!")
        return
    if not TELEGRAM_CHANNEL_ID:
        logger.critical("TELEGRAM_CHANNEL_ID belum diset di file .env!")
        return

    # Inisialisasi database
    init_db()

    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    # Verifikasi koneksi bot
    try:
        me = await bot.get_me()
        logger.info("Bot terhubung: @%s (%s)", me.username, me.full_name)
    except TelegramError as e:
        logger.critical("Gagal konek ke Telegram: %s", e)
        return

    # Kirim pesan startup ke channel
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHANNEL_ID,
            text=(
                "🤖 <b>Bot Berita Nasional Indonesia aktif!</b>\n\n"
                "Sumber berita:\n"
                "• 🇮🇩 Antara News (Top News, Politik, Hukum, Terkini, Tekno, Humaniora)\n"
                "• 🌐 CNN Indonesia (Nasional, Teknologi)\n"
                "• 📊 CNBC Indonesia (News, Market, Tech)\n"
                "• ⏰ Tempo Nasional\n"
                "• 📋 Republika Nasional\n"
                "• 🔴 Detik Berita Utama\n"
                "• 📱 Suara.com Tekno\n"
                "• 🚀 DailySocial (Startup & Tech)\n"
                "• 💰 Kontan Keuangan\n"
                "• 🎓 Okezone Edukasi\n\n"
                f"⏱ Update setiap <b>{CHECK_INTERVAL_MINUTES} menit</b>"
            ),
            parse_mode=ParseMode.HTML,
        )
    except TelegramError as e:
        logger.warning("Gagal kirim pesan startup: %s", e)

    # Jalankan loop asyncio dan scheduler di thread terpisah
    loop = asyncio.get_event_loop()
    scheduler_thread = Thread(
        target=run_scheduler, args=(bot, loop), daemon=True
    )
    scheduler_thread.start()

    # Jaga agar program tetap berjalan
    logger.info("Bot berjalan. Tekan Ctrl+C untuk berhenti.")
    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Bot dihentikan oleh pengguna.")


if __name__ == "__main__":
    asyncio.run(main())
