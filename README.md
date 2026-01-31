# Surveillance créneaux ClicRDV + Discord

Ce projet interroge l’**API ClicRDV** pour détecter les créneaux disponibles et envoie des notifications sur **Discord** dès qu’un nouveau créneau apparaît.

Aucun scraping : uniquement des appels HTTP à l’API `availabletimeslots`.

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

### 1. Bot Discord

1. [Discord Developer Portal](https://discord.com/developers/applications) → nouvelle application → onglet **Bot** → créer un bot, copier le token.
2. Activer **Message Content Intent** si besoin.
3. Inviter le bot sur ton serveur (permissions : envoyer des messages, voir les messages).
4. Activer le mode développeur Discord, clic droit sur le canal → **Copier l’ID** → c’est `DISCORD_CHANNEL_ID`.

### 2. Fichier `.env`

Créer un fichier `.env` à la racine du projet :

```env
# Obligatoire : URL de l’API ClicRDV availabletimeslots
CLICRDV_API_URL=https://www.clicrdv.com/api/v2/availabletimeslots?group_id=124718&promotions=0&time_format=datetime&appointments[0][intervention_id]=2422111&from=2026-02-12&apikey=VOTRE_CLE

# Optionnel : lien affiché dans les messages Discord (page de résa)
BOOKING_URL=https://user.clicrdv.com/consulat-general-du-portugal-a-paris

# Obligatoire
DISCORD_TOKEN=votre_token_bot
DISCORD_CHANNEL_ID=123456789012345678

# Optionnel (défaut: 60)
CHECK_INTERVAL=60

# Optionnel : si l’URL contient {date}, nombre de jours à scanner (défaut: 30)
CLICRDV_DAYS_AHEAD=35

# Sur Railway : RUN_ONCE=1 pour une vérif puis exit (cron = économie de crédits)
# RUN_ONCE=1
```

- **Sans `{date}`** dans l’URL : une seule requête par vérification (date fixe dans l’URL).
- **Avec `{date}`** dans l’URL (ex. `&from={date}&`) : le script teste plusieurs dates (du jour J à J+`CLICRDV_DAYS_AHEAD`).

## Utilisation

```bash
python main.py
```

- Au premier lancement : chargement des créneaux actuels, **aucune notification**.
- Ensuite : à chaque cycle, seuls les **nouveaux** créneaux déclenchent une notification Discord.

Test rapide des créneaux (sans Discord) :

```bash
python api_client.py
```

Arrêt : `Ctrl+C`.

## Déploiement sur Railway (sans flamber les crédits)

Une boucle `while` qui tourne en continu consomme des crédits 24/7. Sur Railway, utilise le **mode une exécution puis exit** + un **cron** :

1. **Variables d’environnement** Railway : ajoute `RUN_ONCE=1` (et toutes les autres : `CLICRDV_API_URL`, `DISCORD_TOKEN`, `DISCORD_CHANNEL_ID`, etc.).
2. **Cron Railway** : crée un Cron Job qui exécute `python main.py` par exemple **toutes les 5 minutes** (ou 10 min).
3. À chaque run : le script fait une vérification (API 5 semaines + Discord si nouveaux créneaux), puis **quitte**. Pas de boucle infinie = tu ne paies que le temps d’exécution (~1–2 min toutes les 5 min).

Sans `RUN_ONCE=1`, le process tourne en boucle et consomme des crédits en continu.

## Dépannage

- **"CLICRDV_API_URL doit être défini"** : vérifier que `.env` existe et contient `CLICRDV_API_URL`.
- **Pas de notifications** : vérifier `DISCORD_TOKEN`, `DISCORD_CHANNEL_ID` et les permissions du bot.
- **Aucun créneau** : l’API renvoie peut‑être une liste vide ; vérifier l’URL (group_id, intervention_id, apikey, date).
