import asyncio
import base64
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from http.server import HTTPServer, BaseHTTPRequestHandler

GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
TWELVEDATA_API_KEY = "YOUR_TWELVEDATA_API_KEY"
CHAT_ID = "YOUR_CHAT_ID"
BOT_TOKEN = "YOUR_BOT_TOKEN"

class Handler(BaseHTTPRequestHandler):
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
    payload = {
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": "image/jpeg", "data": image_base64}},
                {"text": "Analyze this gold chart and give a trading signal: BUY or SELL with entry, SL, TP."}
            ]
        }]
    }

    try:
        response = requests.post(url, json=payload)
        result = response.json()

        # ✅ الإصلاح هنا
        if "candidates" in result and result["candidates"]:
            text = result["candidates"][0]["content"]["parts"][0]["text"]
        else:
            print("Gemini error response:", result)
            await update.message.reply_text("❌ Error analyzing chart, please try again.")
            return

        await update.message.reply_text(text)

    except Exception as e:
        await update.message.reply_text(f"❌ Exception: {str(e)}")

async def auto_signal(bot):
    while True:
        try:
            url = f"https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=1h&outputsize=10&apikey={TWELVEDATA_API_KEY}"
            response = requests.get(url)
            data = response.json()

            # ✅ الإصلاح هنا
            if "values" not in data:
                print("Twelve Data error:", data)
                await asyncio.sleep(60)
                continue

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
            print(f"auto_signal error: {e}")

        await asyncio.sleep(3600)  # كل ساعة

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, analyze_chart))

    asyncio.get_event_loop().run_in_executor(None, run_server)

    async with app:
        await app.start()
        await asyncio.gather(
            app.updater.start_polling(),
            auto_signal(app.bot)
        )
        await app.stop()

if name == "main":
    asyncio.run(main())
