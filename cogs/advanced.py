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

class Advanced(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ════════════════════════════════════════════════════════════
    # WEBHOOK RELAY
    # ════════════════════════════════════════════════════════════

    @app_commands.command(name="webhook", description="Relayer un salon source vers un ou plusieurs salons destination")
    @app_commands.checks.has_permissions(administrator=True)
    async def webhook(self, interaction: discord.Interaction,
                      source: discord.TextChannel,
                      dest: discord.TextChannel,
                      dest2: discord.TextChannel = None,
                      dest3: discord.TextChannel = None,
                      mention_role: discord.Role = None,
                      include_payment_link: bool = False,
                      show_public_info: bool = False,
                      expire_minutes: int = 0):
        data = db.load(interaction.guild_id)
        destinations = [d.id for d in [dest, dest2, dest3] if d]
        data.setdefault("webhook_relays", {})[str(source.id)] = destinations
        data.setdefault("webhook_options", {})[str(source.id)] = {
            "mention_role": mention_role.id if mention_role else None,
            "include_payment_link": include_payment_link,
            "show_public_info": show_public_info,
            "expire_minutes": expire_minutes,
        }
        db.save(interaction.guild_id, data)
        dests_mentions = " + ".join([d.mention for d in [dest, dest2, dest3] if d])
        await interaction.response.send_message(
            f"✅ Relais : {source.mention} → {dests_mentions}", ephemeral=True
        )

    @app_commands.command(name="webhook_stop", description="Arrêter la redirection d'un salon")
    @app_commands.checks.has_permissions(administrator=True)
    async def webhook_stop(self, interaction: discord.Interaction, source: discord.TextChannel):
        data = db.load(interaction.guild_id)
        data.get("webhook_relays", {}).pop(str(source.id), None)
        db.save(interaction.guild_id, data)
        await interaction.response.send_message(f"✅ Relais pour {source.mention} supprimé.", ephemeral=True)

    @app_commands.command(name="set_webhook_role", description="Définir le rôle autorisé à utiliser /webhook")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_webhook_role(self, interaction: discord.Interaction, role: discord.Role):
        db.set_(interaction.guild_id, "webhook_role", role.id)
        await interaction.response.send_message(f"✅ Rôle `{role.name}` peut utiliser /webhook.", ephemeral=True)

    @app_commands.command(name="webhook_pasfixed", description="Définir un PAS fixé (€/place) pour un salon source")
    @app_commands.checks.has_permissions(administrator=True)
    async def webhook_pasfixed(self, interaction: discord.Interaction,
                                source: discord.TextChannel, euros_par_place: float):
        data = db.load(interaction.guild_id)
        data.setdefault("webhook_pas", {})[str(source.id)] = {"mode": "fixed", "value": euros_par_place}
        db.save(interaction.guild_id, data)
        await interaction.response.send_message(f"✅ PAS fixé à **{euros_par_place}€** pour {source.mention}.", ephemeral=True)

    @app_commands.command(name="webhook_pasmap", description="Définir la table PAS par catégories (mode 'map')")
    @app_commands.checks.has_permissions(administrator=True)
    async def webhook_pasmap(self, interaction: discord.Interaction,
                              source: discord.TextChannel, map_json: str):
        import json as _json
        try:
            mapping = _json.loads(map_json)
        except Exception:
            await interaction.response.send_message("❌ JSON invalide.", ephemeral=True)
            return
        data = db.load(interaction.guild_id)
        data.setdefault("webhook_pas", {})[str(source.id)] = {"mode": "map", "value": mapping}
        db.save(interaction.guild_id, data)
        await interaction.response.send_message(f"✅ PAS map définie pour {source.mention}.", ephemeral=True)

    @app_commands.command(name="webhook_pasreset", description="Remettre le PAS sur 'auto' pour un salon source")
    @app_commands.checks.has_permissions(administrator=True)
    async def webhook_pasreset(self, interaction: discord.Interaction, source: discord.TextChannel):
        data = db.load(interaction.guild_id)
        data.get("webhook_pas", {}).pop(str(source.id), None)
        db.save(interaction.guild_id, data)
        await interaction.response.send_message(f"✅ PAS remis sur auto pour {source.mention}.", ephemeral=True)

    @app_commands.command(name="pas_list", description="Voir la liste des PAS configurés pour les salons source")
    @app_commands.checks.has_permissions(administrator=True)
    async def pas_list(self, interaction: discord.Interaction):
        pas_data = db.load(interaction.guild_id).get("webhook_pas", {})
        if not pas_data:
            await interaction.response.send_message("Aucun PAS configuré.", ephemeral=True)
            return
        lines = [f"<#{ch_id}> → `{v}`" for ch_id, v in pas_data.items()]
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        relays = db.load(message.guild.id).get("webhook_relays", {})
        dest_ids = relays.get(str(message.channel.id), [])
        for dest_id in dest_ids:
            dest = message.guild.get_channel(dest_id)
            if dest:
                embed = discord.Embed(description=message.content, color=discord.Color.greyple())
                embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
                await dest.send(embed=embed)

    # ════════════════════════════════════════════════════════════
    # INFO MESSAGES
    # ════════════════════════════════════════════════════════════

    @app_commands.command(name="info_create", description="Créer ou modifier une info (ex: paiement)")
    @app_commands.checks.has_permissions(administrator=True)
    async def info_create(self, interaction: discord.Interaction, nom: str, contenu: str):
        data = db.load(interaction.guild_id)
        data.setdefault("infos", {})[nom.lower()] = contenu
        db.save(interaction.guild_id, data)
        await interaction.response.send_message(f"✅ Info `{nom}` enregistrée.", ephemeral=True)

    @app_commands.command(name="info_delete", description="Supprimer une info pré-enregistrée")
    @app_commands.checks.has_permissions(administrator=True)
    async def info_delete(self, interaction: discord.Interaction, nom: str):
        data = db.load(interaction.guild_id)
        data.get("infos", {}).pop(nom.lower(), None)
        db.save(interaction.guild_id, data)
        await interaction.response.send_message(f"✅ Info `{nom}` supprimée.", ephemeral=True)

    @app_commands.command(name="info", description="Envoyer une info pré-enregistrée (paiement, etc.)")
    async def info(self, interaction: discord.Interaction, nom: str):
        infos = db.load(interaction.guild_id).get("infos", {})
        content = infos.get(nom.lower())
        if not content:
            await interaction.response.send_message(f"❌ Info `{nom}` introuvable.", ephemeral=True)
            return
        await interaction.response.send_message(content)

    # ════════════════════════════════════════════════════════════
    # COMMANDES PERSONNALISÉES
    # ════════════════════════════════════════════════════════════

    @app_commands.command(name="creer_commande", description="Crée ou modifie une commande slash personnalisée pour CE serveur")
    @app_commands.checks.has_permissions(administrator=True)
    async def creer_commande(self, interaction: discord.Interaction,
                              nom: str, reponse: str):
        data = db.load(interaction.guild_id)
        data.setdefault("custom_commands", {})[nom.lower()] = reponse
        db.save(interaction.guild_id, data)
        await interaction.response.send_message(
            f"✅ Commande `/{nom}` créée. (Elle sera disponible via `/info {nom}` ou le système de commandes custom.)",
            ephemeral=True
        )

    # ════════════════════════════════════════════════════════════
    # TICKETMASTER / IDMANIF
    # ════════════════════════════════════════════════════════════

    @app_commands.command(name="idmanif_add", description="Associer un PID Ticketmaster à un événement")
    @app_commands.checks.has_permissions(administrator=True)
    async def idmanif_add(self, interaction: discord.Interaction,
                           evenement: str, pid: str):
        data = db.load(interaction.guild_id)
        data.setdefault("idmanif", {})[evenement] = pid
        db.save(interaction.guild_id, data)
        await interaction.response.send_message(f"✅ PID `{pid}` associé à `{evenement}`.", ephemeral=True)

    @app_commands.command(name="idmanif_list", description="Lister les PID associés")
    @app_commands.checks.has_permissions(administrator=True)
    async def idmanif_list(self, interaction: discord.Interaction):
        idmanif = db.load(interaction.guild_id).get("idmanif", {})
        if not idmanif:
            await interaction.response.send_message("Aucun PID enregistré.", ephemeral=True)
            return
        lines = [f"`{ev}` → `{pid}`" for ev, pid in idmanif.items()]
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @app_commands.command(name="idmanif_remove", description="Supprimer l'association d'un PID")
    @app_commands.checks.has_permissions(administrator=True)
    async def idmanif_remove(self, interaction: discord.Interaction, evenement: str):
        data = db.load(interaction.guild_id)
        data.get("idmanif", {}).pop(evenement, None)
        db.save(interaction.guild_id, data)
        await interaction.response.send_message(f"✅ Association `{evenement}` supprimée.", ephemeral=True)

    @app_commands.command(name="linktmacc", description="(Owner) Lier un compte Ticketmaster à un membre Members+")
    @is_owner()
    async def linktmacc(self, interaction: discord.Interaction,
                         membre: discord.Member, email_tm: str):
        data = db.load(interaction.guild_id)
        data.setdefault("tm_accounts", {})[str(membre.id)] = email_tm
        db.save(interaction.guild_id, data)
        await interaction.response.send_message(
            f"✅ Compte TM `{email_tm}` lié à {membre.mention}.", ephemeral=True
        )

    @app_commands.command(name="mytmacc", description="Voir ton compte Ticketmaster lié (si attribué)")
    async def mytmacc(self, interaction: discord.Interaction):
        acc = db.load(interaction.guild_id).get("tm_accounts", {}).get(str(interaction.user.id))
        if not acc:
            await interaction.response.send_message("❌ Aucun compte TM lié.", ephemeral=True)
            return
        await interaction.response.send_message(f"🎟️ Ton compte Ticketmaster : `{acc}`", ephemeral=True)

    # ════════════════════════════════════════════════════════════
    # WHATSAPP
    # ════════════════════════════════════════════════════════════

    @app_commands.command(name="wa_set_number", description="Définir TON numéro WhatsApp pour recevoir les alertes")
    async def wa_set_number(self, interaction: discord.Interaction, numero: str):
        data = db.load(interaction.guild_id)
        data.setdefault("wa_numbers", {})[str(interaction.user.id)] = numero
        db.save(interaction.guild_id, data)
        await interaction.response.send_message(f"✅ Numéro WA `{numero}` enregistré.", ephemeral=True)

    @app_commands.command(name="wa_my_number", description="Voir TON numéro WhatsApp enregistré")
    async def wa_my_number(self, interaction: discord.Interaction):
        num = db.load(interaction.guild_id).get("wa_numbers", {}).get(str(interaction.user.id))
        if not num:
            await interaction.response.send_message("❌ Aucun numéro WA enregistré.", ephemeral=True)
            return
        await interaction.response.send_message(f"📱 Ton numéro WA : `{num}`", ephemeral=True)

    @app_commands.command(name="wa_subscribe", description="Recevoir les alertes WhatsApp pour les paniers venant de ce salon")
    async def wa_subscribe(self, interaction: discord.Interaction):
        data = db.load(interaction.guild_id)
        subs = data.setdefault("wa_subs", {}).setdefault(str(interaction.channel_id), [])
        uid = interaction.user.id
        if uid in subs:
            subs.remove(uid)
            db.save(interaction.guild_id, data)
            await interaction.response.send_message("❌ Désabonné des alertes WA pour ce salon.", ephemeral=True)
        else:
            subs.append(uid)
            db.save(interaction.guild_id, data)
            await interaction.response.send_message("✅ Abonné aux alertes WA pour ce salon.", ephemeral=True)

    @app_commands.command(name="wa_list", description="Lister tes salons WhatsApp abonnés")
    async def wa_list(self, interaction: discord.Interaction):
        subs = db.load(interaction.guild_id).get("wa_subs", {})
        my_subs = [ch_id for ch_id, uids in subs.items() if interaction.user.id in uids]
        if not my_subs:
            await interaction.response.send_message("Aucun abonnement WA.", ephemeral=True)
            return
        lines = [f"<#{ch_id}>" for ch_id in my_subs]
        await interaction.response.send_message("📱 Tes abonnements WA :\n" + "\n".join(lines), ephemeral=True)

async def setup(bot):
    await bot.add_cog(Advanced(bot))
