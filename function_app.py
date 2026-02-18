"""
Azure Functions - Timer Trigger
Bot Berita Nasional Indonesia

Dipanggil otomatis oleh Azure setiap 15 menit via CRON expression.
Tidak butuh server yang terus hidup (scale to zero).
"""

import asyncio
import logging
import azure.functions as func
from datetime import date as date_type
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHANNEL_ID,
    MAX_ARTICLES_PER_FEED,
)
from database import init_table, is_sent, mark_sent, cleanup_old_articles
from fetcher import fetch_all_feeds, Article

# ─── Logging ─────────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)

# ─── Azure Functions App ──────────────────────────────────────────────────────
app = func.FunctionApp()

# ─── CRON Schedule ───────────────────────────────────────────────────────────
#  Format Azure (6 field): {detik} {menit} {jam} {hari} {bulan} {hari_minggu}
#  "0 */15 * * * *"  = setiap 15 menit tepat di detik ke-0
SCHEDULE = "0 */15 * * * *"


# ─── Format Pesan Telegram ────────────────────────────────────────────────────
def format_message(article: Article) -> str:
    lines = [
        f"<b>{article.source}</b>",
        f"📌 <b>{article.title}</b>",
    ]
    if article.published:
        lines.append(f"🕒 <i>{article.published}</i>")
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    if article.summary:
        lines.append(article.summary)
        lines.append("")
    lines.append(f'🔗 <a href="{article.url}">Baca selengkapnya</a>')
    return "\n".join(lines)


# ─── Kirim Artikel ke Telegram ────────────────────────────────────────────────
async def send_article(bot: Bot, article: Article) -> bool:
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
        # Fallback: kirim teks saja jika foto gagal
        if article.image_url and ("Wrong file" in str(e) or "Bad Request" in str(e)):
            try:
                await bot.send_message(
                    chat_id=TELEGRAM_CHANNEL_ID,
                    text=text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=False,
                )
                return True
            except TelegramError as e2:
                logger.error("Fallback kirim teks gagal [%s]: %s", article.url, e2)
        else:
            logger.error("Gagal kirim artikel [%s]: %s", article.url, e)
        return False


# ─── Logika Utama ─────────────────────────────────────────────────────────────
async def run_news_job() -> None:
    """Ambil semua feed, filter duplikat, kirim yang baru ke Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        logger.critical("TELEGRAM_BOT_TOKEN belum diset!")
        return
    if not TELEGRAM_CHANNEL_ID:
        logger.critical("TELEGRAM_CHANNEL_ID belum diset!")
        return

    # Pastikan tabel Azure Storage ada
    init_table()

    # Cleanup artikel lama (> 30 hari) — murah, dilakukan tiap invocation
    cleanup_old_articles(days=30)

    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    # Verifikasi koneksi bot
    try:
        me = await bot.get_me()
        logger.info("Bot terhubung: @%s", me.username)
    except TelegramError as e:
        logger.critical("Gagal konek ke Telegram: %s", e)
        return

    # Ambil semua artikel dari 17 feed
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
            # Delay antar pesan agar tidak kena rate-limit Telegram (30 msg/detik)
            await asyncio.sleep(1.5)

    logger.info(
        "Selesai. Terkirim: %d | Dilewati (duplikat): %d",
        sent_count, skip_count,
    )


# ─── Azure Timer Trigger Entry Point ─────────────────────────────────────────
@app.timer_trigger(
    schedule=SCHEDULE,
    arg_name="myTimer",
    run_on_startup=False,   # True saat testing lokal, False di production
    use_monitor=False,
)
async def news_timer_trigger(myTimer: func.TimerRequest) -> None:
    """
    Azure Functions Timer Trigger.
    Dipanggil Azure otomatis setiap 15 menit.
    """
    if myTimer.past_due:
        logger.warning("⚠️ Timer past due — invocation terlambat, lanjut proses.")

    logger.info("=== Bot Berita Nasional - Invocation START ===")
    await run_news_job()
    logger.info("=== Bot Berita Nasional - Invocation END ===")
