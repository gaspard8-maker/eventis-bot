import discord
from discord import app_commands
from discord.ext import commands
import db, json, random

class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.participants = []

    @discord.ui.button(label="🎉 Participer", style=discord.ButtonStyle.primary, custom_id="giveaway_join")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        if uid in self.participants:
            self.participants.remove(uid)
            await interaction.response.send_message("❌ Tu as quitté le giveaway.", ephemeral=True)
        else:
            self.participants.append(uid)
            await interaction.response.send_message("✅ Tu participes au giveaway !", ephemeral=True)
        button.label = f"🎉 Participer ({len(self.participants)})"
        await interaction.message.edit(view=self)

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── /embed ────────────────────────────────────────────────
    @app_commands.command(name="embed", description="Créer un embed dans un salon, avec bouton ticket optionnel")
    @app_commands.checks.has_permissions(administrator=True)
    async def embed(self, interaction: discord.Interaction,
                    titre: str, description: str,
                    couleur: str = "blurple",
                    avec_ticket: bool = False,
                    salon: discord.TextChannel = None):
        couleurs = {
            "blurple": discord.Color.blurple(), "rouge": discord.Color.red(),
            "vert": discord.Color.green(), "orange": discord.Color.orange(),
            "jaune": discord.Color.yellow(), "blanc": discord.Color.white(),
        }
        color = couleurs.get(couleur.lower(), discord.Color.blurple())
        embed = discord.Embed(title=titre, description=description, color=color)
        target = salon or interaction.channel
        view = None
        if avec_ticket:
            from cogs.tickets import TicketView
            view = TicketView()
        await target.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Embed envoyé.", ephemeral=True)

    # ── /dump_embed ───────────────────────────────────────────
    @app_commands.command(name="dump_embed", description="Exporter en JSON un message avec embed (pour debug)")
    @app_commands.checks.has_permissions(administrator=True)
    async def dump_embed(self, interaction: discord.Interaction, message_id: str):
        try:
            msg = await interaction.channel.fetch_message(int(message_id))
        except Exception:
            await interaction.response.send_message("❌ Message introuvable.", ephemeral=True)
            return
        if not msg.embeds:
            await interaction.response.send_message("❌ Pas d'embed dans ce message.", ephemeral=True)
            return
        data = msg.embeds[0].to_dict()
        pretty = json.dumps(data, indent=2, ensure_ascii=False)
        await interaction.response.send_message(f"```json\n{pretty[:1900]}\n```", ephemeral=True)

    # ── /giveaway_start ───────────────────────────────────────
    @app_commands.command(name="giveaway_start", description="Lancer un giveaway (bouton)")
    @app_commands.checks.has_permissions(administrator=True)
    async def giveaway_start(self, interaction: discord.Interaction,
                              lot: str, duree_minutes: int = 60):
        view = GiveawayView()
        embed = discord.Embed(
            title="🎉 GIVEAWAY",
            description=f"**Lot :** {lot}\n**Durée :** {duree_minutes} minutes\n\nClique sur le bouton pour participer !",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed, view=view)
        msg = await interaction.original_response()

        import asyncio
        await asyncio.sleep(duree_minutes * 60)
        if not view.participants:
            await msg.reply("❌ Aucun participant, giveaway annulé.")
            return
        winner_id = random.choice(view.participants)
        winner = interaction.guild.get_member(winner_id)
        await msg.reply(f"🎉 Félicitations {winner.mention} ! Tu as gagné **{lot}** !")

    # ── /welcome_setup ────────────────────────────────────────
    @app_commands.command(name="welcome_setup", description="Activer/désactiver le message de bienvenue")
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_setup(self, interaction: discord.Interaction,
                             salon: discord.TextChannel = None,
                             message: str = "Bienvenue {user} sur {server} !"):
        data = db.load(interaction.guild_id)
        if data.get("welcome_enabled") and not salon:
            data["welcome_enabled"] = False
            db.save(interaction.guild_id, data)
            await interaction.response.send_message("✅ Message de bienvenue **désactivé**.", ephemeral=True)
        else:
            data["welcome_enabled"] = True
            data["welcome_channel"] = salon.id if salon else None
            data["welcome_message"] = message
            db.save(interaction.guild_id, data)
            await interaction.response.send_message(
                f"✅ Message de bienvenue **activé** dans {salon.mention if salon else 'ce salon'}.", ephemeral=True
            )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        data = db.load(member.guild.id)
        if not data.get("welcome_enabled"):
            return
        ch_id = data.get("welcome_channel")
        ch = member.guild.get_channel(ch_id) if ch_id else None
        if not ch:
            return
        msg = data.get("welcome_message", "Bienvenue {user} sur {server} !")
        msg = msg.replace("{user}", member.mention).replace("{server}", member.guild.name)
        await ch.send(msg)

    # ── /list ─────────────────────────────────────────────────
    @app_commands.command(name="list", description="Liste tous les channels avec leurs IDs")
    @app_commands.checks.has_permissions(administrator=True)
    async def list_channels(self, interaction: discord.Interaction):
        lines = []
        for ch in interaction.guild.channels:
            lines.append(f"`{ch.id}` — {ch.name} ({ch.type})")
        text = "\n".join(lines)
        chunks = [text[i:i+1900] for i in range(0, len(text), 1900)]
        await interaction.response.send_message(f"📋 Channels :\n{chunks[0]}", ephemeral=True)
        for chunk in chunks[1:]:
            await interaction.followup.send(chunk, ephemeral=True)

    # ── /gcpsg ────────────────────────────────────────────────
    @app_commands.command(name="gcpsg", description="Lien vers les cartes cadeaux PSG")
    async def gcpsg(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎁 Cartes cadeaux PSG",
            description="[Cliquez ici pour accéder aux cartes cadeaux PSG](https://www.psg.fr/)",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))
