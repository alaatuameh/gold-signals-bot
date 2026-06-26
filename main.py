import logging
import os
import base64
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحبا! أرسل صورة شارت الذهب وسأحللها 📊")

async def analyze_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("أرسل صورة الشارت 📸")
        return
    await update.message.reply_text("جاري التحليل... ⏳")
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"inline_data": {"mime_type": "image/jpeg", "data": image_base64}}, {"text": "حلل هذا الشارت وأعطني توصية BUY أو SELL مع نقطة الدخول وStop Loss وTake Profit"}]}]}
    response = requests.post(url, json=payload)
    result = response.json()
    text = result["candidates"][0]["content"]["parts"][0]["text"]
    await update.message.reply_text(text)

async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, analyze_chart))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
