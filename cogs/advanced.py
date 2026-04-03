import discord
from discord import app_commands
from discord.ext import commands
import db
import asyncio
import re

OWNER_ID = 0  # ← Remplace par ton Discord user ID

def is_owner():
    async def pred(interaction: discord.Interaction) -> bool:
        if interaction.user.id != OWNER_ID and not interaction.user.guild_permissions.administrator:
            raise app_commands.CheckFailure("Commande réservée au Owner.")
        return True
    return app_commands.check(pred)


class GoodView(discord.ui.View):
    def __init__(self, clicker_id: int, clicker_name: str, checkout_url: str = None):
        super().__init__(timeout=None)
        self.clicker_id = clicker_id
        self.clicker_name = clicker_name
        if checkout_url:
            self.add_item(discord.ui.Button(
                label="💳 Ouvrir le lien de paiement",
                style=discord.ButtonStyle.link,
                url=checkout_url,
                row=1
            ))

    @discord.ui.button(label="✅ Good", style=discord.ButtonStyle.success, custom_id="good_btn", row=0)
    async def good(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = db.load(interaction.guild_id)
        good_role_id = data.get("good_perm_role")
        if good_role_id:
            role = interaction.guild.get_role(good_role_id)
            if role and role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("❌ Tu n'as pas la permission d'utiliser Good.", ephemeral=True)
                return
        new_name = f"good-{self.clicker_name.lower().replace(' ', '-')[:20]}"
        await interaction.channel.edit(name=f"✅・{new_name}")
        button.disabled = True
        button.label = "✅ Good validé"
        await interaction.message.edit(view=self)
        embed = discord.Embed(
            description=f"✅ Panier validé par {interaction.user.mention} pour <@{self.clicker_id}> !",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)


class BuyCartView(discord.ui.View):
    def __init__(self, embed_data: dict, checkout_url: str = None, source_channel_id: int = None):
        super().__init__(timeout=None)
        self.embed_data = embed_data
        self.checkout_url = checkout_url
        self.source_channel_id = source_channel_id

    @discord.ui.button(label="🛒 Buy Cart", style=discord.ButtonStyle.success, custom_id="buy_cart_btn")
    async def buy_cart(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        data = db.load(guild.id)

        access_role_id = data.get("ticket_access_role")
        if access_role_id:
            role = guild.get_role(access_role_id)
            if role and role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("❌ Tu n'as pas le rôle requis pour claim ce panier.", ephemeral=True)
                return

        category_id = data.get("ticket_category")
        category = guild.get_channel(category_id) if category_id else None
        ticket_name = interaction.user.display_name.lower().replace(' ', '-')[:20]

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        staff_role_id = data.get("staff_role")
        if staff_role_id:
            staff_role = guild.get_role(staff_role_id)
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"ticket-{ticket_name}",
            category=category,
            overwrites=overwrites
        )

        original_embed = discord.Embed.from_dict(self.embed_data) if self.embed_data else None
        staff_mention = f"<@&{staff_role_id}>" if staff_role_id else ""
        cb_infos = data.get("cb_users", {}).get(str(interaction.user.id))

        welcome_embed = discord.Embed(color=discord.Color.green())
        welcome_embed.description = f"🎉 {interaction.user.mention} a réservé ce panier !\n{staff_mention} merci de finaliser."

        if cb_infos:
            show_public = data.get("webhook_options", {}).get(str(self.source_channel_id or 0), {}).get("show_public_info", False)
            if show_public:
                cb_text = "\n".join(f"**{k.capitalize()}** : {v}" for k, v in cb_infos.items() if v)
                welcome_embed.add_field(name="🔒 Infos CB", value=cb_text, inline=False)
            else:
                welcome_embed.add_field(name="🔒 Infos CB", value="Infos CB disponibles — utilise `/myinfos` pour les voir.", inline=False)
        else:
            welcome_embed.add_field(name="⚠️ Infos CB", value="Aucune info CB enregistrée. Utilise `/register`.", inline=False)

        good_view = GoodView(
            clicker_id=interaction.user.id,
            clicker_name=interaction.user.display_name,
            checkout_url=self.checkout_url
        )

        if original_embed:
            await channel.send(content=f"🎉 {interaction.user.mention} a réservé ce panier !\n{staff_mention}", embed=original_embed)
        await channel.send(embed=welcome_embed, view=good_view)

        button.disabled = True
        button.label = f"✅ Claimed — {interaction.user.display_name}"
        button.style = discord.ButtonStyle.secondary
        await interaction.message.edit(view=self)

        await interaction.response.send_message(f"✅ Ticket créé : {channel.mention}", ephemeral=True)


class Advanced(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
        await interaction.response.send_message(f"✅ Relais : {source.mention} → {dests_mentions}", ephemeral=True)

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
        if not message.guild:
            return
        data = db.load(message.guild.id)
        relays = data.get("webhook_relays", {})
        dest_ids = relays.get(str(message.channel.id), [])
        if not dest_ids:
            return

        options = data.get("webhook_options", {}).get(str(message.channel.id), {})
        mention_role_id = options.get("mention_role")
        include_payment_link = options.get("include_payment_link", False)
        expire_minutes = options.get("expire_minutes", 0)

        embed_to_relay = message.embeds[0] if message.embeds else None

        checkout_url = None
        if embed_to_relay and include_payment_link:
            for field in embed_to_relay.fields:
                if any(k in field.name.lower() for k in ["checkout", "url", "lien", "payment", "link"]):
                    urls = re.findall(r'https?://\S+', field.value)
                    if urls:
                        checkout_url = urls[0]
                        break
            if not checkout_url and embed_to_relay.description:
                urls = re.findall(r'https?://\S+', embed_to_relay.description)
                if urls:
                    checkout_url = urls[0]

        for dest_id in dest_ids:
            dest = message.guild.get_channel(dest_id)
            if not dest:
                continue

            mention_text = f"<@&{mention_role_id}>" if mention_role_id else None

            view = BuyCartView(
                embed_data=embed_to_relay.to_dict() if embed_to_relay else {},
                checkout_url=checkout_url,
                source_channel_id=message.channel.id
            )

            if embed_to_relay:
                await dest.send(content=mention_text, embed=embed_to_relay, view=view)
            else:
                embed = discord.Embed(description=message.content, color=discord.Color.greyple())
                embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
                await dest.send(content=mention_text, embed=embed, view=view)

            if expire_minutes > 0:
                async def expire_later(ch=dest, mins=expire_minutes):
                    await asyncio.sleep(mins * 60)
                    try:
                        await ch.send(embed=discord.Embed(
                            description=f"⏰ Ce panier a expiré après {mins} minutes.",
                            color=discord.Color.red()
                        ))
                    except Exception:
                        pass
                self.bot.loop.create_task(expire_later())

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

    @app_commands.command(name="creer_commande", description="Crée ou modifie une commande slash personnalisée pour CE serveur")
    @app_commands.checks.has_permissions(administrator=True)
    async def creer_commande(self, interaction: discord.Interaction, nom: str, reponse: str):
        data = db.load(interaction.guild_id)
        data.setdefault("custom_commands", {})[nom.lower()] = reponse
        db.save(interaction.guild_id, data)
        await interaction.response.send_message(f"✅ Commande `/{nom}` créée.", ephemeral=True)

    @app_commands.command(name="idmanif_add", description="Associer un PID Ticketmaster à un événement")
    @app_commands.checks.has_permissions(administrator=True)
    async def idmanif_add(self, interaction: discord.Interaction, evenement: str, pid: str):
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
    async def linktmacc(self, interaction: discord.Interaction, membre: discord.Member, email_tm: str):
        data = db.load(interaction.guild_id)
        data.setdefault("tm_accounts", {})[str(membre.id)] = email_tm
        db.save(interaction.guild_id, data)
        await interaction.response.send_message(f"✅ Compte TM `{email_tm}` lié à {membre.mention}.", ephemeral=True)

    @app_commands.command(name="mytmacc", description="Voir ton compte Ticketmaster lié (si attribué)")
    async def mytmacc(self, interaction: discord.Interaction):
        acc = db.load(interaction.guild_id).get("tm_accounts", {}).get(str(interaction.user.id))
        if not acc:
            await interaction.response.send_message("❌ Aucun compte TM lié.", ephemeral=True)
            return
        await interaction.response.send_message(f"🎟️ Ton compte Ticketmaster : `{acc}`", ephemeral=True)

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
