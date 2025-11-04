import os
import requests
import asyncio
import discord
from datetime import datetime
from flask import Flask
import threading

# ===========================
# DUMMY FLASK SERVER
# ===========================
app = Flask(__name__)

@app.route("/")
def home():
    return "Discord bot is running!"

def run_flask():
    # Run Flask on port 10000 (Render detects this as an open port)
    app.run(host="0.0.0.0", port=10000)

# Start Flask in a separate thread so it doesn't block the Discord bot
threading.Thread(target=run_flask).start()


# ===========================
# DISCORD BOT SETUP
# ===========================
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

alerted_games = set()
current_day = datetime.utcnow().date()


async def check_scores():
    global alerted_games, current_day

    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"

    while True:
        try:
            today = datetime.utcnow().date()
            if today != current_day:
                alerted_games = set()
                current_day = today
                print("🔄 New day — alerts reset")

            response = requests.get(url, timeout=10)
            data = response.json()

            for event in data.get("events", []):
                game_id = event.get("id")
                competition = event.get("competitions", [])[0]
                competitors = competition.get("competitors", [])
                game_status = competition.get("status", {}).get("type", {}).get("state")

                # Skip if already announced or game hasn’t started
                if game_id in alerted_games or game_status != "in":
                    continue

                for team_data in competitors:
                    team = team_data["team"]["displayName"]
                    score = int(team_data.get("score", 0))

                    if score >= 69:
                        channel = client.get_channel(CHANNEL_ID)
                        await channel.send(f"🔥 {team} has reached 69 points in their game! 🏀")
                        alerted_games.add(game_id)
                        print(f"Announced {team} in game {game_id}")
                        break

        except Exception as e:
            print("⚠️ Error:", e)

        await asyncio.sleep(60)  # check every minute


@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    client.loop.create_task(check_scores())


client.run(TOKEN)


