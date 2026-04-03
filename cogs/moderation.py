import discord
from discord import app_commands
from discord.ext import commands
import db

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── /ban ──────────────────────────────────────────────────
    @app_commands.command(name="ban", description="Bannir un membre avec une raison")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction,
                  membre: discord.Member, raison: str = "Aucune raison"):
        await membre.ban(reason=raison)
        embed = discord.Embed(
            title="🔨 Membre banni",
            description=f"**{membre}** a été banni.\n📝 Raison : {raison}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

    # ── /kick ─────────────────────────────────────────────────
    @app_commands.command(name="kick", description="Kick un membre avec une raison")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction,
                   membre: discord.Member, raison: str = "Aucune raison"):
        await membre.kick(reason=raison)
        embed = discord.Embed(
            title="👢 Membre kické",
            description=f"**{membre}** a été kické.\n📝 Raison : {raison}",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)

    # ── /mute ─────────────────────────────────────────────────
    @app_commands.command(name="mute", description="Mute (timeout) un membre en minutes")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction,
                   membre: discord.Member, minutes: int, raison: str = "Aucune raison"):
        import datetime
        until = discord.utils.utcnow() + datetime.timedelta(minutes=minutes)
        await membre.timeout(until, reason=raison)
        embed = discord.Embed(
            title="🔇 Membre muté",
            description=f"**{membre}** muté pour **{minutes} min**.\n📝 Raison : {raison}",
            color=discord.Color.yellow()
        )
        await interaction.response.send_message(embed=embed)

    # ── /warn ─────────────────────────────────────────────────
    @app_commands.command(name="warn", description="Warn un membre")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction,
                   membre: discord.Member, raison: str = "Aucune raison"):
        data = db.load(interaction.guild_id)
        warns = data.setdefault("warns", {})
        uid = str(membre.id)
        warns.setdefault(uid, []).append(raison)
        db.save(interaction.guild_id, data)
        embed = discord.Embed(
            title="⚠️ Avertissement",
            description=f"**{membre}** a reçu un warn ({len(warns[uid])} total).\n📝 {raison}",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed)

    # ── /unwarn ───────────────────────────────────────────────
    @app_commands.command(name="unwarn", description="Supprimer un warning (par ID)")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unwarn(self, interaction: discord.Interaction,
                     membre: discord.Member, index: int):
        data = db.load(interaction.guild_id)
        warns = data.get("warns", {}).get(str(membre.id), [])
        if not warns or index < 1 or index > len(warns):
            await interaction.response.send_message("❌ Index invalide.", ephemeral=True)
            return
        removed = warns.pop(index - 1)
        db.save(interaction.guild_id, data)
        await interaction.response.send_message(
            f"✅ Warn #{index} supprimé pour **{membre}** : `{removed}`"
        )

    # ── /warnings ─────────────────────────────────────────────
    @app_commands.command(name="warnings", description="Voir les warnings d'un membre")
    async def warnings(self, interaction: discord.Interaction, membre: discord.Member):
        warns = db.load(interaction.guild_id).get("warns", {}).get(str(membre.id), [])
        if not warns:
            await interaction.response.send_message(f"✅ **{membre}** n'a aucun warn.", ephemeral=True)
            return
        lines = "\n".join(f"`{i+1}.` {r}" for i, r in enumerate(warns))
        embed = discord.Embed(title=f"⚠️ Warns de {membre}", description=lines, color=discord.Color.orange())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /clear ────────────────────────────────────────────────
    @app_commands.command(name="clear", description="Supprimer un nombre de messages dans ce salon")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, nombre: int):
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=nombre)
        await interaction.followup.send(f"🗑️ {len(deleted)} messages supprimés.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
