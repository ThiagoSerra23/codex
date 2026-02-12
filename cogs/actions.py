import discord
from discord.ext import commands
import aiosqlite
import asyncio

class RemoveParticipantModal(discord.ui.Modal, title="Remover Participante"):
    def __init__(self, action_id, view):
        super().__init__()
        self.action_id = action_id
        self.view_ref = view

    user_id_input = discord.ui.TextInput(label="ID do Usuário", placeholder="Cole o ID do usuário aqui")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            user_id = int(self.user_id_input.value)
            async with aiosqlite.connect("database.db") as db:
                await db.execute("DELETE FROM action_participants WHERE action_id = ? AND user_id = ?", (self.action_id, user_id))
                await db.commit()
            
            await interaction.followup.send(f"Usuário {user_id} removido da ação.", ephemeral=True)
            await self.view_ref.update_embed(interaction, self.action_id)
        except ValueError:
            await interaction.followup.send("ID inválido.", ephemeral=True)

class PersistentActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Entrar", style=discord.ButtonStyle.success, custom_id="join_action_generic")
    async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_action(interaction, "join")

    @discord.ui.button(label="Sair", style=discord.ButtonStyle.danger, custom_id="leave_action_generic")
    async def leave_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_action(interaction, "leave")

    @discord.ui.button(label="Remover", style=discord.ButtonStyle.secondary, custom_id="remove_participant_generic")
    async def remove_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_action(interaction, "remove")

    async def handle_action(self, interaction, action_type):
        if action_type != "remove":
            await interaction.response.defer()
        
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.execute("SELECT id, name, date, time, max_participants FROM actions WHERE message_id = ?", (interaction.message.id,))
            row = await cursor.fetchone()
            
            if not row:
                await interaction.followup.send("Ação não encontrada no banco de dados.", ephemeral=True)
                return
            
            action_id, name, date, time, max_p = row
            
            if action_type == "join":
                # Check participants
                cursor = await db.execute("SELECT count(*) FROM action_participants WHERE action_id = ?", (action_id,))
                count = (await cursor.fetchone())[0]
                
                if count >= max_p:
                     await interaction.followup.send("Ação cheia!", ephemeral=True)
                     return

                try:
                    await db.execute("INSERT INTO action_participants (action_id, user_id) VALUES (?, ?)", (action_id, interaction.user.id))
                    await db.commit()
                    await interaction.followup.send("Você entrou na ação!", ephemeral=True)
                    await self.update_embed(interaction, action_id)
                except aiosqlite.IntegrityError:
                    await interaction.followup.send("Você já está nesta ação.", ephemeral=True)

            elif action_type == "leave":
                await db.execute("DELETE FROM action_participants WHERE action_id = ? AND user_id = ?", (action_id, interaction.user.id))
                await db.commit()
                await interaction.followup.send("Você saiu da ação.", ephemeral=True)
                await self.update_embed(interaction, action_id)
            
            elif action_type == "remove":
                 if interaction.user.guild_permissions.administrator:
                    await interaction.response.send_modal(RemoveParticipantModal(action_id, self))
                 else:
                    await interaction.response.send_message("Você não tem permissão para remover participantes.", ephemeral=True)

    async def update_embed(self, interaction, action_id):
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.execute("SELECT name, date, time, max_participants FROM actions WHERE id = ?", (action_id,))
            action_data = await cursor.fetchone()
            if not action_data: return
            name, date, time, max_p = action_data

            cursor = await db.execute("SELECT user_id FROM action_participants WHERE action_id = ?", (action_id,))
            rows = await cursor.fetchall()
            participants = []
            for r in rows:
                m = interaction.guild.get_member(r[0])
                if m: participants.append(m.mention)
                else: participants.append(f"<@{r[0]}>")

        embed = discord.Embed(title=f"Ação: {name}", color=discord.Color.red())
        embed.add_field(name="Data", value=date, inline=True)
        embed.add_field(name="Horário", value=time, inline=True)
        embed.add_field(name="Vagas", value=f"{len(participants)}/{max_p}", inline=True)
        
        if participants:
            embed.add_field(name="Participantes", value="\n".join(participants), inline=False)
        else:
            embed.add_field(name="Participantes", value="Nenhum", inline=False)
            
        try:
             await interaction.message.edit(embed=embed, view=self)
        except:
             pass

class Actions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(PersistentActionView())

    @commands.command()
    async def action(self, ctx, name: str, date: str, time: str, max_participants: int):
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.execute("INSERT INTO actions (name, date, time, max_participants, created_by, channel_id) VALUES (?, ?, ?, ?, ?, ?)", 
                                      (name, date, time, max_participants, ctx.author.id, ctx.channel.id))
            action_id = cursor.lastrowid
            await db.commit()

        embed = discord.Embed(title=f"Ação: {name}", color=discord.Color.red())
        embed.add_field(name="Data", value=date, inline=True)
        embed.add_field(name="Horário", value=time, inline=True)
        embed.add_field(name="Vagas", value=f"0/{max_participants}", inline=True)
        embed.add_field(name="Participantes", value="Nenhum", inline=False)

        view = PersistentActionView()
        msg = await ctx.send(embed=embed, view=view)
        
        async with aiosqlite.connect("database.db") as db:
            await db.execute("UPDATE actions SET message_id = ? WHERE id = ?", (msg.id, action_id))
            await db.commit()

async def setup(bot):
    await bot.add_cog(Actions(bot))
