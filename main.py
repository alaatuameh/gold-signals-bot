import os
import base64
import requests
import threading
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TWELVEDATA_API_KEY = os.environ.get("TWELVEDATA_API_KEY")
CHAT_ID = "8091574168"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    def log_message(self, format, *args):
        pass

def run_server():
    server = HTTPServer(("0.0.0.0", 10000), Handler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Send me a gold chart image and I will analyze it!")

async def analyze_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Please send a chart image!")
        return
    await update.message.reply_text("Analyzing...")
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"inline_data": {"mime_type": "image/jpeg", "data": image_base64}}, {"text": "Analyze this gold chart and give BUY or SELL signal with entry point, Stop Loss, and Take Profit levels."}]}]}
    response = requests.post(url, json=payload)
    result = response.json()
    text = result["candidates"][0]["content"]["parts"][0]["text"]
    await update.message.reply_text(text)

async def auto_signal(bot):
    while True:
        try:
            url = f"https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=1h&outputsize=10&apikey={TWELVEDATA_API_KEY}"
            response = requests.get(url)
            data = response.json()
            values = data["values"]
            closes = [float(v["close"]) for v in values]
            latest = closes[0]
            prev = closes[1]
            change = latest - prev
            if change > 2:
                signal = f"🟢 BUY SIGNAL\nXAU/USD\nPrice: {latest}\nEntry: {latest}\nSL: {latest - 10}\nTP: {latest + 20}"
            elif change < -2:
                signal = f"🔴 SELL SIGNAL\nXAU/USD\nPrice: {latest}\nEntry: {latest}\nSL: {latest + 10}\nTP: {latest - 20}"
            else:
                signal = f"⏳ No clear signal now\nXAU/USD Price: {latest}"
            await bot.send_message(chat_id=CHAT_ID, text=signal)
        except Exception as e:
            print(f"Auto signal error: {e}")
        await asyncio.sleep(3600)

def main():
    threading.Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, analyze_chart))
    loop = asyncio.get_event_loop()
    loop.create_task(auto_signal(app.bot))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
