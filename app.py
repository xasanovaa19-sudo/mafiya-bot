import os
import random
import threading
import asyncio
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Render/FPS.ms uxlab qolmasligi uchun veb-server
app = Flask(__name__)

@app.route('/')
def home():
    return "Mafiya boti ishlayapti!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# O'yin holati (xotirada saqlanadi)
games = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! Men Mafiya botiman. O'yinni boshlash uchun guruhda /newgame buyrug'ini yuboring.")

async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in games:
        await update.message.reply_text("Bu guruhda o'yin allaqachon boshlangan!")
        return
    
    games[chat_id] = {"players": {}, "state": "joining", "roles": {}}
    await update.message.reply_text(
        "🕵️‍♂️ **Mafiya o'yini boshlandi!**\n\n"
        "Qatnashish uchun pastdagi tugmani bosing. Kamida 4 kishi kerak.\n"
        "Tayyor bo'lgach, /startgame buyrug'ini yuboring.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Qo'shilish", callback_data="join")]
        ])
    )

async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user = query.from_user

    if chat_id not in games or games[chat_id]["state"] != "joining":
        await query.message.reply_text("O'yin hozir qo'shilish uchun ochiq emas.")
        return

    if user.id in games[chat_id]["players"]:
        await query.message.reply_text(f"{user.first_name}, siz allaqachon qo'shilgansiz!")
        return

    games[chat_id]["players"][user.id] = user.first_name
    await query.message.reply_text(f"✅ {user.first_name} o'yinga qo'shildi! (Jami: {len(games[chat_id]['players'])} kishi)")

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in games:
        await update.message.reply_text("Avval /newgame buyrug'i bilan o'yin yarating.")
        return
    
    game = games[chat_id]
    if len(game["players"]) < 4:
        await update.message.reply_text("O'yinni boshlash uchun kamida 4 kishi kerak!")
        return

    game["state"] = "playing"
    player_ids = list(game["players"].keys())
    
    # Rollarni taqsimlash (4 kishi uchun 1 mafiya, 3 tinch aholi)
    mafia_id = random.choice(player_ids)
    game["roles"] = {pid: ("mafiya" if pid == mafia_id else "tinch") for pid in player_ids}

    # Har bir o'yinchiga rolini shaxsiy xabar orqali yuborish
    for pid, role in game["roles"].items():
        try:
            role_text = "🔪 Siz **Mafiyasiz**! Kechasi odamlarni o'ldirishingiz mumkin." if role == "mafiya" else "👨‍🌾 Siz **Tinch aholisiz**! Kunduzi mafiyani toping."
            await context.bot.send_message(chat_id=pid, text=role_text, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"Diqqat: {game['players'][pid]} ga shaxsiy xabar yuborib bo'lmadi. Iltimos, botga shaxsiy xabar yozing.")

    await update.message.reply_text(
        "🌙 **O'yin boshlandi! Tun tushdi.**\n\n"
        "Har bir o'yinchi o'z rolini shaxsiy xabarda ko'rdi. Hozir hamma 'uxlayapti'."
    )
    # Keyingi bosqichlar (tun harakati, ovoz berish) keyinroq qo'shiladi
    # Hozircha o'yinni yakunlaymiz
    del games[chat_id]
    await asyncio.sleep(5)
    await update.message.reply_text("O'yinning keyingi qismlari tez orada qo'shiladi! Hozircha sinov tugadi.")

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("XATO: BOT_TOKEN topilmadi!")
        return

    threading.Thread(target=run_web_server, daemon=True).start()

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("newgame", new_game))
    application.add_handler(CommandHandler("startgame", start_game))
    application.add_handler(CallbackQueryHandler(join_game, pattern="^join$"))
    
    print("Mafiya boti ishga tushdi...")
    application.run_polling()

if __name__ == '__main__':
    main()
