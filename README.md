# Telegram Bot - Deployment Guide

A Telegram bot that processes images with MEGA links, creates Rentry pastes, locks them with Linkvertise, and posts to Discord and Telegram channels.

## Features

- ✅ Processes images with captions containing names and MEGA links
- ✅ Creates double Rentry pastes for additional security
- ✅ Locks links with Linkvertise
- ✅ Posts to multiple Discord webhooks
- ✅ Posts to Telegram channel
- ✅ Robust error handling with retry logic
- ✅ Flask keep-alive server for Render
- ✅ Comprehensive logging

## Requirements

- Python 3.11+
- Telegram Bot Token
- Telegram Channel ID
- Rentry CSRF Token
- Linkvertise Tag ID
- Discord Webhook URLs

## Local Testing

1. **Clone/Download the repository**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file** (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

4. **Fill in your credentials in `.env`:**
   ```env
   BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHANNEL_ID=-1001234567890
   RENTRY_CSRF_TOKEN=your_csrf_token
   LINKVERTISE_TAG_ID=your_tag_id
   DISCORD_WEBHOOK_1=https://discord.com/api/webhooks/...
   DISCORD_WEBHOOK_2=https://discord.com/api/webhooks/...
   ```

5. **Run the bot:**
   ```bash
   python bot.py
   ```

## Deploy to Render

### Method 1: Using Render Dashboard (Recommended)

1. **Create a new Web Service** on [Render](https://render.com)

2. **Connect your GitHub repository** or upload files manually

3. **Configure the service:**
   - **Name:** telegram-bot (or your choice)
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Plan:** Free

4. **Add Environment Variables** in the Render dashboard:
   - `BOT_TOKEN` - Your Telegram bot token
   - `TELEGRAM_CHANNEL_ID` - Your channel ID (e.g., -1001234567890)
   - `RENTRY_CSRF_TOKEN` - Your Rentry CSRF token
   - `LINKVERTISE_TAG_ID` - Your Linkvertise tag ID
   - `DISCORD_WEBHOOK_1` - First Discord webhook URL
   - `DISCORD_WEBHOOK_2` - Second Discord webhook URL

5. **Deploy!** Render will automatically build and start your bot.

### Method 2: Using render.yaml

If you have a `render.yaml` file in your repository, Render will automatically detect it and configure your service.

## How to Use the Bot

1. **Start the bot:**
   - Send `/start` or `/help` to get instructions

2. **Send a photo with caption:**
   ```
   My Awesome File Name
   https://mega.nz/file/xxxxx
   ```

3. **The bot will:**
   - Process the image and link
   - Create Rentry pastes
   - Apply Linkvertise locks
   - Post to all configured Discord and Telegram channels
   - Reply with a success message

## Getting Your Credentials

### Telegram Bot Token
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow instructions
3. Copy the token provided

### Telegram Channel ID
1. Add your bot to the channel as an admin
2. Forward a message from the channel to [@userinfobot](https://t.me/userinfobot)
3. Copy the channel ID (starts with -100)

### Rentry CSRF Token
1. Open [rentry.co](https://rentry.co) in your browser
2. Open Developer Tools (F12)
3. Go to Console tab
4. Type: `document.cookie`
5. Find and copy the `csrftoken` value

### Linkvertise Tag ID
1. Log in to your Linkvertise account
2. Go to your dashboard
3. Find your Tag/User ID in the URL or settings

### Discord Webhook
1. Go to your Discord server
2. Edit channel → Integrations → Webhooks
3. Create a new webhook
4. Copy the webhook URL

## Monitoring

- Visit `https://your-render-url.onrender.com/` to check if bot is alive
- Visit `https://your-render-url.onrender.com/health` for health status
- Check Render logs for detailed bot activity

## Keeping Bot Alive (24/7)

Use a service like [UptimeRobot](https://uptimerobot.com):
1. Create a new monitor
2. Monitor Type: HTTP(s)
3. URL: `https://your-render-url.onrender.com/`
4. Monitoring Interval: Every 5 minutes

## Troubleshooting

### Bot doesn't respond
- Check if all environment variables are set correctly
- Check Render logs for errors
- Verify bot token is valid

### Rentry paste creation fails
- Check if CSRF token is valid (tokens expire)
- Try getting a new CSRF token from rentry.co

### Posts not appearing
- Verify channel ID is correct (should start with -100)
- Ensure bot is admin in the Telegram channel
- Check Discord webhook URLs are valid

### Rate Limiting
- The bot includes retry logic for most operations
- If you experience rate limits, reduce posting frequency

## Support

If you encounter issues:
1. Check the logs in Render dashboard
2. Verify all credentials are correct
3. Ensure your bot has proper permissions

## License

This project is for personal use. Modify as needed for your requirements.
