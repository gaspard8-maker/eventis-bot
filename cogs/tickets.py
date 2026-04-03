import discord
from discord import app_commands
from discord.ext import commands
import db

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Ouvrir un ticket", style=discord.ButtonStyle.primary, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        data = db.load(guild.id)
        category_id = data.get("ticket_category")
        category = guild.get_channel(category_id) if category_id else None

        # Permissions du salon ticket
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        staff_role_id = data.get("staff_role")
        if staff_role_id:
            staff_role = guild.get_role(staff_role_id)
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        name = f"🎫・{interaction.user.display_name}"
        if data.get("renameautoticket", True):
            name = f"🎫・{interaction.user.display_name}"

        channel = await guild.create_text_channel(
            name=name,
            category=category,
            overwrites=overwrites
        )
        embed = discord.Embed(
            title="🎫 Ticket ouvert",
            description=f"Bonjour {interaction.user.mention} ! Notre équipe va vous répondre rapidement.",
            color=discord.Color.blurple()
        )
        close_view = CloseTicketView()
        await channel.send(embed=embed, view=close_view)
        await interaction.response.send_message(f"✅ Ticket créé : {channel.mention}", ephemeral=True)


class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Fermer le ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete(reason=f"Ticket fermé par {interaction.user}")


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(TicketView())
        bot.add_view(CloseTicketView())

    # ── /ticketpanel_setup ────────────────────────────────────
    @app_commands.command(name="ticketpanel_setup", description="Créer un panel de tickets (bouton) + définir où créer les tickets")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticketpanel_setup(self, interaction: discord.Interaction,
                                 salon_tickets: discord.TextChannel,
                                 categorie: discord.CategoryChannel):
        db.set_(interaction.guild_id, "ticket_category", categorie.id)
        embed = discord.Embed(
            title="🎫 Support",
            description="Clique sur le bouton ci-dessous pour ouvrir un ticket.",
            color=discord.Color.blurple()
        )
        await salon_tickets.send(embed=embed, view=TicketView())
        await interaction.response.send_message(f"✅ Panel de tickets créé dans {salon_tickets.mention}.", ephemeral=True)

    # ── /close-ticket ─────────────────────────────────────────
    @app_commands.command(name="close-ticket", description="Ferme le ticket en cours")
    async def close_ticket(self, interaction: discord.Interaction):
        data = db.load(interaction.guild_id)
        close_role_id = data.get("close_role")
        if close_role_id:
            role = interaction.guild.get_role(close_role_id)
            if role and role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("❌ Tu n'as pas la permission.", ephemeral=True)
                return
        await interaction.response.send_message("🔒 Fermeture du ticket...")
        await interaction.channel.delete()

    # ── /access-ticket ────────────────────────────────────────
    @app_commands.command(name="access-ticket", description="Définir le rôle qui a accès aux tickets (Buy Cart)")
    @app_commands.checks.has_permissions(administrator=True)
    async def access_ticket(self, interaction: discord.Interaction, role: discord.Role):
        db.set_(interaction.guild_id, "ticket_access_role", role.id)
        await interaction.response.send_message(f"✅ Rôle `{role.name}` défini pour l'accès aux tickets.", ephemeral=True)

    # ── /set_close_role ───────────────────────────────────────
    @app_commands.command(name="set_close_role", description="Définir le rôle autorisé à utiliser /close-ticket")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_close_role(self, interaction: discord.Interaction, role: discord.Role):
        db.set_(interaction.guild_id, "close_role", role.id)
        await interaction.response.send_message(f"✅ Rôle `{role.name}` peut fermer les tickets.", ephemeral=True)

    # ── /set_staff_role ───────────────────────────────────────
    @app_commands.command(name="set_staff_role", description="Définir le rôle mentionné pour finaliser dans les tickets")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_staff_role(self, interaction: discord.Interaction, role: discord.Role):
        db.set_(interaction.guild_id, "staff_role", role.id)
        await interaction.response.send_message(f"✅ Rôle staff : `{role.name}`.", ephemeral=True)

    # ── /set_ticket_category ──────────────────────────────────
    @app_commands.command(name="set_ticket_category", description="Choisir la catégorie des tickets")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_ticket_category(self, interaction: discord.Interaction, categorie: discord.CategoryChannel):
        db.set_(interaction.guild_id, "ticket_category", categorie.id)
        await interaction.response.send_message(f"✅ Catégorie des tickets : `{categorie.name}`.", ephemeral=True)

    # ── /renameautoticket ─────────────────────────────────────
    @app_commands.command(name="renameautoticket", description="Activer/désactiver le renommage automatique des tickets")
    @app_commands.checks.has_permissions(administrator=True)
    async def renameautoticket(self, interaction: discord.Interaction):
        current = db.get(interaction.guild_id, "renameautoticket", True)
        db.set_(interaction.guild_id, "renameautoticket", not current)
        state = "activé" if not current else "désactivé"
        await interaction.response.send_message(f"✅ Renommage automatique **{state}**.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Tickets(bot))
