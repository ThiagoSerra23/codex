import discord
from discord.ext import commands
import aiosqlite

class ApprovalView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.green, custom_id="approve_btn")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        async with aiosqlite.connect("database.db") as db:
            async with db.execute("SELECT approve_role_id, register_role_id FROM guild_config WHERE guild_id = ?", (interaction.guild.id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    approve_role_id, register_role_id = row
                    
                    # Check permissions
                    allowed = False
                    if interaction.user.guild_permissions.administrator:
                        allowed = True
                    elif approve_role_id:
                        role = interaction.guild.get_role(approve_role_id)
                        if role and role in interaction.user.roles:
                            allowed = True
                    
                    if not allowed:
                        await interaction.followup.send("Você não tem permissão para aprovar registros.", ephemeral=True)
                        return

                    try:
                        # Extract user ID from embed footer or field
                        if interaction.message.embeds:
                            embed = interaction.message.embeds[0]
                            # Assuming user ID is in the footer text like "User ID: 123456" or we can parse the mention
                            # Let's rely on the mention in the first field for now
                            user_mention = embed.fields[0].value
                            user_id = int(user_mention.strip("<@!>"))
                            member = interaction.guild.get_member(user_id)
                            
                            if register_role_id:
                                reg_role = interaction.guild.get_role(register_role_id)
                                if member and reg_role:
                                    await member.add_roles(reg_role)
                                    try:
                                        await member.send("Seu registro foi aprovado! Bem-vindo!")
                                    except:
                                        pass # DM might fail
                                    await interaction.message.edit(content=f"✅ Aprovado por {interaction.user.mention}", view=None)
                                    await interaction.followup.send("Usuário aprovado com sucesso.", ephemeral=True)
                                else:
                                    await interaction.followup.send("Erro: Membro saiu do servidor ou cargo não encontrado.", ephemeral=True)
                            else:
                                 await interaction.followup.send("Erro: Cargo de registrado não configurado.", ephemeral=True)
                        else:
                            await interaction.followup.send("Erro: Embed original não encontrada.", ephemeral=True)

                    except Exception as e:
                        await interaction.followup.send(f"Erro ao aprovar: {e}", ephemeral=True)

                else:
                    await interaction.followup.send("Configuração incompleta no banco de dados.", ephemeral=True)

    @discord.ui.button(label="Recusar", style=discord.ButtonStyle.red, custom_id="deny_btn")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        async with aiosqlite.connect("database.db") as db:
             async with db.execute("SELECT approve_role_id FROM guild_config WHERE guild_id = ?", (interaction.guild.id,)) as cursor:
                row = await cursor.fetchone()
                approve_role_id = row[0] if row else None

                allowed = False
                if interaction.user.guild_permissions.administrator:
                    allowed = True
                elif approve_role_id:
                     role = interaction.guild.get_role(approve_role_id)
                     if role and role in interaction.user.roles:
                         allowed = True
                
                if not allowed:
                    await interaction.followup.send("Você não tem permissão para recusar registros.", ephemeral=True)
                    return

                try:
                    if interaction.message.embeds:
                        embed = interaction.message.embeds[0]
                        user_mention = embed.fields[0].value
                        user_id = int(user_mention.strip("<@!>"))
                        member = interaction.guild.get_member(user_id)
                        
                        if member:
                            try:
                                await member.send("Seu registro foi recusado. Entre em contato com a administração.")
                            except:
                                pass
                        
                        await interaction.message.edit(content=f"❌ Recusado por {interaction.user.mention}", view=None)
                        await interaction.followup.send("Registro recusado.", ephemeral=True)
                except Exception as e:
                    await interaction.followup.send(f"Erro ao recusar: {e}", ephemeral=True)

class RegistrationModal(discord.ui.Modal, title="Formulário de Registro"):
    name = discord.ui.TextInput(label="Nome", placeholder="Seu nome real")
    age = discord.ui.TextInput(label="Idade", placeholder="Sua idade")
    about = discord.ui.TextInput(label="Sobre Você", style=discord.TextStyle.paragraph, placeholder="Conte um pouco sobre você...")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with aiosqlite.connect("database.db") as db:
            async with db.execute("SELECT log_channel_id FROM guild_config WHERE guild_id = ?", (interaction.guild.id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    channel_id = row[0]
                    channel = interaction.guild.get_channel(channel_id)
                    if channel:
                        embed = discord.Embed(title="Novo Registro", color=discord.Color.blue())
                        embed.add_field(name="Usuário", value=interaction.user.mention, inline=False)
                        embed.add_field(name="Nome", value=self.name.value, inline=False)
                        embed.add_field(name="Idade", value=self.age.value, inline=False)
                        embed.add_field(name="Sobre", value=self.about.value, inline=False)
                        embed.set_footer(text=f"User ID: {interaction.user.id}")
                        
                        view = ApprovalView()
                        await channel.send(embed=embed, view=view)
                        await interaction.followup.send("Registro enviado com sucesso! Aguarde a aprovação.", ephemeral=True)
                    else:
                        await interaction.followup.send("Erro: Canal de logs não encontrado.", ephemeral=True)
                else:
                    await interaction.followup.send("Erro: Canal de logs não configurado.", ephemeral=True)

class RegisterButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Registrar-se", style=discord.ButtonStyle.success, custom_id="register_btn")
    async def register_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RegistrationModal())

class RegistrationConfigView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Definir Canal de Logs", style=discord.ButtonStyle.primary)
    async def set_log_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Mencione o canal de logs para o registro.", ephemeral=True)
        
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel and m.channel_mentions

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30.0)
            channel = msg.channel_mentions[0]
            
            async with aiosqlite.connect("database.db") as db:
                # Check if entry exists, if not insert, else update
                # Simplified UPSERT logic or standard implementation
                cursor = await db.execute("SELECT 1 FROM guild_config WHERE guild_id = ?", (interaction.guild.id,))
                if await cursor.fetchone():
                    await db.execute("UPDATE guild_config SET log_channel_id = ? WHERE guild_id = ?", (channel.id, interaction.guild.id))
                else:
                    await db.execute("INSERT INTO guild_config (guild_id, log_channel_id) VALUES (?, ?)", (interaction.guild.id, channel.id))
                await db.commit()
            
            await interaction.followup.send(f"Canal de logs definido para {channel.mention}", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("Tempo esgotado.", ephemeral=True)

    @discord.ui.button(label="Definir Cargo de Aprovação", style=discord.ButtonStyle.primary)
    async def set_approve_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Mencione o cargo que poderá aprovar registros.", ephemeral=True)
        
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel and m.role_mentions

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30.0)
            role = msg.role_mentions[0]
            
            async with aiosqlite.connect("database.db") as db:
                cursor = await db.execute("SELECT 1 FROM guild_config WHERE guild_id = ?", (interaction.guild.id,))
                if await cursor.fetchone():
                    await db.execute("UPDATE guild_config SET approve_role_id = ? WHERE guild_id = ?", (role.id, interaction.guild.id))
                else:
                    await db.execute("INSERT INTO guild_config (guild_id, approve_role_id) VALUES (?, ?)", (interaction.guild.id, role.id))
                await db.commit()
            
            await interaction.followup.send(f"Cargo de aprovação definido para {role.mention}", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("Tempo esgotado.", ephemeral=True)

    @discord.ui.button(label="Definir Cargo Registrado", style=discord.ButtonStyle.primary)
    async def set_registered_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Mencione o cargo que o usuário receberá ao ser aprovado.", ephemeral=True)
        
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel and m.role_mentions

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30.0)
            role = msg.role_mentions[0]
            
            async with aiosqlite.connect("database.db") as db:
                cursor = await db.execute("SELECT 1 FROM guild_config WHERE guild_id = ?", (interaction.guild.id,))
                if await cursor.fetchone():
                    await db.execute("UPDATE guild_config SET register_role_id = ? WHERE guild_id = ?", (role.id, interaction.guild.id))
                else:
                    await db.execute("INSERT INTO guild_config (guild_id, register_role_id) VALUES (?, ?)", (interaction.guild.id, role.id))
                await db.commit()
            
            await interaction.followup.send(f"Cargo de registrado definido para {role.mention}", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("Tempo esgotado.", ephemeral=True)


class Registration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # Register persistent views
        self.bot.add_view(ApprovalView())
        self.bot.add_view(RegisterButtonView())

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def config_registro(self, ctx):
        embed = discord.Embed(title="Configuração de Registro", description="Utilize os botões abaixo para configurar o sistema de registro.")
        await ctx.send(embed=embed, view=RegistrationConfigView(self.bot))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setup_registro(self, ctx):
        """Envia a mensagem com o botão de registro para o canal atual."""
        embed = discord.Embed(title="Registro", description="Clique no botão abaixo para iniciar o registro.", color=discord.Color.green())
        await ctx.send(embed=embed, view=RegisterButtonView())


async def setup(bot):
    await bot.add_cog(Registration(bot))
