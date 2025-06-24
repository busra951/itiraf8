#!/usr/bin/env python3
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.error import BadRequest
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Bot ayarların
BOT_TOKEN      = "7936867639:AAGJLC0rDQOG-woIJQvvcn5-i7anHGhK2wg"
ADMIN_GROUP_ID = -1002532660895 # Admin grubu
CHANNEL_ID     = -1002470083664  # Hedef kanal
KANAL_LINK     = "https://t.me/ankara_istanbul7"  # İtiraf grubu
BOT_LINK       = "https://t.me/goygoyitiraf_bot?start"  # Bot linki

awaiting_confession = set()

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return

    keyboard = [
        [InlineKeyboardButton("✅ İtiraf Et", callback_data="start_confess")],
        [InlineKeyboardButton("İtiraf grubuna gitmek için buraya tıkla", url=KANAL_LINK)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Anonim olarak bir itiraf göndermek ister misin?\n\n"
        "Aşağıdaki butona tıkla ve itirafını yaz!\n\n"
        "Tüm itirafları görmek için itiraf grubumuza katılabilirsin.",
        reply_markup=reply_markup
    )

async def tanitim_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("İtiraf etmek için buraya tıkla", url=BOT_LINK)],
        [InlineKeyboardButton("İtiraf grubuna gitmek için buraya tıkla", url=KANAL_LINK)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "✨ Anonim itiraf etmek için aşağıdaki butonu kullan.\n"
        "Tüm itirafları görmek için itiraf grubumuza katıl!",
        reply_markup=reply_markup
    )

async def start_cb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    await cq.edit_message_reply_markup(None)

    if cq.data == "start_confess":
        awaiting_confession.add(cq.from_user.id)
        await cq.message.reply_text("✍️ Lütfen itiraf metnini yazın:")
    else:
        await cq.message.reply_text(
            "❌ İtiraf etmekten vazgeçildi. Yeniden başlamak için /start komutunu kullanabilirsin."
        )

async def confession_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private" or not update.message.text:
        return

    user_id = update.effective_user.id
    if user_id not in awaiting_confession:
        return

    text = update.message.text.strip()
    awaiting_confession.remove(user_id)

    keyboard = [
        [
            InlineKeyboardButton("✅ Onayla", callback_data=f"approve|{text.replace('|',' ')}"),
            InlineKeyboardButton("❌ Reddet", callback_data=f"reject|{text.replace('|',' ')}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=ADMIN_GROUP_ID,
        text=f"📢 Yeni İtiraf:\n\n{text}",
        reply_markup=reply_markup
    )

    await update.message.reply_text(
        "🙌 İtirafınız yöneticilere iletildi, teşekkürler!\n\n"
        f"İtiraf grubumuza katılmak için: {KANAL_LINK}"
    )

async def admin_approval_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, confession = query.data.split("|", 1)

    await query.edit_message_reply_markup(reply_markup=None)

    if action == "approve":
        # Mesajı iki gömülü bağlantı ile alt alta gönder
        text = (
            f"🙊 Yeni bir itiraf var:\n\n"
            f"{confession}\n\n"
            f"[İtiraf etmek için buraya tıkla]({BOT_LINK})\n"
            f"[İtiraf grubuna gitmek için buraya tıkla!]({KANAL_LINK})"
        )
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=text,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        await query.message.reply_text("✅ İtiraf kanalda paylaşıldı.")
    else:
        await query.message.reply_text("❌ İtiraf reddedildi.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    error = context.error
    if isinstance(error, BadRequest) and "too old" in str(error).lower():
        return
    print(f"Unhandled error: {error!r}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("tanitim", tanitim_cmd))
    app.add_handler(CallbackQueryHandler(start_cb_handler, pattern="^start_"))
    app.add_handler(CallbackQueryHandler(admin_approval_handler, pattern="^(approve|reject)\|"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, confession_handler))
    app.add_error_handler(error_handler)

    print("Bot çalışıyor…")
    app.run_polling()

if __name__ == "__main__":
    main()
