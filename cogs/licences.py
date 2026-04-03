import discord
from discord import app_commands
from discord.ext import commands
import db, secrets, string

OWNER_ID = 0  # ← Remplace par ton Discord user ID

def gen_key(length=32) -> str:
    chars = string.ascii_uppercase + string.digits
    raw = ''.join(secrets.choice(chars) for _ in range(length))
    return '-'.join(raw[i:i+8] for i in range(0, length, 8))

def is_owner():
    async def pred(interaction: discord.Interaction) -> bool:
        if interaction.user.id != OWNER_ID and not interaction.user.guild_permissions.administrator:
            raise app_commands.CheckFailure("Commande réservée au Owner.")
        return True
    return app_commands.check(pred)

class Licences(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── /activer_licence ──────────────────────────────────────
    @app_commands.command(name="activer_licence", description="Activer la licence du serveur")
    async def activer_licence(self, interaction: discord.Interaction, cle: str):
        g_data = db.load_global()
        keys = g_data.get("keys", {})
        if cle not in keys:
            await interaction.response.send_message("❌ Clé invalide.", ephemeral=True)
            return
        key_data = keys[cle]
        if key_data.get("disabled"):
            await interaction.response.send_message("❌ Cette clé est désactivée.", ephemeral=True)
            return
        if key_data.get("guild_id") and key_data["guild_id"] != interaction.guild_id:
            await interaction.response.send_message("❌ Cette clé est liée à un autre serveur.", ephemeral=True)
            return
        key_data["guild_id"] = interaction.guild_id
        key_data["activated_by"] = interaction.user.id
        g_data["keys"][cle] = key_data
        db.save_global(g_data)
        db.set_(interaction.guild_id, "licence_active", True)
        db.set_(interaction.guild_id, "licence_key", cle)
        await interaction.response.send_message("✅ Licence activée avec succès !", ephemeral=True)

    # ── /key_create ───────────────────────────────────────────
    @app_commands.command(name="key_create", description="(Owner) Créer une licence (KEY) pour un utilisateur")
    @is_owner()
    async def key_create(self, interaction: discord.Interaction,
                          utilisateur: discord.User, note: str = ""):
        key = gen_key()
        g_data = db.load_global()
        g_data.setdefault("keys", {})[key] = {
            "user_id": utilisateur.id,
            "note": note,
            "disabled": False,
            "guild_id": None,
        }
        db.save_global(g_data)
        embed = discord.Embed(title="🔑 Clé créée", color=discord.Color.green())
        embed.add_field(name="Clé", value=f"`{key}`", inline=False)
        embed.add_field(name="Utilisateur", value=utilisateur.mention)
        if note:
            embed.add_field(name="Note", value=note)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        try:
            await utilisateur.send(f"🔑 Ta licence Eventis Bot : `{key}`")
        except Exception:
            pass

    # ── /key_disable ──────────────────────────────────────────
    @app_commands.command(name="key_disable", description="(Owner) Désactiver une KEY")
    @is_owner()
    async def key_disable(self, interaction: discord.Interaction, cle: str):
        g_data = db.load_global()
        if cle not in g_data.get("keys", {}):
            await interaction.response.send_message("❌ Clé introuvable.", ephemeral=True)
            return
        g_data["keys"][cle]["disabled"] = True
        db.save_global(g_data)
        await interaction.response.send_message(f"✅ Clé `{cle}` désactivée.", ephemeral=True)

    # ── /key_enable ───────────────────────────────────────────
    @app_commands.command(name="key_enable", description="(Owner) Réactiver une KEY")
    @is_owner()
    async def key_enable(self, interaction: discord.Interaction, cle: str):
        g_data = db.load_global()
        if cle not in g_data.get("keys", {}):
            await interaction.response.send_message("❌ Clé introuvable.", ephemeral=True)
            return
        g_data["keys"][cle]["disabled"] = False
        db.save_global(g_data)
        await interaction.response.send_message(f"✅ Clé `{cle}` réactivée.", ephemeral=True)

    # ── /key_info ─────────────────────────────────────────────
    @app_commands.command(name="key_info", description="(Owner) Voir l'état d'une KEY")
    @is_owner()
    async def key_info(self, interaction: discord.Interaction, cle: str):
        g_data = db.load_global()
        k = g_data.get("keys", {}).get(cle)
        if not k:
            await interaction.response.send_message("❌ Clé introuvable.", ephemeral=True)
            return
        embed = discord.Embed(title="🔑 Info clé", color=discord.Color.blurple())
        embed.add_field(name="Clé", value=f"`{cle}`", inline=False)
        embed.add_field(name="User ID", value=k.get("user_id", "N/A"))
        embed.add_field(name="Guild ID", value=k.get("guild_id", "Non activée"))
        embed.add_field(name="Statut", value="❌ Désactivée" if k.get("disabled") else "✅ Active")
        embed.add_field(name="Note", value=k.get("note") or "—")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /reset_hwid ───────────────────────────────────────────
    @app_commands.command(name="reset_hwid", description="(Owner) Reset l'HWID (permet de réutiliser la KEY sur un autre appareil)")
    @is_owner()
    async def reset_hwid(self, interaction: discord.Interaction, cle: str):
        g_data = db.load_global()
        if cle not in g_data.get("keys", {}):
            await interaction.response.send_message("❌ Clé introuvable.", ephemeral=True)
            return
        g_data["keys"][cle]["hwid"] = None
        db.save_global(g_data)
        await interaction.response.send_message(f"✅ HWID réinitialisé pour `{cle}`.", ephemeral=True)

    # ── /script_add_license ───────────────────────────────────
    @app_commands.command(name="script_add_license", description="(Owner) Ajouter/MAJ une licence script pour un membre")
    @is_owner()
    async def script_add_license(self, interaction: discord.Interaction,
                                  utilisateur: discord.User, script: str, expire: str = "never"):
        g_data = db.load_global()
        g_data.setdefault("script_licenses", {})[str(utilisateur.id)] = {
            "script": script, "expire": expire, "active": True
        }
        db.save_global(g_data)
        await interaction.response.send_message(
            f"✅ Licence script `{script}` ajoutée pour {utilisateur.mention}.", ephemeral=True
        )

    # ── /script_license_info ──────────────────────────────────
    @app_commands.command(name="script_license_info", description="(Owner) Voir les infos d'une licence script")
    @is_owner()
    async def script_license_info(self, interaction: discord.Interaction, utilisateur: discord.User):
        g_data = db.load_global()
        lic = g_data.get("script_licenses", {}).get(str(utilisateur.id))
        if not lic:
            await interaction.response.send_message("❌ Aucune licence script.", ephemeral=True)
            return
        embed = discord.Embed(title="📜 Licence script", color=discord.Color.blurple())
        embed.add_field(name="Script", value=lic["script"])
        embed.add_field(name="Expire", value=lic["expire"])
        embed.add_field(name="Actif", value="✅" if lic["active"] else "❌")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /script_license_user ──────────────────────────────────
    @app_commands.command(name="script_license_user", description="(Owner) Voir la licence script liée à un membre")
    @is_owner()
    async def script_license_user(self, interaction: discord.Interaction, utilisateur: discord.User):
        await self.script_license_info.callback(self, interaction, utilisateur)

    # ── /script_remove_license ────────────────────────────────
    @app_commands.command(name="script_remove_license", description="(Owner) Supprimer une licence script")
    @is_owner()
    async def script_remove_license(self, interaction: discord.Interaction, utilisateur: discord.User):
        g_data = db.load_global()
        g_data.get("script_licenses", {}).pop(str(utilisateur.id), None)
        db.save_global(g_data)
        await interaction.response.send_message(f"✅ Licence script supprimée pour {utilisateur.mention}.", ephemeral=True)

    # ── /script_toggle_license ────────────────────────────────
    @app_commands.command(name="script_toggle_license", description="(Owner) Activer/Désactiver une licence script")
    @is_owner()
    async def script_toggle_license(self, interaction: discord.Interaction, utilisateur: discord.User):
        g_data = db.load_global()
        lic = g_data.get("script_licenses", {}).get(str(utilisateur.id))
        if not lic:
            await interaction.response.send_message("❌ Aucune licence script.", ephemeral=True)
            return
        lic["active"] = not lic["active"]
        db.save_global(g_data)
        state = "activée" if lic["active"] else "désactivée"
        await interaction.response.send_message(f"✅ Licence script **{state}** pour {utilisateur.mention}.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Licences(bot))
