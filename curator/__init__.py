import discord
from discord.ext import commands
import sqlite3
from .bot import Recbot


__all__ = (
    "Recbot",
    "Cog"
)

class Cog(commands.Cog):
    """Base class for all cogs"""

    def __init__(self, bot: Recbot) -> None:
        self.bot = bot