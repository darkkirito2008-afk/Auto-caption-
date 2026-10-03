import time
import re
import requests
from collections import defaultdict
import os

# ==================== CONFIG ====================
BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN_HERE"
CHANNELS = ["@NEW_ANIME_HINDI_DUB_OFFICIALL"]
LANGUAGE = "Hindi Dub"
# ================================================

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

current_episode = 1
qualities = ["480p [SD]", "720p [HD]", "1080p [FHD]", "2160p [4K]"]
episode_videos = defaultdict(list)
last_update_id = 0

def send_message(chat_id, text):
    try:
        requests.post(f"{API_URL}/sendMessage", json={
            "chat_id": chat_id, "text": text, "parse_mode": "Markdown"
        }, timeout=5)
    except:
        pass

def make_caption(ep, quality):
    return f"""Episode :- {ep}
🗣 Language :- {LANGUAGE}
🟡 Quality :- {quality}
{CHANNELS[0]}"""

def detect_episode(text):
    if not text:
        return None
    text = re.sub(r'(2160|1080|720|480)\s*p?', ' ', text.lower())
    for p in [r'(?:ep|episode|e)\s*[.\-_ ]*(\d{1,3})', r's\d{1,2}e(\d{1,3})', r'[\[\(](\d{1,3})[\]\)]', r'\b(\d{1,3})\b']:
        m = re.search(p, text)
        if m:
            num = int(m.group(1))
            if num not in [480, 720, 1080, 2160]:
                return num
    return None

def is_forwarded(msg):
    return any(k in msg for k in ["forward_from", "forward_from_chat", "forward_origin", "forward_sender_name"])

def edit_caption(chat_id, msg_id, caption):
    try:
        r = requests.post(f"{API_URL}/editMessageCaption", json={
            "chat_id": chat_id, "message_id": msg_id, "caption": caption
        }, timeout=6)
        return r.status_code == 200
    except:
        return False

def post_video(file_id, caption, chat_id=None):
    targets = [chat_id] if chat_id else CHANNELS
    for ch in targets:
        try:
            requests.post(f"{API_URL}/sendVideo", json={
                "chat_id": ch, "video": file_id, "caption": caption
            }, timeout=30)
        except:
            pass

def assign_and_update(ep):
    videos = episode_videos[ep]
    if not videos:
        return
    sorted_vids = sorted(videos, key=lambda x: x["size"])
    for i, v in enumerate(sorted_vids):
        quality = qualities[min(i, 3)]
        caption = make_caption(ep, quality)
        if v.get("msg_id") and v.get("is_channel"):
            edit_caption(v["chat_id"], v["msg_id"], caption)

def process_video(file_id, filename, caption_text, file_size, chat_id, msg_id=None, is_channel=False, forwarded=False):
    global current_episode
    ep = detect_episode(f"{filename or ''} {caption_text or ''}") or current_episode
    current_episode = ep

    episode_videos[ep].append({
        "size": file_size or 0,
        "file_id": file_id,
        "chat_id": chat_id,
        "msg_id": msg_id,
        "is_channel": is_channel
    })
    if len(episode_videos[ep]) > 4:
        episode_videos[ep] = episode_videos[ep][-4:]

    assign_and_update(ep)

    if not is_channel:
        sorted_vids = sorted(episode_videos[ep], key=lambda x: x["size"])
        rank = next((i for i, v in enumerate(sorted_vids) if v["file_id"] == file_id), 0)
        quality = qualities[min(rank, 3)]
        send_message(chat_id, f"🚀 Ep {ep} | {quality}")
        post_video(file_id, make_caption(ep, quality))

def handle_command(chat_id, text):
    global current_episode, episode_videos
    if text.startswith(("/start", "/help")):
        send_message(chat_id, f"🎬 *Fast Rank Bot*\nCurrent Ep: `{current_episode}`\n\n/status /set 5 /reset /clear")
    elif text.startswith("/status"):
        send_message(chat_id, f"Ep `{current_episode}`")
    elif text.startswith("/set"):
        try:
            current_episode = int(text.split()[1])
            send_message(chat_id, f"✅ Ep {current_episode}")
        except:
            send_message(chat_id, "Usage: /set 5")
    elif text.startswith("/reset"):
        current_episode = 1
        episode_videos.clear()
        send_message(chat_id, "✅ Reset")
    elif text.startswith("/clear"):
        episode_videos.clear()
        send_message(chat_id, "✅ Cleared")

def main():
    global last_update_id
    print("Bot started on cloud...")
    while True:
        try:
            r = requests.get(f"{API_URL}/getUpdates", params={
                "offset": last_update_id + 1,
                "timeout": 20
            }, timeout=25)
            data = r.json()
            if not data.get("ok"):
                time.sleep(2)
                continue

            for u in data["result"]:
                last_update_id = u["update_id"]

                msg = u.get("message")
                if msg:
                    cid = msg["chat"]["id"]
                    if "video" in msg:
                        v = msg["video"]
                        process_video(v["file_id"], v.get("file_name"), msg.get("caption"),
                                      v.get("file_size", 0), cid, forwarded=is_forwarded(msg))
                    elif msg.get("text", "").startswith("/"):
                        handle_command(cid, msg["text"])

                cp = u.get("channel_post")
                if cp and "video" in cp:
                    v = cp["video"]
                    process_video(v["file_id"], v.get("file_name"), cp.get("caption"),
                                  v.get("file_size", 0), cp["chat"]["id"], cp["message_id"],
                                  is_channel=True, forwarded=is_forwarded(cp))
        except Exception as e:
            print("Error:", e)
            time.sleep(3)

if __name__ == "__main__":
    main()