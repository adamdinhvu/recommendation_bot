import discord
from discord.ext import commands
from os import getenv
import sqlite3

class Recbot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents(
                    members=True,
                    messages=True,
                    message_content=True,
                    guilds=True,
                ))

        sql = sqlite3.connect("curator.db")
        cur = sql.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS videos
                (video_id TEXT PRIMARY KEY, user_id INTEGER)""")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS museum
                (image_id INTEGER PRIMARY KEY, channel_id INTEGER, image_name TEXT)""")
    
        for cog in ["cogs.rec", "cogs.museum"]: 
            self.load_extension(cog)

    async def on_ready(self):
        print(f"Recbot is ready and online!")

    def run(self):
        super().run(getenv("TOKEN"))