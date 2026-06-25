import os
import telebot
import re
import sys
from threading import Thread
from flask import Flask

# 1. Dummy web server for Render's port scanner
app = Flask('')

@app.route('/')
def home():
    return "Second Bot is alive and running!"

def run_web_server():
    # Force dynamic port binding for Render's requirements
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. Main Telegram Bot Logic (PASTE YOUR SECOND BOT'S TOKEN HERE)
BOT_TOKEN = "PASTE_YOUR_SECOND_BOT_TOKEN_HERE"
bot = telebot.TeleBot(BOT_TOKEN)

# Global trackers
video_counter = 0  # Total videos processed overall
ep = 1             # Episode tracker
manual_quality = None

@bot.message_handler(content_types=['video', 'document'], func=lambda message: True)
def handle_incoming_media(message):
    global video_counter, ep, manual_quality
    
    media = message.video or message.document
    if not media:
        return

    # Calculate exact quality loop stage across 4 versions (remainder of division by 4)
    if manual_quality:
        quality = manual_quality
    else:
        remainder = video_counter % 4
        if remainder == 0:
            quality = "480p [SD]"
        elif remainder == 1:
            quality = "720p [HD]"
        elif remainder == 2:
            quality = "1080p [FHD]"
        else:
            quality = "2160p [4K]"

    caption_text = (
        f"Episode :- {ep}\n"
        f"🗣 Language :- Hindi Dub\n"
        f"🟡 Quality :- {quality}\n"
        f"@NEW_HINDI_ANIME_OFFICIAL_DUB"
    )

    try:
        # Deliver the copied file with HTML format intact
        bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            caption=caption_text,
            parse_mode="HTML"
        )
        
        # Safe structural state updates
        if not manual_quality:
            video_counter += 1
            # Every 4 videos completed means one full episode set is done
            if video_counter % 4 == 0:
                ep += 1
        else:
            ep += 1
            
    except Exception as e:
        print(f"Error handling media: {e}")

@bot.message_handler(commands=['start'])
def command_start(message):
    if manual_quality:
        q = f"{manual_quality} (MANUAL LOCK)"
    else:
        remainder = video_counter % 4
        if remainder == 0:
            q = "480p [SD]"
        elif remainder == 1:
            q = "720p [HD]"
        elif remainder == 2:
            q = "1080p [FHD]"
        else:
            q = "2160p [4K]"
    
    status = f"👋 <b>Bot Status:</b>\n\n🔢 Next Episode: <code>Episode {ep}</code>\n🟡 Next Quality: <code>{q}</code>"
    bot.reply_to(message, status, parse_mode="HTML")

@bot.message_handler(commands=['setep'])
def command_setep(message):
    global ep
    match = re.search(r'\d+', message.text)
    if match:
        ep = int(match.group())
        bot.reply_to(message, f"✅ Next episode target set manually to: Episode {ep}")
    else:
        bot.reply_to(message, "❌ Use format: /setep 15")

@bot.message_handler(commands=['setquality'])
def command_setquality(message):
    global manual_quality, video_counter
    text = message.text.lower()
    
    if "480" in text:
        manual_quality = "480p [SD]"
        bot.reply_to(message, "✅ Quality locked to: <b>480p [SD]</b>", parse_mode="HTML")
    elif "720" in text:
        manual_quality = "720p [HD]"
        bot.reply_to(message, "✅ Quality locked to: <b>720p [HD]</b>", parse_mode="HTML")
    elif "1080" in text:
        manual_quality = "1080p [FHD]"
        bot.reply_to(message, "✅ Quality locked to: <b>1080p [FHD]</b>", parse_mode="HTML")
    elif "2160" in text or "4k" in text:
        manual_quality = "2160p [4K]"
        bot.reply_to(message, "✅ Quality locked to: <b>2160p [4K]</b>", parse_mode="HTML")
    elif "auto" in text or "reset" in text:
        manual_quality = None
        video_counter = 0
        bot.reply_to(message, "🔄 Restored to automatic <b>Auto-Rotation Mode</b> starting at 480p.", parse_mode="HTML")
    else:
        bot.reply_to(message, "❌ Provide a quality level!\nExamples: <code>/setquality 4k</code> or <code>/setquality auto</code>", parse_mode="HTML")

@bot.message_handler(commands=['restart'])
def command_restart(message):
    global ep, video_counter, manual_quality
    ep = 1
    video_counter = 0
    manual_quality = None
    bot.reply_to(message, "🔄 Bot system memory fully reset to Episode 1 & 480p [SD]!")

if __name__ == "__main__":
    server_thread = Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()
    
    print("🚀 SECOND CAPTION BOT ENGINE ACTIVE & WEB PORT OPEN...")
    bot.infinity_polling()
