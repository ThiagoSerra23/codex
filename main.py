import discord
import json
import os
import asyncio
from discord.ext import commands
from utils.database import init_db

# Load configuration
if os.path.exists("config.json"):
    with open("config.json", "r") as f:
        config = json.load(f)
else:
    config = {"token": "", "prefix": "!"}

class ManagerBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix=config["prefix"], intents=intents)
        self.extensions_loaded = False

    async def setup_hook(self):
        print("--- SETUP HOOK STARTED ---", flush=True)
        await init_db()
        print("Database initialized.", flush=True)

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})", flush=True)
        if not self.extensions_loaded:
            print("--- LOADING EXTENSIONS IN ON_READY ---", flush=True)
            print(f"CWD: {os.getcwd()}", flush=True)
            import traceback
            for filename in os.listdir("./cogs"):
                if filename.endswith(".py") and filename != "__init__.py":
                    try:
                        await self.load_extension(f"cogs.{filename[:-3]}")
                        print(f"Loaded extension: {filename}", flush=True)
                    except Exception as e:
                        print(f"Failed to load extension {filename}: {e}", flush=True)
                        traceback.print_exc()
            self.extensions_loaded = True
            print("--- EXTENSIONS LOADED ---", flush=True)

    async def on_message(self, message):
        if message.author.bot:
            return
        print(f"[DEBUG] Message from {message.author}: {message.content}", flush=True)
        await self.process_commands(message)

async def main():
    bot = ManagerBot()
    async with bot:
        if config["token"]:
            await bot.start(config["token"])
        else:
            print("Please set your bot token in config.json")

if __name__ == "__main__":
    asyncio.run(main())
