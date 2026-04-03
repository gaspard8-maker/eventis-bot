import discord
from discord.ext import commands
import os
import json
import asyncio

# ── Configuration ──────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID   = 0  # Remplace par ton Discord user ID

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ── Chargement des cogs ────────────────────────────────────────
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"  ✅ Cog chargé : {filename}")

@bot.event
async def on_ready():
    print(f"\n🤖 Eventis Bot est en ligne !")
    print(f"   Connecté en tant que : {bot.user}")
    print(f"   ID : {bot.user.id}")
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="Eventis 🎟️")
    )
    try:
        synced = await bot.tree.sync()
        print(f"   {len(synced)} commandes slash synchronisées.\n")
    except Exception as e:
        print(f"   ❌ Erreur sync : {e}")

async def main():
    async with bot:
        print("🔄 Chargement des cogs...")
        await load_cogs()
        await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
