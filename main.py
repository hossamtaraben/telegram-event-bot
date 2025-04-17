import requests
from bs4 import BeautifulSoup
import json
import os
import time
from telegram import Bot

# === ENV VARIABLES ===
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")
WEB_URL = 'https://webook.com/en/explore?type=events'
CACHE_FILE = 'events_cache.json'
CHECK_INTERVAL = 60 * 10  # Check every 10 minutes

# === PREFERENCES ===
CATEGORY_PREFERENCES = {
    'sports': True,
    'concerts': True,
    'other': False  # Disable irrelevant categories
}

# Keywords for classifying events
CATEGORY_KEYWORDS = {
    'sports': ['football', 'match', 'game', 'tournament', 'sport'],
    'concerts': ['concert', 'music', 'live', 'band', 'artist']
}

bot = Bot(token=TELEGRAM_TOKEN)

# === CACHE UTILITIES ===
def load_cache():
    return json.load(open(CACHE_FILE)) if os.path.exists(CACHE_FILE) else []

def save_cache(seen_links):
    with open(CACHE_FILE, 'w') as f:
        json.dump(seen_links, f)

# === CATEGORY DETECTION ===
def get_event_category(event_text):
    text = event_text.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(k in text for k in keywords):
            return cat
    return 'other'

# === FETCH EVENTS FROM SITE ===
def fetch_events():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(WEB_URL, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    event_cards = soup.select('.css-1dbjc4n.r-1loqt21.r-13awgt0.r-18u37iz.r-1wtj0ep')
    events = []

    for card in event_cards:
        link_tag = card.find('a', href=True)
        img_tag = card.find('img', src=True)
        title_tag = card.find('div', class_='title')

        if link_tag and img_tag:
            link = 'https://webook.com' + link_tag['href']
            img = img_tag['src']
            title = title_tag.text.strip() if title_tag else ''
            category = get_event_category(f"{title} {link}")
            if CATEGORY_PREFERENCES.get(category, False):
                events.append({'link': link, 'img': img, 'title': title, 'category': category})
    return events

# === SEND TO TELEGRAM ===
def send_telegram_message(event):
    emoji = '🎵' if event['category'] == 'concerts' else '🏆'
    msg = f"{emoji} *New {event['category'].capitalize()} Event!*\n{event['title']}\n{event['link']}"
    try:
        bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=event['img'], caption=msg, parse_mode="Markdown")
        print(f"✅ Sent: {event['title']}")
    except Exception as e:
        print(f"❌ Telegram Error: {e}")

# === MAIN LOOP ===
def main():
    print("🚀 Bot is running...")
    seen_links = load_cache()

     send_telegram_message({
        'link': 'https://webook.com',
        'img': 'https://via.placeholder.com/300x200.png?text=Test+Image',
        'title': '✅ Bot Deployed Successfully',
        'category': 'concerts'
    })

    while True:
        try:
            events = fetch_events()
            new_events = [e for e in events if e['link'] not in seen_links]

            for event in new_events:
                send_telegram_message(event)

            if new_events:
                seen_links = [e['link'] for e in events]
                save_cache(seen_links)

        except Exception as e:
            print(f"❌ Unexpected error: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
