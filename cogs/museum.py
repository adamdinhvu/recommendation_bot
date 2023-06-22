import discord
from discord.ext import commands
from curator import Cog
import sqlite3
from os import getenv
import re
from random import randrange
from time import sleep
import aiosqlite

class Museum(Cog):
    flavour_texts = [
        "The curator dusts off a crate, as he slides off the wooden lid you get a glimpse of this",
        "Under a stack of bookshelves, a cylindrical tube slides out. The curator twists off the lid and out pops this",
        "After a brief pause, the curator rummages into his back pocket and pulls out this",
        "In a small delicate jewel box you hear the twinkle of a lullaby. As the curator leads open the lid you see this",
        "The curator reaches as high as he can to get a dusty old book. As he steps off the ladder a piece of paper slides out, you see this",
        "The curator's cat wanders atop a stack of shelves. As she lays down you see a sheet of paper poking out at her front paws. You reach up to grab it and find this",
        "The curator pokes his head out of a box that's larger than him. He tosses down a small cardbox box. As you open it, you see this",
        "With a soft sigh, the curator leads you to a dark corner of the warehouse. Lying on a table unceremoniously, you spy this",
        "With a suprised blink, the curator takes a thin cylinder out from behind his ear. Unfurling the scroll inside of it, you see this",
        "Apologising for the mess, the curator reaches into a stack of boxes. With a pleased grin he hands you this",
        "The curator thumbs through a catalogue. He ventures out into a neat stack of shelves and returns with this",
    ]
    
    @Cog.listener()
    async def on_message(self, message : discord.Message) -> None:
        
        channel_id = int(getenv("MUSEUM_CHANNEL"))
        if message.channel.id == channel_id:
    
            sql = await aiosqlite.connect("curator.db")
            cur = await sql.cursor()

            content_urls = re.findall(r'(https?://[^\s]+)', message.content)
            attatchments = [a.url for a in message.attachments]

            valid_extensions = (".mov",".mp4",".jpg",".jpeg",".png",".gif",".gifv",".webm",".mp3",".ogg")
            for i in content_urls + attatchments:
                if i.endswith(valid_extensions):
                    url_parts = i.replace("https://cdn.discordapp.com/attachments/","").split("/")
                    print(f"Adding {str(i)} to the database")
                    # The SQL columns: image_id INTEGER PRIMARY KEY, channel_id INTEGER, image_name TEXT
                    values = (int(url_parts[1]),int(url_parts[0]),url_parts[2]) 
                    await cur.execute(f"""INSERT OR IGNORE INTO museum VALUES(?,?,?)""",values)
            
            await sql.commit()
            

    
    @discord.slash_command()
    @discord.option("artifact",description="Get a random museum artifact")
    async def artifact(self, ctx : discord.ApplicationContext):
        channel_id = int(getenv("QUERY_CHANNEL"))
        if ctx.channel_id != channel_id:
            await ctx.respond(f"Command only available in channel: {self.bot.get_channel(channel_id).name}")
            return
        
        msg = await ctx.respond(embed= 
            discord.Embed(title="", description="The curator searches for something.", color=0x00ff00))
        
        print(f"Launching artifact request")

        sleep(.7)
        
        sql = await aiosqlite.connect("curator.db")
        cur = await sql.cursor()    
        await cur.execute(f"""SELECT * FROM museum ORDER BY RANDOM() LIMIT 1""")
        try:
            record = (await cur.fetchall())[0]
        except:
            await ctx.send("Nothing found in the database, ensure you run /update_museum_backlog first")
            await sql.close()
            return

        if len(record) > 0:
            url = f"https://cdn.discordapp.com/attachments/{record[1]}/{record[0]}/{record[2]}"
            new_text = f"👴 {self.flavour_texts[randrange(0,len(self.flavour_texts)-1)]}"

            embded_response = discord.Embed(title="", description=new_text, color=0x00ff00)

            non_image_extensions = (".mov",".mp4",".gif",".gifv",".webm",".mp3",".ogg")
            if(not url.endswith(non_image_extensions)):
                embded_response.set_image(url=url)
            else:
                await ctx.send(url)

            msg = await msg.edit_original_response(embed=embded_response)

            await sql.close()
            return

        

    @discord.slash_command()
    @discord.default_permissions(manage_guild=True)
    @discord.option("update_museum_backlog",description="Update the museum database")
    async def update_museum_backlog(self, ctx : discord.ApplicationContext):
        channel_id = int(getenv("QUERY_CHANNEL"))
        if ctx.channel_id != channel_id:
            await ctx.respond(f"Command only available in channel: {self.bot.get_channel(channel_id).name}")
            return
        
        await ctx.respond("Attempting database update")

        sql = await aiosqlite.connect("curator.db")
        cur = await sql.cursor()
        async for message in ctx.guild.get_channel_or_thread(int(getenv("MUSEUM_CHANNEL"))).history(limit=None):    
            #get message attachements, and check them for any supported formats
            #look at the actual message and double check there's no embeded file in the message 
            content_urls = re.findall(r'(https?://[^\s]+)', message.content)
            attatchments = [a.url for a in message.attachments]

            valid_extensions = (".mov",".mp4",".jpg",".jpeg",".png",".gif",".gifv",".webm",".mp3",".ogg")
            for i in content_urls + attatchments:
                if i.endswith(valid_extensions):
                    url_parts = i.replace("https://cdn.discordapp.com/attachments/","").replace("https://media.discordapp.net/attachments/","").split("/")
                    print(f"Adding {str(i)} to the database")
                    # The SQL columns: image_id INTEGER PRIMARY KEY, channel_id INTEGER, image_name TEXT
                    values = (int(url_parts[1]),int(url_parts[0]),url_parts[2]) 
                    await cur.execute(f"""INSERT OR IGNORE INTO museum VALUES(?,?,?)""",values)

        await ctx.send("Update Successful :)")

        await sql.commit()
        await sql.close()

def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Museum(bot)) # add the cog to the bot