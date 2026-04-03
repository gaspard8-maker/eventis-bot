# 🤖 Eventis Bot – Clone

Bot Discord recréé à partir des commandes du Eventis Bot original.

## 📁 Structure

```
fluyn_bot/
├── bot.py              ← Fichier principal (lance le bot)
├── db.py               ← Stockage JSON local
├── requirements.txt
├── data/               ← Créé automatiquement (sauvegarde JSON)
└── cogs/
    ├── moderation.py   ← /ban /kick /mute /warn /unwarn /warnings /clear
    ├── tickets.py      ← /ticketpanel_setup /close-ticket /access-ticket etc.
    ├── roles.py        ← /setup_roles /add_role_button /reset_roles etc.
    ├── utility.py      ← /embed /dump_embed /giveaway_start /welcome_setup /list /gcpsg
    ├── licences.py     ← /activer_licence /key_create /key_disable /key_enable etc.
    ├── cb_infos.py     ← /register /myinfos /edit_infos /admin_infos /quota_* etc.
    └── advanced.py     ← /webhook /info_create /creer_commande /idmanif_* /wa_* etc.
```

## 🚀 Installation

### 1. Prérequis
- Python 3.10+
- Un bot Discord créé sur https://discord.com/developers/applications

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3. Configurer le bot

Dans **bot.py**, remplace :
```python
BOT_TOKEN = "VOTRE_TOKEN_ICI"
OWNER_ID   = 0  # ← ton Discord user ID
```

Dans **cogs/licences.py** et **cogs/cb_infos.py** et **cogs/advanced.py**, remplace :
```python
OWNER_ID = 0  # ← ton Discord user ID
```

### 4. Activer les Intents sur Discord Developer Portal
- Va sur https://discord.com/developers/applications
- Sélectionne ton bot → Bot → Active **Server Members Intent** et **Message Content Intent**

### 5. Lancer le bot
```bash
python bot.py
```

## 📋 Liste complète des commandes

### Modération
| Commande | Description |
|----------|-------------|
| `/ban` | Bannir un membre avec raison |
| `/kick` | Kick un membre avec raison |
| `/mute` | Mute (timeout) un membre en minutes |
| `/warn` | Avertir un membre |
| `/unwarn` | Supprimer un warning |
| `/warnings` | Voir les warnings d'un membre |
| `/clear` | Supprimer des messages |

### Tickets
| Commande | Description |
|----------|-------------|
| `/ticketpanel_setup` | Créer le panel de tickets |
| `/close-ticket` | Fermer le ticket en cours |
| `/access-ticket` | Définir le rôle d'accès tickets |
| `/set_close_role` | Rôle autorisé à fermer |
| `/set_staff_role` | Rôle staff des tickets |
| `/set_ticket_category` | Catégorie des tickets |
| `/renameautoticket` | Toggle renommage auto |

### Rôles
| Commande | Description |
|----------|-------------|
| `/setup_roles` | Panel de sélection de rôles |
| `/add_role_button` | Ajouter un bouton de rôle |
| `/remove_role_button` | Supprimer un bouton de rôle |
| `/reset_roles` | Réinitialiser les rôles |
| `/good_perm_role` | Rôle bouton Good |

### Utilitaires
| Commande | Description |
|----------|-------------|
| `/embed` | Créer un embed |
| `/dump_embed` | Exporter embed en JSON |
| `/giveaway_start` | Lancer un giveaway |
| `/welcome_setup` | Config message de bienvenue |
| `/list` | Lister les channels |
| `/gcpsg` | Lien cartes cadeaux PSG |

### Licences (Owner)
| Commande | Description |
|----------|-------------|
| `/activer_licence` | Activer la licence serveur |
| `/key_create` | Créer une clé licence |
| `/key_disable` | Désactiver une clé |
| `/key_enable` | Réactiver une clé |
| `/key_info` | Infos d'une clé |
| `/reset_hwid` | Reset HWID |
| `/script_add_license` | Licence script |
| `/script_license_info` | Info licence script |
| `/script_remove_license` | Supprimer licence script |
| `/script_toggle_license` | Toggle licence script |

### CB / Infos
| Commande | Description |
|----------|-------------|
| `/register` | Enregistrer infos CB |
| `/register_plus` | Infos CB étendues |
| `/myinfos` | Voir mes infos |
| `/myinfos_plus` | Voir mes infos (étendu) |
| `/edit_infos` | Modifier mes infos |
| `/edit_infos_plus` | Modifier mes infos (étendu) |
| `/admin_infos` | Voir infos d'un membre (Owner) |
| `/admin_infos_plus` | Idem étendu |
| `/quota_toggle` | Activer/désactiver quotas |
| `/quota_add` | Ajouter des quotas |
| `/quota_show` | Mon solde quotas |
| `/quota_list` | Tous les quotas |
| `/quota_perm_role` | Rôle gestion quotas |
| `/carts_analytics` | Stats paniers 7j |
| `/warning_message` | Toggle message avertissement |

### Avancé
| Commande | Description |
|----------|-------------|
| `/webhook` | Relayer un salon |
| `/webhook_stop` | Arrêter un relais |
| `/set_webhook_role` | Rôle webhook |
| `/webhook_pasfixed` | PAS fixé |
| `/webhook_pasmap` | PAS map |
| `/webhook_pasreset` | Reset PAS |
| `/pas_list` | Lister les PAS |
| `/info_create` | Créer une info |
| `/info_delete` | Supprimer une info |
| `/info` | Envoyer une info |
| `/creer_commande` | Commande slash custom |
| `/idmanif_add` | Associer PID TM |
| `/idmanif_list` | Lister PID |
| `/idmanif_remove` | Supprimer PID |
| `/linktmacc` | Lier compte TM (Owner) |
| `/mytmacc` | Mon compte TM |
| `/wa_set_number` | Mon numéro WA |
| `/wa_my_number` | Voir mon numéro WA |
| `/wa_subscribe` | S'abonner alertes WA |
| `/wa_list` | Mes abonnements WA |
