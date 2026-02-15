import os
import threading
import re
import secrets
import requests
import time
from flask import Flask
from telebot import TeleBot
import logging

# ==================================================
# LOGGING CONFIGURATION
# ==================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================================================
# ENVIRONMENT VARIABLES
# ==================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHANNEL_ID = int(os.getenv("TELEGRAM_CHANNEL_ID", "0"))
RENTRY_CSRF_TOKEN = os.getenv("RENTRY_CSRF_TOKEN")
LINKVERTISE_TAG_ID = os.getenv("LINKVERTISE_TAG_ID")
DISCORD_WEBHOOK_1 = os.getenv("DISCORD_WEBHOOK_1")
DISCORD_WEBHOOK_2 = os.getenv("DISCORD_WEBHOOK_2")

# Validate required environment variables
required_vars = {
    "BOT_TOKEN": BOT_TOKEN,
    "TELEGRAM_CHANNEL_ID": TELEGRAM_CHANNEL_ID,
    "RENTRY_CSRF_TOKEN": RENTRY_CSRF_TOKEN,
    "LINKVERTISE_TAG_ID": LINKVERTISE_TAG_ID,
    "DISCORD_WEBHOOK_1": DISCORD_WEBHOOK_1,
    "DISCORD_WEBHOOK_2": DISCORD_WEBHOOK_2
}

missing_vars = [key for key, value in required_vars.items() if not value or value == "0"]
if missing_vars:
    logger.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# ==================================================
# TELEGRAM BOT
# ==================================================

bot = TeleBot(BOT_TOKEN, parse_mode=None)
logger.info("✅ Telegram bot initialized")

# ==================================================
# FLASK KEEP-ALIVE (RENDER / UPTIMEROBOT)
# ==================================================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive and running! ✅", 200

@app.route("/health")
def health():
    return {"status": "healthy", "bot": "running"}, 200

def run_flask():
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

# ==================================================
# RENTRY (WITH RETRY LOGIC)
# ==================================================

def create_rentry_paste(content: str, max_retries=3):
    """Create a Rentry paste with retry logic"""
    for attempt in range(max_retries):
        try:
            session = requests.Session()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://rentry.co/",
                "X-CSRFToken": RENTRY_CSRF_TOKEN
            })

            payload = {
                "text": content,
                "edit_code": secrets.token_hex(8)
            }

            response = session.post(
                "https://rentry.co/api/new",
                data=payload,
                timeout=15
            )

            response.raise_for_status()
            data = response.json()

            if "url" not in data:
                raise Exception(f"Invalid Rentry response: {data}")

            logger.info(f"✅ Rentry paste created: {data['url']}")
            return data["url"]

        except requests.exceptions.Timeout:
            logger.warning(f"⚠️ Rentry timeout (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            raise Exception("Rentry request timed out after multiple attempts")

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Rentry error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            raise Exception(f"Rentry failed: {e}")

        except Exception as e:
            logger.error(f"❌ Unexpected error creating Rentry paste: {e}")
            raise

    raise Exception("Failed to create Rentry paste after all retries")

# ==================================================
# LINKVERTISE
# ==================================================

def linkvertise_lock(url: str) -> str:
    """Create a Linkvertise locked URL"""
    try:
        encoded_url = requests.utils.quote(url, safe='')
        lv_url = f"https://linkvertise.com/{LINKVERTISE_TAG_ID}?r={encoded_url}"
        logger.info(f"✅ Linkvertise URL created")
        return lv_url
    except Exception as e:
        logger.error(f"❌ Error creating Linkvertise URL: {e}")
        raise

# ==================================================
# DISCORD
# ==================================================

def post_to_discord(webhook_url, image_url, name, link, max_retries=2):
    """Post to Discord webhook with retry logic"""
    for attempt in range(max_retries):
        try:
            payload = {
                "content": f"**{name}**\n\n{link}",
                "embeds": [{
                    "image": {"url": image_url},
                    "color": 3447003
                }]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("✅ Posted to Discord successfully")
            return
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Discord post failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            logger.error(f"❌ Failed to post to Discord after {max_retries} attempts")

# ==================================================
# TELEGRAM CHANNEL
# ==================================================

def post_to_telegram_channel(file_id, name, link, max_retries=2):
    """Post to Telegram channel with retry logic"""
    for attempt in range(max_retries):
        try:
            caption = f"📦 {name}\n\n🔗 {link}"
            bot.send_photo(
                TELEGRAM_CHANNEL_ID,
                file_id,
                caption=caption,
                parse_mode=None
            )
            logger.info("✅ Posted to Telegram channel successfully")
            return
            
        except Exception as e:
            logger.warning(f"⚠️ Telegram channel post failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            logger.error(f"❌ Failed to post to Telegram channel after {max_retries} attempts")
            raise

# ==================================================
# PIPELINE
# ==================================================

def process_pipeline(photo_file_id, name, mega_link):
    """Process the complete pipeline: Rentry -> Linkvertise -> Post"""
    logger.info(f"🚀 Pipeline started for: {name}")

    try:
        # Step 1: Create first Rentry paste with MEGA link
        logger.info("📝 Creating first Rentry paste...")
        rentry1 = create_rentry_paste(
            f"📦 {name}\n\n⬇️ Download:\n{mega_link}"
        )

        # Step 2: Create first Linkvertise link
        logger.info("🔗 Creating first Linkvertise link...")
        lv1 = linkvertise_lock(rentry1)

        # Step 3: Create second Rentry paste with first Linkvertise
        logger.info("📝 Creating second Rentry paste...")
        rentry2 = create_rentry_paste(
            f"📦 {name}\n\n⬇️ Continue:\n{lv1}"
        )

        # Step 4: Create final Linkvertise link
        logger.info("🔗 Creating final Linkvertise link...")
        lv2 = linkvertise_lock(rentry2)

        # Step 5: Get Telegram image URL
        logger.info("🖼️ Getting image URL...")
        file_info = bot.get_file(photo_file_id)
        image_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        # Step 6: Post to all platforms
        logger.info("📤 Posting to all platforms...")
        post_to_discord(DISCORD_WEBHOOK_1, image_url, name, lv2)
        post_to_discord(DISCORD_WEBHOOK_2, image_url, name, lv2)
        post_to_telegram_channel(photo_file_id, name, lv2)

        logger.info("✅ Pipeline completed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        raise

# ==================================================
# MESSAGE HANDLER
# ==================================================

@bot.message_handler(content_types=["photo"])
def handle_message(message):
    """Handle incoming photo messages with caption"""
    logger.info(f"📩 Message received from user {message.from_user.id}")

    try:
        # Get photo file ID
        photo_file_id = message.photo[-1].file_id
        
        # Get caption/text
        text = message.caption or ""

        if not text:
            bot.reply_to(message, "❌ Please send an image with a caption containing the name and link.")
            return

        # Extract link
        link_match = re.search(r"https?://[^\s]+", text)
        if not link_match:
            bot.reply_to(message, "❌ No valid link found in caption. Please include a MEGA link.")
            return

        mega_link = link_match.group(0)
        
        # Extract name (everything except the link)
        name = text.replace(mega_link, "").strip()

        if not name:
            bot.reply_to(message, "❌ Name is missing. Please include a name before or after the link.")
            return

        # Confirm processing started
        processing_msg = bot.reply_to(message, "⏳ Processing your request... Please wait.")

        # Process the pipeline
        process_pipeline(photo_file_id, name, mega_link)
        
        # Success message
        bot.edit_message_text(
            "✅ Done! Your content has been processed and posted to all channels.",
            processing_msg.chat.id,
            processing_msg.message_id
        )

    except Exception as e:
        logger.error(f"❌ Error handling message: {e}")
        error_message = f"❌ Error occurred:\n{str(e)[:200]}"
        try:
            bot.reply_to(message, error_message, parse_mode=None)
        except:
            bot.reply_to(message, "❌ An error occurred while processing your request.")

# ==================================================
# START COMMAND
# ==================================================

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Handle /start and /help commands"""
    welcome_text = """
👋 Welcome to the Bot!

📸 Send me a photo with a caption containing:
• Name of the content
• MEGA download link

Example:
My Amazing File
https://mega.nz/file/xxxxx

I'll process it and post to all configured channels automatically.
    """
    bot.reply_to(message, welcome_text)

# ==================================================
# MAIN
# ==================================================

if __name__ == "__main__":
    logger.info("🚀 Starting bot...")
    
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("✅ Flask server started")
    
    # Start bot polling
    logger.info("✅ Starting Telegram bot polling...")
    
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"❌ Bot polling error: {e}")
            logger.info("🔄 Restarting bot in 5 seconds...")
            time.sleep(5)
