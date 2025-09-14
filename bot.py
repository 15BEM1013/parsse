import asyncio
import threading
import re
import requests
import os
from datetime import datetime
import pytz
import time
from telethon import TelegramClient, events
from flask import Flask
import telegram

# Initialize Flask app
app = Flask(__name__)

# Telegram API credentials
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Validate environment variables
if not all([API_ID, API_HASH, BOT_TOKEN, CHAT_ID]):
    raise ValueError("Missing required environment variables: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_BOT_TOKEN, or TELEGRAM_CHAT_ID")

# Initialize clients
client = TelegramClient('bot_session', API_ID, API_HASH)
bot = telegram.Bot(token=BOT_TOKEN)

# Channels to monitor
CHANNELS = ['cryptocapitalgl', 'Official_GCR', 'THE_WOLFREAL']

# Regex patterns
PATTERNS = {
    'pair': r'(?:Coin|Pair)\s*[:\-]?\s*([A-Z0-9]+/[A-Z0-9]+)',
    'trade_type': r'(LONG|SHORT|BUY|SELL)',
    'leverage': r'(?:Leverage|Lev)\s*[:\-]?\s*(\d+x)',
    'entry': r'(?:Entry|Buy at|Enter at)\s*[:\-]?\s*([\d.]+(?:\s*-\s*[\d.]+)?)',
    'targets': r'(?:Take-Profit|Targets?|TP)\s*[:\-]?\s*([\d.\s\-]+)',
    'stop_loss': r'(?:Stop-Loss|SL)\s*[:\-]?\s*([\d.]+)'
}

async def parse_signal(text):
    signal = {}
    for key, pattern in PATTERNS.items():
        match = re.search(pattern, text, re.IGNORECASE)
        signal[key] = match.group(1) if match else 'Not found'
    return signal

async def format_signal_message(signal, original_text, timestamp):
    ist = pytz.timezone('Asia/Kolkata')
    formatted_time = timestamp.astimezone(ist).strftime('%Y-%m-%d %H:%M:%S IST')
    message = (
        f"📊 *New Trading Signal*\n\n"
        f"**Coin/Pair**: {signal['pair']}\n"
        f"**Trade Type**: {signal['trade_type']}\n"
        f"**Leverage**: {signal['leverage']}\n"
        f"**Entry Price**: {signal['entry']}\n"
        f"**Take-Profit/Targets**: {signal['targets']}\n"
        f"**Stop-Loss**: {signal['stop_loss']}\n\n"
        f"**Original Message**:\n{original_text}\n\n"
        f"**Time**: {formatted_time}"
    )
    return message

async def send_to_chat(message):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')
    except Exception as e:
        print(f"Error sending message: {e}")

@client.on(events.NewMessage(chats=CHANNELS))
async def handle_new_message(event):
    message = event.message
    text = message.text
    timestamp = message.date
    signal = await parse_signal(text)
    if any(signal[key] != 'Not found' for key in ['pair', 'trade_type', 'entry']):
        formatted_message = await format_signal_message(signal, text, timestamp)
        await send_to_chat(formatted_message)

async def start_bot():
    await client.start(bot_token=BOT_TOKEN)
    print("Bot is running and listening for signals...")
    await client.run_until_disconnected()

@app.route('/')
def home():
    return "Crypto Signal Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    bot_thread = threading.Thread(target=lambda: asyncio.run(start_bot()))
    bot_thread.start()
    run_flask()
