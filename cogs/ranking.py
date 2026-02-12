import discord
from discord.ext import commands
import aiosqlite
from datetime import datetime, timedelta

class Ranking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ranking", aliases=["rank", "top"])
    async def ranking_command(self, ctx, periodo: str = "total"):
        """
        Mostra o ranking de farm.
        Uso: !ranking [semanal|mensal|total]
        """
        periodo = periodo.lower()
        
        if periodo not in ["semanal", "mensal", "total", "semana", "mes"]:
            await ctx.send("❌ Período inválido! Use: `semanal`, `mensal` ou `total`")
            return
        
        # Normalizar nomes
        if periodo == "semana":
            periodo = "semanal"
        elif periodo == "mes":
            periodo = "mensal"
        
        # Calcular data de corte
        now = datetime.now()
        if periodo == "semanal":
            cutoff_date = now - timedelta(days=7)
            title = "🏆 Ranking Semanal de Farm"
        elif periodo == "mensal":
            cutoff_date = now - timedelta(days=30)
            title = "🏆 Ranking Mensal de Farm"
        else:
            cutoff_date = datetime(2000, 1, 1)  # Data muito antiga = todos os registros
            title = "🏆 Ranking Total de Farm"
        
        # Buscar dados do banco
        async with aiosqlite.connect("database.db") as db:
            # Buscar cor customizada
            cursor = await db.execute(
                "SELECT stats_color FROM bot_customization WHERE guild_id = ?",
                (ctx.guild.id,)
            )
            row = await cursor.fetchone()
            color_hex = row[0] if row else "#3498DB"
            
            # Converter hex para int
            color = int(color_hex.replace("#", ""), 16)
            
            # Buscar ranking
            query = """
                SELECT 
                    user_id,
                    SUM(farm_amount) as total_farm,
                    SUM(powder_amount) as total_powder,
                    SUM(capsule_amount) as total_capsules,
                    COUNT(*) as total_farms,
                    (SUM(farm_amount) + (SUM(powder_amount) * 0.5) + (SUM(capsule_amount) * 2)) as score
                FROM farms
                WHERE guild_id = ? AND timestamp >= ?
                GROUP BY user_id
                ORDER BY score DESC
                LIMIT 10
            """
            
            cursor = await db.execute(query, (ctx.guild.id, cutoff_date.isoformat()))
            results = await cursor.fetchall()
        
        if not results:
            await ctx.send(f"📊 Nenhum farm registrado no período **{periodo}**.")
            return
        
        # Criar embed
        embed = discord.Embed(title=title, color=color)
        embed.set_footer(text=f"Período: {periodo.capitalize()} | Score = Farm + (Powder × 0.5) + (Capsules × 2)")
        
        description = ""
        medals = ["🥇", "🥈", "🥉"]
        
        for idx, (user_id, farm, powder, capsules, count, score) in enumerate(results, 1):
            user = ctx.guild.get_member(user_id)
            username = user.mention if user else f"<@{user_id}>"
            
            medal = medals[idx - 1] if idx <= 3 else f"`#{idx}`"
            
            description += f"{medal} **{username}**\n"
            description += f"   └ Farm: `{farm:,}` | Powder: `{powder:,}` | Capsules: `{capsules:,}`\n"
            description += f"   └ Total de Farms: `{count}` | **Score: `{score:,.1f}`**\n\n"
        
        embed.description = description
        
        await ctx.send(embed=embed)

    @commands.command(name="meusfarms", aliases=["farms", "meufarm"])
    async def my_farms(self, ctx, membro: discord.Member = None):
        """
        Mostra o histórico de farms de um usuário.
        Uso: !meusfarms [@usuario]
        """
        target = membro or ctx.author
        
        async with aiosqlite.connect("database.db") as db:
            # Buscar cor customizada
            cursor = await db.execute(
                "SELECT farm_color FROM bot_customization WHERE guild_id = ?",
                (ctx.guild.id,)
            )
            row = await cursor.fetchone()
            color_hex = row[0] if row else "#FFD700"
            color = int(color_hex.replace("#", ""), 16)
            
            # Buscar farms do usuário (últimos 10)
            query = """
                SELECT farm_amount, powder_amount, capsule_amount, timestamp
                FROM farms
                WHERE user_id = ? AND guild_id = ?
                ORDER BY timestamp DESC
                LIMIT 10
            """
            
            cursor = await db.execute(query, (target.id, ctx.guild.id))
            farms = await cursor.fetchall()
            
            # Buscar totais
            cursor = await db.execute("""
                SELECT 
                    SUM(farm_amount),
                    SUM(powder_amount),
                    SUM(capsule_amount),
                    COUNT(*)
                FROM farms
                WHERE user_id = ? AND guild_id = ?
            """, (target.id, ctx.guild.id))
            
            totals = await cursor.fetchone()
        
        if not farms:
            await ctx.send(f"📊 {target.mention} ainda não registrou nenhum farm.")
            return
        
        # Criar embed
        embed = discord.Embed(
            title=f"📊 Histórico de Farms - {target.display_name}",
            color=color
        )
        
        total_farm, total_powder, total_capsules, total_count = totals
        
        embed.add_field(
            name="📈 Totais Acumulados",
            value=f"**Farm:** `{total_farm:,}`\n**Powder:** `{total_powder:,}`\n**Capsules:** `{total_capsules:,}`\n**Total de Farms:** `{total_count}`",
            inline=False
        )
        
        # Últimos 10 farms
        history = ""
        for farm, powder, capsules, timestamp in farms:
            dt = datetime.fromisoformat(timestamp)
            date_str = dt.strftime("%d/%m/%Y %H:%M")
            history += f"**{date_str}**\n└ Farm: `{farm:,}` | Powder: `{powder:,}` | Capsules: `{capsules:,}`\n\n"
        
        embed.add_field(
            name="📜 Últimos 10 Farms",
            value=history if history else "Nenhum farm registrado",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command(name="resetranking")
    async def reset_ranking(self, ctx, tipo: str = "semanal"):
        """
        Reseta o ranking (apenas admin).
        Uso: !resetranking [semanal|mensal|total]
        """
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Você precisa de permissão de Administrador para resetar o ranking.")
            return
        
        tipo = tipo.lower()
        if tipo not in ["semanal", "mensal", "total"]:
            await ctx.send("❌ Tipo inválido! Use: `semanal`, `mensal` ou `total`")
            return
        
        # Confirmação
        confirm_msg = await ctx.send(
            f"⚠️ **ATENÇÃO!** Você está prestes a resetar o ranking **{tipo}**.\n"
            f"Isso irá {'**DELETAR TODOS OS FARMS**' if tipo == 'total' else 'marcar um ponto de reset'}!\n\n"
            f"Reaja com ✅ para confirmar ou ❌ para cancelar."
        )
        
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == "❌":
                await ctx.send("❌ Reset cancelado.")
                return
            
            # Executar reset
            async with aiosqlite.connect("database.db") as db:
                if tipo == "total":
                    # Deletar todos os farms
                    await db.execute("DELETE FROM farms WHERE guild_id = ?", (ctx.guild.id,))
                    await db.commit()
                    await ctx.send("✅ **Ranking total resetado!** Todos os farms foram deletados.")
                else:
                    # Registrar reset no histórico
                    await db.execute(
                        "INSERT INTO ranking_resets (guild_id, reset_type, reset_by) VALUES (?, ?, ?)",
                        (ctx.guild.id, tipo, ctx.author.id)
                    )
                    await db.commit()
                    await ctx.send(f"✅ **Ponto de reset {tipo} criado!** O ranking {tipo} agora começa do zero.")
        
        except TimeoutError:
            await ctx.send("⏱️ Tempo esgotado. Reset cancelado.")

async def setup(bot):
    await bot.add_cog(Ranking(bot))
