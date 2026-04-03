import discord
from discord import app_commands
from discord.ext import commands
import db

class RoleButtonView(discord.ui.View):
    """Vue persistante pour les boutons de rôle."""
    def __init__(self):
        super().__init__(timeout=None)

class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── /setup_roles ──────────────────────────────────────────
    @app_commands.command(name="setup_roles", description="Créer un message de sélection de rôles (jusqu'à 5 rôles)")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_roles(self, interaction: discord.Interaction,
                          role1: discord.Role,
                          role2: discord.Role = None,
                          role3: discord.Role = None,
                          role4: discord.Role = None,
                          role5: discord.Role = None,
                          titre: str = "Choisissez vos rôles",
                          description: str = "Clique sur un bouton pour obtenir ou retirer un rôle."):
        roles = [r for r in [role1, role2, role3, role4, role5] if r]
        view = discord.ui.View(timeout=None)
        for role in roles:
            btn = discord.ui.Button(
                label=role.name,
                style=discord.ButtonStyle.secondary,
                custom_id=f"role_{role.id}"
            )
            async def callback(inter: discord.Interaction, r=role):
                if r in inter.user.roles:
                    await inter.user.remove_roles(r)
                    await inter.response.send_message(f"❌ Rôle **{r.name}** retiré.", ephemeral=True)
                else:
                    await inter.user.add_roles(r)
                    await inter.response.send_message(f"✅ Rôle **{r.name}** attribué.", ephemeral=True)
            btn.callback = callback
            view.add_item(btn)

        embed = discord.Embed(title=titre, description=description, color=discord.Color.blurple())
        msg = await interaction.channel.send(embed=embed, view=view)
        db.set_(interaction.guild_id, "roles_message_id", msg.id)
        await interaction.response.send_message("✅ Message de sélection de rôles créé.", ephemeral=True)

    # ── /add_role_button ──────────────────────────────────────
    @app_commands.command(name="add_role_button", description="Ajouter un bouton de rôle au message existant")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_role_button(self, interaction: discord.Interaction,
                               message_id: str, role: discord.Role):
        try:
            msg = await interaction.channel.fetch_message(int(message_id))
        except Exception:
            await interaction.response.send_message("❌ Message introuvable.", ephemeral=True)
            return
        # On ne peut pas modifier dynamiquement une view persistante sans recréer
        await interaction.response.send_message(
            f"⚠️ Bouton pour `{role.name}` noté. Recrée le panel avec `/setup_roles` pour l'inclure.",
            ephemeral=True
        )

    # ── /remove_role_button ───────────────────────────────────
    @app_commands.command(name="remove_role_button", description="Supprimer un bouton de rôle du message existant")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_role_button(self, interaction: discord.Interaction,
                                  message_id: str, role: discord.Role):
        await interaction.response.send_message(
            f"⚠️ Suppression du bouton `{role.name}` notée. Recrée le panel avec `/setup_roles`.",
            ephemeral=True
        )

    # ── /reset_roles ──────────────────────────────────────────
    @app_commands.command(name="reset_roles", description="Supprimer le message de rôles et toute la configuration")
    @app_commands.checks.has_permissions(administrator=True)
    async def reset_roles(self, interaction: discord.Interaction):
        msg_id = db.get(interaction.guild_id, "roles_message_id")
        if msg_id:
            try:
                msg = await interaction.channel.fetch_message(msg_id)
                await msg.delete()
            except Exception:
                pass
        db.set_(interaction.guild_id, "roles_message_id", None)
        await interaction.response.send_message("✅ Configuration des rôles réinitialisée.", ephemeral=True)

    # ── /good_perm_role ───────────────────────────────────────
    @app_commands.command(name="good_perm_role", description="Définir le rôle autorisé à utiliser le bouton ✅ Good")
    @app_commands.checks.has_permissions(administrator=True)
    async def good_perm_role(self, interaction: discord.Interaction, role: discord.Role):
        db.set_(interaction.guild_id, "good_perm_role", role.id)
        await interaction.response.send_message(f"✅ Rôle `{role.name}` peut utiliser le bouton Good.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Roles(bot))
