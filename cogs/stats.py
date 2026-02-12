import discord
from discord.ext import commands
import aiosqlite
from datetime import datetime, timedelta

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="stats", aliases=["estatisticas", "dashboard"])
    async def stats_command(self, ctx):
        """
        Mostra estatísticas gerais do servidor.
        """
        async with aiosqlite.connect("database.db") as db:
            # Buscar cor customizada
            cursor = await db.execute(
                "SELECT stats_color FROM bot_customization WHERE guild_id = ?",
                (ctx.guild.id,)
            )
            row = await cursor.fetchone()
            color_hex = row[0] if row else "#3498DB"
            color = int(color_hex.replace("#", ""), 16)
            
            # Total de registros
            cursor = await db.execute(
                "SELECT COUNT(*) FROM registrations WHERE status = 'approved'"
            )
            total_registros = (await cursor.fetchone())[0]
            
            cursor = await db.execute(
                "SELECT COUNT(*) FROM registrations WHERE status = 'denied'"
            )
            total_negados = (await cursor.fetchone())[0]
            
            # Total de farms
            cursor = await db.execute(
                "SELECT COUNT(*), SUM(farm_amount), SUM(powder_amount), SUM(capsule_amount) FROM farms WHERE guild_id = ?",
                (ctx.guild.id,)
            )
            farm_stats = await cursor.fetchone()
            total_farms, total_farm_amount, total_powder, total_capsules = farm_stats
            
            # Total de ações
            cursor = await db.execute(
                "SELECT COUNT(*) FROM actions WHERE guild_id = ?",
                (ctx.guild.id,)
            )
            total_acoes = (await cursor.fetchone())[0]
            
            # Top 5 membros mais ativos (por farms)
            cursor = await db.execute("""
                SELECT user_id, COUNT(*) as farm_count
                FROM farms
                WHERE guild_id = ?
                GROUP BY user_id
                ORDER BY farm_count DESC
                LIMIT 5
            """, (ctx.guild.id,))
            top_members = await cursor.fetchall()
            
            # Farms nos últimos 7 dias
            seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor = await db.execute(
                "SELECT COUNT(*) FROM farms WHERE guild_id = ? AND timestamp >= ?",
                (ctx.guild.id, seven_days_ago)
            )
            farms_last_week = (await cursor.fetchone())[0]
        
        # Criar embed
        embed = discord.Embed(
            title="📊 Dashboard de Estatísticas",
            description=f"Estatísticas gerais do servidor **{ctx.guild.name}**",
            color=color
        )
        
        # Registros
        embed.add_field(
            name="📝 Sistema de Registro",
            value=f"✅ Aprovados: `{total_registros}`\n❌ Negados: `{total_negados}`",
            inline=True
        )
        
        # Farms
        embed.add_field(
            name="🚜 Sistema de Farm",
            value=f"Total de Farms: `{total_farms or 0}`\nÚltimos 7 dias: `{farms_last_week or 0}`",
            inline=True
        )
        
        # Ações
        embed.add_field(
            name="⚔️ Sistema de Ações",
            value=f"Ações Criadas: `{total_acoes or 0}`",
            inline=True
        )
        
        # Totais de farm
        if total_farm_amount:
            embed.add_field(
                name="📈 Totais Acumulados",
                value=f"Farm: `{total_farm_amount:,}`\nPowder: `{total_powder:,}`\nCapsules: `{total_capsules:,}`",
                inline=False
            )
        
        # Top 5 membros
        if top_members:
            top_text = ""
            for idx, (user_id, count) in enumerate(top_members, 1):
                user = ctx.guild.get_member(user_id)
                username = user.mention if user else f"<@{user_id}>"
                top_text += f"`#{idx}` {username} - `{count}` farms\n"
            
            embed.add_field(
                name="🏆 Top 5 Membros Mais Ativos",
                value=top_text,
                inline=False
            )
        
        embed.set_footer(text=f"Solicitado por {ctx.author.display_name}")
        embed.timestamp = datetime.now()
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Stats(bot))
