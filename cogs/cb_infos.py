import discord
from discord import app_commands
from discord.ext import commands
import db

OWNER_ID = 0  # ← Remplace par ton Discord user ID

def is_owner():
    async def pred(interaction: discord.Interaction) -> bool:
        if interaction.user.id != OWNER_ID and not interaction.user.guild_permissions.administrator:
            raise app_commands.CheckFailure("Commande réservée au Owner.")
        return True
    return app_commands.check(pred)

class CBInfos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── /register ─────────────────────────────────────────────
    @app_commands.command(name="register", description="Enregistrer tes infos CB")
    async def register(self, interaction: discord.Interaction,
                       nom: str, prenom: str, email: str):
        data = db.load(interaction.guild_id)
        data.setdefault("cb_users", {})[str(interaction.user.id)] = {
            "nom": nom, "prenom": prenom, "email": email
        }
        db.save(interaction.guild_id, data)
        await interaction.response.send_message("✅ Infos CB enregistrées.", ephemeral=True)

    # ── /register_plus ────────────────────────────────────────
    @app_commands.command(name="register_plus", description="Enregistrer tes infos CB (version étendue)")
    async def register_plus(self, interaction: discord.Interaction,
                             nom: str, prenom: str, email: str,
                             telephone: str = "", adresse: str = ""):
        data = db.load(interaction.guild_id)
        data.setdefault("cb_users", {})[str(interaction.user.id)] = {
            "nom": nom, "prenom": prenom, "email": email,
            "telephone": telephone, "adresse": adresse
        }
        db.save(interaction.guild_id, data)
        await interaction.response.send_message("✅ Infos CB+ enregistrées.", ephemeral=True)

    # ── /myinfos ──────────────────────────────────────────────
    @app_commands.command(name="myinfos", description="Voir tes infos CB")
    async def myinfos(self, interaction: discord.Interaction):
        infos = db.load(interaction.guild_id).get("cb_users", {}).get(str(interaction.user.id))
        if not infos:
            await interaction.response.send_message("❌ Aucune info enregistrée. Utilise `/register`.", ephemeral=True)
            return
        embed = discord.Embed(title="📋 Tes infos CB", color=discord.Color.blurple())
        for k, v in infos.items():
            if v:
                embed.add_field(name=k.capitalize(), value=v, inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /myinfos_plus ─────────────────────────────────────────
    @app_commands.command(name="myinfos_plus", description="Voir tes infos CB (version étendue)")
    async def myinfos_plus(self, interaction: discord.Interaction):
        await self.myinfos.callback(self, interaction)

    # ── /edit_infos ───────────────────────────────────────────
    @app_commands.command(name="edit_infos", description="Modifier tes infos CB")
    async def edit_infos(self, interaction: discord.Interaction,
                          champ: str, valeur: str):
        data = db.load(interaction.guild_id)
        user_data = data.setdefault("cb_users", {}).setdefault(str(interaction.user.id), {})
        user_data[champ.lower()] = valeur
        db.save(interaction.guild_id, data)
        await interaction.response.send_message(f"✅ Champ `{champ}` mis à jour.", ephemeral=True)

    # ── /edit_infos_plus ──────────────────────────────────────
    @app_commands.command(name="edit_infos_plus", description="Modifier tes infos CB (version étendue)")
    async def edit_infos_plus(self, interaction: discord.Interaction,
                               champ: str, valeur: str):
        await self.edit_infos.callback(self, interaction, champ, valeur)

    # ── /admin_infos ──────────────────────────────────────────
    @app_commands.command(name="admin_infos", description="(Owner) Voir toutes les infos CB")
    @is_owner()
    async def admin_infos(self, interaction: discord.Interaction, membre: discord.Member):
        infos = db.load(interaction.guild_id).get("cb_users", {}).get(str(membre.id))
        if not infos:
            await interaction.response.send_message(f"❌ Aucune info pour {membre}.", ephemeral=True)
            return
        embed = discord.Embed(title=f"📋 Infos CB de {membre}", color=discord.Color.orange())
        for k, v in infos.items():
            if v:
                embed.add_field(name=k.capitalize(), value=v, inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /admin_infos_plus ─────────────────────────────────────
    @app_commands.command(name="admin_infos_plus", description="(Owner) Voir toutes les infos CB (étendu)")
    @is_owner()
    async def admin_infos_plus(self, interaction: discord.Interaction, membre: discord.Member):
        await self.admin_infos.callback(self, interaction, membre)

    # ── Quotas ────────────────────────────────────────────────
    @app_commands.command(name="quota_toggle", description="Activer ou désactiver le système de quotas sur ce serveur")
    @app_commands.checks.has_permissions(administrator=True)
    async def quota_toggle(self, interaction: discord.Interaction):
        current = db.get(interaction.guild_id, "quota_enabled", False)
        db.set_(interaction.guild_id, "quota_enabled", not current)
        state = "activé" if not current else "désactivé"
        await interaction.response.send_message(f"✅ Système de quotas **{state}**.", ephemeral=True)

    @app_commands.command(name="quota_add", description="Ajouter des quotas à un membre (1 quota = 1€)")
    @app_commands.checks.has_permissions(administrator=True)
    async def quota_add(self, interaction: discord.Interaction,
                         membre: discord.Member, montant: int):
        data = db.load(interaction.guild_id)
        quotas = data.setdefault("quotas", {})
        quotas[str(membre.id)] = quotas.get(str(membre.id), 0) + montant
        db.save(interaction.guild_id, data)
        await interaction.response.send_message(
            f"✅ {montant} quota(s) ajouté(s) à {membre.mention}. Total : {quotas[str(membre.id)]}€", ephemeral=True
        )

    @app_commands.command(name="quota_show", description="Voir ton solde de quotas (si activé)")
    async def quota_show(self, interaction: discord.Interaction):
        if not db.get(interaction.guild_id, "quota_enabled", False):
            await interaction.response.send_message("❌ Le système de quotas n'est pas activé.", ephemeral=True)
            return
        val = db.load(interaction.guild_id).get("quotas", {}).get(str(interaction.user.id), 0)
        await interaction.response.send_message(f"💰 Tu as **{val}€** de quotas.", ephemeral=True)

    @app_commands.command(name="quota_list", description="Voir les quotas de tous les membres (si quotas activés)")
    @app_commands.checks.has_permissions(administrator=True)
    async def quota_list(self, interaction: discord.Interaction):
        if not db.get(interaction.guild_id, "quota_enabled", False):
            await interaction.response.send_message("❌ Quotas non activés.", ephemeral=True)
            return
        quotas = db.load(interaction.guild_id).get("quotas", {})
        if not quotas:
            await interaction.response.send_message("Aucun quota enregistré.", ephemeral=True)
            return
        lines = [f"<@{uid}> : **{val}€**" for uid, val in quotas.items()]
        embed = discord.Embed(title="💰 Quotas", description="\n".join(lines), color=discord.Color.gold())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="quota_perm_role", description="Définir un rôle qui peut gérer les quotas")
    @app_commands.checks.has_permissions(administrator=True)
    async def quota_perm_role(self, interaction: discord.Interaction, role: discord.Role):
        db.set_(interaction.guild_id, "quota_perm_role", role.id)
        await interaction.response.send_message(f"✅ Rôle `{role.name}` peut gérer les quotas.", ephemeral=True)

    # ── /carts_analytics ──────────────────────────────────────
    @app_commands.command(name="carts_analytics", description="Voir les stats de paniers pris (7 derniers jours)")
    @app_commands.checks.has_permissions(administrator=True)
    async def carts_analytics(self, interaction: discord.Interaction):
        data = db.load(interaction.guild_id)
        carts = data.get("carts", [])
        # Filtre 7 jours
        import datetime
        cutoff = (discord.utils.utcnow() - datetime.timedelta(days=7)).timestamp()
        recent = [c for c in carts if c.get("ts", 0) > cutoff]
        total = sum(c.get("amount", 0) for c in recent)
        embed = discord.Embed(
            title="📊 Analytics Paniers (7j)",
            description=f"**Paniers :** {len(recent)}\n**Total :** {total}€",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /warning_message ──────────────────────────────────────
    @app_commands.command(name="warning_message", description="Activer ou désactiver le gros message d'avertissement sur les paniers")
    @app_commands.checks.has_permissions(administrator=True)
    async def warning_message(self, interaction: discord.Interaction):
        current = db.get(interaction.guild_id, "warning_message", False)
        db.set_(interaction.guild_id, "warning_message", not current)
        state = "activé" if not current else "désactivé"
        await interaction.response.send_message(f"✅ Message d'avertissement **{state}**.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CBInfos(bot))
