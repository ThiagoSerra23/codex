import discord
from discord.ext import commands
import aiosqlite

class FarmSubmissionView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Finalizar e Enviar", style=discord.ButtonStyle.green, custom_id="submit_farm_btn")
    async def submit_farm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Retrieve values from channel history or temporary storage?
        # Better: use a modal for the final checks or just read the last messages?
        # The prompt says: "Solicitar que o usuário informe: Quantidade de farm entregue, Quantidade de pólvora, Quantidade de cápsula"
        # Since it's a private channel, maybe a modal is best invoked by this button, or just a command.
        # Let's use a Modal for clean data entry.
        await interaction.response.send_modal(FarmDataModal())

class FarmDataModal(discord.ui.Modal, title="Relatório de Farm"):
    farm_amount = discord.ui.TextInput(label="Farm Entregue", placeholder="Quantidade (ex: 100000)")
    powder_amount = discord.ui.TextInput(label="Pólvora", placeholder="Quantidade (ex: 50)")
    capsule_amount = discord.ui.TextInput(label="Cápsula", placeholder="Quantidade (ex: 20)")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Validate inputs
        try:
            farm = int(self.farm_amount.value)
            powder = int(self.powder_amount.value)
            capsule = int(self.capsule_amount.value)
        except ValueError:
            await interaction.followup.send("Por favor, insira apenas números válidos.", ephemeral=True)
            return

        embed = discord.Embed(title="Relatório de Farm Enviado", color=discord.Color.gold())
        embed.add_field(name="Entregador", value=interaction.user.mention, inline=False)
        embed.add_field(name="Farm Entregue", value=f"{farm:,}", inline=True)
        embed.add_field(name="Pólvora", value=f"{powder:,}", inline=True)
        embed.add_field(name="Cápsulas", value=f"{capsule:,}", inline=True)
        embed.set_timestamp()

        await interaction.channel.send(embed=embed)
        await interaction.followup.send("Relatório gerado com sucesso!", ephemeral=True)
        
        # Log to DB with guild_id and channel_id
        async with aiosqlite.connect("database.db") as db:
            await db.execute(
                "INSERT INTO farms (user_id, guild_id, channel_id, farm_amount, powder_amount, capsule_amount) VALUES (?, ?, ?, ?, ?, ?)", 
                (interaction.user.id, interaction.guild.id, interaction.channel.id, farm, powder, capsule)
            )
            await db.commit()

        # Rename channel to indicate completion
        from datetime import datetime
        date_str = datetime.now().strftime("%d-%m")
        await interaction.channel.edit(name=f"farm-{interaction.user.name}-{date_str}-✅")


class FarmInitView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Registrar Farm", style=discord.ButtonStyle.secondary, emoji="🚜", custom_id="init_farm_btn")
    async def init_farm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        async with aiosqlite.connect("database.db") as db:
            async with db.execute("SELECT farm_category_id, farm_allowed_roles FROM guild_config WHERE guild_id = ?", (interaction.guild.id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    category_id, allowed_roles_str = row
                    
                    # Check allowed roles if defined
                    if allowed_roles_str:
                        allowed_role_ids = [int(r) for r in allowed_roles_str.split(',') if r]
                        user_role_ids = [r.id for r in interaction.user.roles]
                        if not any(rid in user_role_ids for rid in allowed_role_ids) and not interaction.user.guild_permissions.administrator:
                             await interaction.followup.send("Você não tem permissão para registrar farms.", ephemeral=True)
                             return

                    category = interaction.guild.get_channel(category_id) if category_id else None
                    
                    overwrites = {
                        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                    }

                    # Add allowed roles to overwrites so they can see too? Usually only the user and admins/approvers.
                    # Let's keep it private for now + admins.
                    
                    try:
                        channel = await interaction.guild.create_text_channel(
                            name=f"farm-{interaction.user.name}",
                            category=category,
                            overwrites=overwrites
                        )
                        
                        embed = discord.Embed(title="Registro de Farm", description="Clique no botão abaixo para preencher o relatório.", color=discord.Color.orange())
                        await channel.send(f"{interaction.user.mention}", embed=embed, view=FarmSubmissionView(self.bot))
                        
                        await interaction.followup.send(f"Canal criado: {channel.mention}", ephemeral=True)
                    except Exception as e:
                        await interaction.followup.send(f"Erro ao criar canal: {e}", ephemeral=True)

                else:
                    await interaction.followup.send("Configuração de farm não encontrada.", ephemeral=True)

class FarmConfigView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Definir Categoria", style=discord.ButtonStyle.primary)
    async def set_category(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Envie o ID da categoria onde os canais serão criados.", ephemeral=True)
        
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30.0)
            try:
                category_id = int(msg.content)
                category = interaction.guild.get_channel(category_id)
                if not isinstance(category, discord.CategoryChannel):
                     await interaction.followup.send("ID inválido ou não é uma categoria.", ephemeral=True)
                     return
            except ValueError:
                 await interaction.followup.send("ID inválido.", ephemeral=True)
                 return
            
            async with aiosqlite.connect("database.db") as db:
                cursor = await db.execute("SELECT 1 FROM guild_config WHERE guild_id = ?", (interaction.guild.id,))
                if await cursor.fetchone():
                    await db.execute("UPDATE guild_config SET farm_category_id = ? WHERE guild_id = ?", (category.id, interaction.guild.id))
                else:
                     await db.execute("INSERT INTO guild_config (guild_id, farm_category_id) VALUES (?, ?)", (interaction.guild.id, category.id))
                await db.commit()
            
            await interaction.followup.send(f"Categoria definida para {category.name}", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("Tempo esgotado.", ephemeral=True)
    
    # Implement Role configuration button similar to above

class Farm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(FarmInitView(self.bot))
        self.bot.add_view(FarmSubmissionView(self.bot))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def config_farm(self, ctx):
        embed = discord.Embed(title="Configuração de Farm", description="Configure a categoria de farm.")
        await ctx.send(embed=embed, view=FarmConfigView(self.bot))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setup_farm(self, ctx):
        embed = discord.Embed(title="Central de Farm", description="Clique abaixo para iniciar um registro de farm.", color=discord.Color.gold())
        await ctx.send(embed=embed, view=FarmInitView(self.bot))

async def setup(bot):
    await bot.add_cog(Farm(bot))
