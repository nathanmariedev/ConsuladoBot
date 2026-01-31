import discord
import logging
from typing import List, Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AppointmentNotifier:
    
    def __init__(self, token: str, channel_id: int):
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        self.token = token
        self.channel_id = channel_id
        self.channel = None
        
        @self.client.event
        async def on_ready():
            logger.info(f'Bot connecté en tant que {self.client.user}')
            self.channel = self.client.get_channel(self.channel_id)
            if not self.channel:
                logger.error(f"Canal avec l'ID {channel_id} introuvable")
            else:
                logger.info(f"Canal configuré: {self.channel.name}")
    
    async def send_notification(self, appointments: List[Dict], url: str):
        if not self.channel:
            logger.error("Canal Discord non configuré")
            return
        
        if not appointments:
            return

        for appointment in appointments:
            start = appointment.get('start', '') or appointment.get('text', 'Créneau disponible')
            embed = discord.Embed(
                title="🎯 Nouveau créneau ClicRDV",
                description=f"**{start}**",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Réserver", value=f"[Ouvrir la page de réservation]({url})", inline=False)
            embed.set_footer(text="Surveillance API – 5 semaines")
            
            try:
                await self.channel.send(embed=embed)
                logger.info("Notification Discord envoyée: %s", start)
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de la notification: {e}")
    
    async def send_startup_message(self, url: str, check_interval: int, api_mode: bool = False):
        if not self.channel:
            return
        
        title = "🤖 Surveillance créneaux démarrée"
        desc = f"API ClicRDV – Lien réservation: {url}" if api_mode else f"Surveillance: {url}"
        embed = discord.Embed(
            title=title,
            description=desc,
            color=discord.Color.blue()
        )
        embed.add_field(name="Intervalle de vérification", value=f"{check_interval} secondes", inline=False)
        
        try:
            await self.channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message de démarrage: {e}")
    
    async def start(self):
        try:
            await self.client.start(self.token)
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du bot: {e}")
            raise
    
    async def close(self):
        await self.client.close()
