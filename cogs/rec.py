import discord
from discord.ext import commands
from curator import Cog
import sqlite3
import aiosqlite
from os import getenv
from urllib.parse import urlparse, parse_qs
from contextlib import suppress
import re

class Recommendation(Cog):
    @Cog.listener()
    async def on_message(self, message : discord.Message) -> None:
        
        channel_id = int(getenv("RECOMMENDATION_THREAD"))
        if message.channel.id == channel_id:
            url_search = re.search("(?P<url>https?://[^\s]+)",  message.content)
            if url_search is None:
                return

            youtube_id = extract_id(url_search.group("url"))
            if youtube_id is None:
                return
            
            print(f"Adding {youtube_id} to the database")

            #print(youtube_id)
            values = (youtube_id,message.author.id)
            sql = await aiosqlite.connect("curator.db")
            await sql.execute(f"""INSERT OR IGNORE INTO videos VALUES(?,?)""",values)
            await sql.commit()
            await sql.close()
            
    
    @discord.slash_command()
    @discord.option("imbored",description="Get a random video from the database")
    async def imbored(self, ctx : discord.ApplicationContext):
        channel_id = int(getenv("QUERY_CHANNEL"))
        if ctx.channel_id != channel_id:
            await ctx.respond(f"Command only available in channel: {self.bot.get_channel(channel_id).name}")
            return
        
        print("Searching for a video")

        sql = await aiosqlite.connect("curator.db")
        cur = await sql.execute(f"""SELECT * FROM videos ORDER BY RANDOM() LIMIT 1""")
        try:
            record = (await cur.fetchall())[0]
        except:
            await ctx.respond("Nothing found in the database, ensure you run /update_video_backlog first")
            await sql.close()
            return

        if len(record) > 0:
            await ctx.respond(f" Originally recommended by 🗣 **{(await self.bot.get_or_fetch_user(record[1])).display_name}** \n https://youtu.be/{record[0]}" )
            await sql.close()

    @discord.slash_command()
    @discord.default_permissions(manage_guild=True)
    @discord.option("update_videos",description="Update the video database")
    async def update_video_backlog(self, ctx : discord.ApplicationContext):
        channel_id = int(getenv("QUERY_CHANNEL"))
        if ctx.channel_id != channel_id:
            await ctx.respond(f"Command only available in channel: {self.bot.get_channel(channel_id).name}")
            return
        
        sql = await aiosqlite.connect("curator.db")
        async for message in ctx.guild.get_channel_or_thread(int(getenv("RECOMMENDATION_THREAD"))).history(limit=None):
            url_search = re.search("(?P<url>https?://[^\s]+)", message.content)
            if url_search is None:
                continue

            youtube_id = extract_id(url_search.group("url"))
            if youtube_id is None:
                continue
            
            print(f"Adding {youtube_id} to the database")
            values = (youtube_id,message.author.id)
            await sql.execute(f"""INSERT OR IGNORE INTO videos VALUES(?,?)""",values)
        
        await sql.commit()
        await ctx.respond("Updated video database")
        await sql.close()

YOUTUBE_DOMAINS = [
    'youtu.be',
    'youtube.com',
]

def extract_id(url_string):
    # Make sure all URLs start with a valid scheme
    if not url_string.lower().startswith('http'):
        url_string = 'http://%s' % url_string

    url = urlparse(url_string)

    # Check host against whitelist of domains
    if url.hostname.replace('www.', '') not in YOUTUBE_DOMAINS:
        return None

    # Video ID is usually to be found in 'v' query string
    qs = parse_qs(url.query)
    if 'v' in qs:
        return qs['v'][0]

    # Otherwise fall back to path component
    new_path = url.path.lstrip('/').replace("shorts/", "").replace("embed/", "")
    return new_path


def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Recommendation(bot)) # add the cog to the bot
