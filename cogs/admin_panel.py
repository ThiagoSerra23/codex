import discord
from discord.ext import commands
import aiosqlite
from .actions import PersistentActionView
from .registration import RegisterButtonView
from .farm import FarmInitView

class AdminPanelView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Criar Ação", style=discord.ButtonStyle.danger, emoji="⚔️", custom_id="admin_create_action")
    async def create_action(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.send_modal(CreateActionModal(self.bot))
        except Exception as e:
            print(f"[ERROR] create_action button: {e}", flush=True)
            await interaction.response.send_message(f"Erro ao abrir modal: {e}", ephemeral=True)

    @discord.ui.button(label="Gerenciar Hierarquia", style=discord.ButtonStyle.primary, emoji="👑", custom_id="admin_manage_hierarchy")
    async def manage_hierarchy(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.send_modal(HierarchyRoleModal(self.bot))
        except Exception as e:
            print(f"[ERROR] manage_hierarchy button: {e}", flush=True)
            await interaction.response.send_message(f"Erro ao abrir modal: {e}", ephemeral=True)

    @discord.ui.button(label="Configurações", style=discord.ButtonStyle.secondary, emoji="⚙️", custom_id="admin_settings", row=1)
    async def settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.send_message("## Menu de Configuração\nSelecione o sistema que deseja configurar:", view=SettingsView(self.bot), ephemeral=True)
        except Exception as e:
            print(f"[ERROR] settings button: {e}", flush=True)
            await interaction.response.send_message(f"Erro ao abrir configurações: {e}", ephemeral=True)

    @discord.ui.button(label="Painel de Farm (Público)", style=discord.ButtonStyle.success, emoji="🚜", custom_id="admin_public_farm", row=2)
    async def public_farm(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            embed = discord.Embed(title="Central de Farm", description="Clique abaixo para iniciar um registro de farm.", color=discord.Color.gold())
            await interaction.channel.send(embed=embed, view=FarmInitView(self.bot))
            await interaction.response.send_message("Painel de Farm enviado neste canal!", ephemeral=True)
        except Exception as e:
            print(f"[ERROR] public_farm button: {e}", flush=True)
            await interaction.response.send_message(f"Erro ao enviar painel de farm: {e}", ephemeral=True)

    @discord.ui.button(label="Painel de Registro (Público)", style=discord.ButtonStyle.success, emoji="📝", custom_id="admin_public_reg", row=2)
    async def public_reg(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            embed = discord.Embed(title="Registro", description="Clique no botão abaixo para iniciar o registro.", color=discord.Color.green())
            await interaction.channel.send(embed=embed, view=RegisterButtonView())
            await interaction.response.send_message("Painel de registro enviado neste canal!", ephemeral=True)
        except Exception as e:
            print(f"[ERROR] public_reg button: {e}", flush=True)
            await interaction.response.send_message(f"Erro ao enviar painel de registro: {e}", ephemeral=True)

class SettingsView(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @discord.ui.button(label="Configurar Registro", style=discord.ButtonStyle.primary, emoji="📝")
    async def config_reg(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Selecione os cargos e canais para o Registro:", view=RegistrationConfigView(self.bot), ephemeral=True)

    @discord.ui.button(label="Configurar Farm", style=discord.ButtonStyle.success, emoji="🚜")
    async def config_farm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Selecione a categoria para os Farms:", view=FarmConfigSelectView(self.bot), ephemeral=True)

class RegistrationConfigView(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @discord.ui.select(cls=discord.ui.RoleSelect, placeholder="Selecione o Cargo de Aprovação", min_values=1, max_values=1, custom_id="reg_approve_role")
    async def select_approve_role(self, interaction: discord.Interaction, select: discord.ui.Select):
        role_id = select.values[0].id
        async with aiosqlite.connect("database.db") as db:
            await db.execute("INSERT INTO guild_config (guild_id, approve_role_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET approve_role_id=excluded.approve_role_id", (interaction.guild.id, role_id))
            await db.commit()
        await interaction.response.send_message(f"Cargo de Aprovação definido para: {select.values[0].mention}", ephemeral=True)

    @discord.ui.select(cls=discord.ui.RoleSelect, placeholder="Selecione o Cargo Registrado (Entregue)", min_values=1, max_values=1, custom_id="reg_given_role")
    async def select_given_role(self, interaction: discord.Interaction, select: discord.ui.Select):
        role_id = select.values[0].id
        async with aiosqlite.connect("database.db") as db:
            await db.execute("INSERT INTO guild_config (guild_id, register_role_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET register_role_id=excluded.register_role_id", (interaction.guild.id, role_id))
            await db.commit()
        await interaction.response.send_message(f"Cargo Entregue definido para: {select.values[0].mention}", ephemeral=True)

    @discord.ui.select(cls=discord.ui.ChannelSelect, placeholder="Selecione o Canal de Logs", channel_types=[discord.ChannelType.text], min_values=1, max_values=1, custom_id="reg_log_channel")
    async def select_log_channel(self, interaction: discord.Interaction, select: discord.ui.Select):
        channel_id = select.values[0].id
        async with aiosqlite.connect("database.db") as db:
            await db.execute("INSERT INTO guild_config (guild_id, log_channel_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET log_channel_id=excluded.log_channel_id", (interaction.guild.id, channel_id))
            await db.commit()
        await interaction.response.send_message(f"Canal de Logs definido para: {select.values[0].mention}", ephemeral=True)

class FarmConfigSelectView(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @discord.ui.select(cls=discord.ui.ChannelSelect, placeholder="Selecione a Categoria de Farm", channel_types=[discord.ChannelType.category], min_values=1, max_values=1, custom_id="farm_category_select")
    async def select_category(self, interaction: discord.Interaction, select: discord.ui.Select):
        cat_id = select.values[0].id
        async with aiosqlite.connect("database.db") as db:
            await db.execute("INSERT INTO guild_config (guild_id, farm_category_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET farm_category_id=excluded.farm_category_id", (interaction.guild.id, cat_id))
            await db.commit()
        await interaction.response.send_message(f"Categoria de Farm definida para: {select.values[0].name}", ephemeral=True)

class CreateActionModal(discord.ui.Modal, title="Criar Nova Ação"):
    name = discord.ui.TextInput(label="Nome da Ação", placeholder="Invasão, Treino, etc.")
    date = discord.ui.TextInput(label="Data", placeholder="DD/MM")
    time = discord.ui.TextInput(label="Horário", placeholder="HB (ex: 20:00)")
    limit = discord.ui.TextInput(label="Limite de Vagas", placeholder="Número (ex: 15)")

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        try:
            max_participants = int(self.limit.value)
        except ValueError:
            await interaction.response.send_message("Limite deve ser um número.", ephemeral=True)
            return

        async with aiosqlite.connect("database.db") as db:
            cursor = await db.execute("INSERT INTO actions (name, date, time, max_participants, created_by, channel_id) VALUES (?, ?, ?, ?, ?, ?)", 
                                      (self.name.value, self.date.value, self.time.value, max_participants, interaction.user.id, interaction.channel.id))
            action_id = cursor.lastrowid
            await db.commit()

        embed = discord.Embed(title=f"Ação: {self.name.value}", color=discord.Color.red())
        embed.add_field(name="Data", value=self.date.value, inline=True)
        embed.add_field(name="Horário", value=self.time.value, inline=True)
        embed.add_field(name="Vagas", value=f"0/{max_participants}", inline=True)
        embed.add_field(name="Participantes", value="Nenhum", inline=False)

        view = PersistentActionView()
        msg = await interaction.channel.send(embed=embed, view=view)
        
        async with aiosqlite.connect("database.db") as db:
            await db.execute("UPDATE actions SET message_id = ? WHERE id = ?", (msg.id, action_id))
            await db.commit()
        
        await interaction.response.send_message("Ação criada com sucesso!", ephemeral=True)

class HierarchyRoleModal(discord.ui.Modal, title="Adicionar/Remover Cargo"):
    operation = discord.ui.TextInput(label="Operação (add/remove)", placeholder="add ou remove")
    role_id = discord.ui.TextInput(label="ID do Cargo", placeholder="Botão direito no cargo -> Copiar ID")
    position = discord.ui.TextInput(label="Posição (se add)", placeholder="Número (1 = mais alto)", required=False)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        op = self.operation.value.lower()
        try:
            r_id = int(self.role_id.value)
            role = interaction.guild.get_role(r_id)
            if not role:
                 await interaction.response.send_message("Cargo não encontrado.", ephemeral=True)
                 return
        except ValueError:
            await interaction.response.send_message("ID do cargo inválido.", ephemeral=True)
            return

        async with aiosqlite.connect("database.db") as db:
            if op == "add":
                try:
                    pos = int(self.position.value)
                except:
                    pos = 99
                await db.execute("INSERT OR REPLACE INTO hierarchy (role_id, guild_id, position) VALUES (?, ?, ?)", (r_id, interaction.guild.id, pos))
                await interaction.response.send_message(f"Cargo {role.name} adicionado à hierarquia na posição {pos}.", ephemeral=True)
            elif op == "remove":
                await db.execute("DELETE FROM hierarchy WHERE role_id = ? AND guild_id = ?", (r_id, interaction.guild.id))
                await interaction.response.send_message(f"Cargo {role.name} removido da hierarquia.", ephemeral=True)
            else:
                await interaction.response.send_message("Operação inválida. Use 'add' ou 'remove'.", ephemeral=True)
            await db.commit()

class AdminPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="painel", aliases=["admin"])
    async def admin_panel(self, ctx):
        # Check if user has administrator permission in the guild
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Você precisa de permissão de Administrador para usar este comando.", ephemeral=True)
            return
            
        print(f"[DEBUG] admin_panel command called by {ctx.author}", flush=True)
        try:
            embed = discord.Embed(title="Painel Administrativo", description="Gerencie o bot através dos botões abaixo.", color=discord.Color.dark_grey())
            embed.add_field(name="Ações Disponíveis", value="⚔️ Criar Ação: Abre formulário para nova ação.\n👑 Gerenciar Hierarquia: Adiciona/Remove cargos.\n⚙️ Configurações: Configura canais e cargos do bot.\n🚜/📝 Painéis Públicos: Envia os botões para os membros.")
            await ctx.send(embed=embed, view=AdminPanelView(self.bot))
            print(f"[DEBUG] Painel sent successfully", flush=True)
        except Exception as e:
            print(f"[ERROR] Failed to send panel: {e}", flush=True)
            import traceback
            traceback.print_exc()

    @commands.command(name="acao")
    async def acao_command(self, ctx):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Você precisa de permissão de Administrador para usar este comando.")
            return
        await ctx.send("Utilize o comando `!painel` e clique em 'Criar Ação'.")

async def setup(bot):
    await bot.add_cog(AdminPanel(bot))
