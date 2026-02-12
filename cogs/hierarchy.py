import discord
from discord.ext import commands, tasks
import aiosqlite

class Hierarchy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hierarchy_message_id = None
        self.hierarchy_channel_id = None
        self.update_hierarchy.start()

    def cog_unload(self):
        self.update_hierarchy.cancel()

    @tasks.loop(minutes=5)
    async def update_hierarchy(self):
        # Iterate over all configured messages
        async with aiosqlite.connect("database.db") as db:
             # Ensure table exists first
             await db.execute("CREATE TABLE IF NOT EXISTS hierarchy_messages (guild_id INTEGER PRIMARY KEY, channel_id INTEGER, message_id INTEGER)")
             
             async with db.execute("SELECT guild_id, channel_id, message_id FROM hierarchy_messages") as cursor:
                 rows = await cursor.fetchall()
                 for row in rows:
                     guild_id, channel_id, message_id = row
                     guild = self.bot.get_guild(guild_id)
                     if guild:
                         channel = guild.get_channel(channel_id)
                         if channel:
                             await self.update_message(guild, channel, message_id)

    @commands.group(invoke_without_command=True)
    async def hierarquia(self, ctx):
        await ctx.send("Comandos: !hierarquia add <role> <pos>, !hierarquia remove <role>, !hierarquia setup")

    @hierarquia.command()
    async def add(self, ctx, role: discord.Role, position: int):
        async with aiosqlite.connect("database.db") as db:
            await db.execute("INSERT OR REPLACE INTO hierarchy (role_id, guild_id, position) VALUES (?, ?, ?)", (role.id, ctx.guild.id, position))
            await db.commit()
        await ctx.send(f"Cargo {role.name} adicionado à hierarquia na posição {position}.")

    @hierarquia.command()
    async def remove(self, ctx, role: discord.Role):
        async with aiosqlite.connect("database.db") as db:
            await db.execute("DELETE FROM hierarchy WHERE role_id = ? AND guild_id = ?", (role.id, ctx.guild.id))
            await db.commit()
        await ctx.send(f"Cargo {role.name} removido da hierarquia.")

    @hierarquia.command()
    async def setup(self, ctx):
        embed = discord.Embed(title="Hierarquia da Facção", description="Carregando...", color=discord.Color.dark_red())
        msg = await ctx.send(embed=embed)
        
        # Save msg.id and ctx.channel.id to DB
        async with aiosqlite.connect("database.db") as db:
             await db.execute("INSERT OR REPLACE INTO hierarchy_messages (guild_id, channel_id, message_id) VALUES (?, ?, ?)", (ctx.guild.id, ctx.channel.id, msg.id))
             await db.commit()
        
        # Trigger update
        await self.update_message(ctx.guild, ctx.channel, msg.id)

    async def update_message(self, guild, channel, message_id):
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.execute("SELECT role_id FROM hierarchy WHERE guild_id = ? ORDER BY position ASC", (guild.id,))
            rows = await cursor.fetchall()
            
        embed = discord.Embed(title="Hierarquia", color=discord.Color.dark_red())
        
        for row in rows:
            role_id = row[0]
            role = guild.get_role(role_id)
            if role:
                members = [m.mention for m in role.members]
                if members:
                    embed.add_field(name=f"{role.name} ({len(members)})", value="\n".join(members), inline=False)
                # else:
                #     embed.add_field(name=role.name, value="Vazio", inline=False)
        
        try:
            msg = await channel.fetch_message(message_id)
            await msg.edit(embed=embed)
        except:
            print(f"Failed to update hierarchy message {message_id}")

    @update_hierarchy.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Hierarchy(bot))
