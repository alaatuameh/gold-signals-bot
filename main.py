import threading
import os
import requests
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

GEMINI_PROMPT = """You are a gold XAUUSD trading expert.
Analyze this chart and reply in Arabic with:
1. Trend direction up or down or neutral
2. Support and resistance levels
3. Recommendation BUY or SELL or WAIT
4. Entry point
5. Stop Loss SL
6. Take Profit TP
7. Confidence percentage
Reply in Arabic only, clear and organized."""

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
    await update.message.reply_text(
        "Welcome! Send me a gold chart image and I will analyze it!\n"
        "You will get: Trend, Entry, SL, TP"
    )

async def analyze_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Please send a chart image!")
        return

    await update.message.reply_text("Analyzing chart, please wait...")

    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-8b:generateContent"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GEMINI_API_KEY}"
        }
        payload = {
            "contents": [{
                "parts": [
                    {"inline_data": {"mime_type": "image/jpeg", "data": image_base64}},
                    {"text": GEMINI_PROMPT}
                ]
            }]
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        result = response.json()

        if "candidates" in result and result["candidates"]:
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            await update.message.reply_text(text)
        else:
            await update.message.reply_text(f"Error from Gemini: {result}")

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

def main():
    threading.Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, analyze_chart))
    print("Bot started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
