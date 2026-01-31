"""
Surveillance des créneaux ClicRDV via l'API et notifications Discord.
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path

from dotenv import load_dotenv
import os

from api_client import ClicRDVClient
from discord_bot import AppointmentNotifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

script_dir = Path(__file__).parent.absolute()
env_path = script_dir / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)
else:
    load_dotenv(override=True)


class SlotMonitor:
    """Surveillance API ClicRDV + notifications Discord."""

    def __init__(self):
        self.api_url = os.getenv("CLICRDV_API_URL", "").strip()
        self.booking_url = os.getenv("BOOKING_URL", "").strip() or "https://user.clicrdv.com"
        self.discord_token = os.getenv("DISCORD_TOKEN", "").strip()
        discord_channel_id_str = os.getenv("DISCORD_CHANNEL_ID", "0").strip()
        self.check_interval = int(os.getenv("CHECK_INTERVAL", "60"))

        errors = []

        if not self.api_url:
            errors.append("CLICRDV_API_URL doit être défini dans le fichier .env")
        if not self.discord_token:
            errors.append("DISCORD_TOKEN doit être défini dans le fichier .env")
        try:
            self.discord_channel_id = int(discord_channel_id_str)
            if self.discord_channel_id == 0:
                errors.append("DISCORD_CHANNEL_ID doit être défini dans le fichier .env")
        except ValueError:
            errors.append(f"DISCORD_CHANNEL_ID invalide: '{discord_channel_id_str}'")
            self.discord_channel_id = 0

        if errors:
            logger.error("=" * 60)
            logger.error("ERREURS DE CONFIGURATION:")
            for err in errors:
                logger.error("  - %s", err)
            logger.error("=" * 60)
            raise ValueError("\n".join(errors))

        logger.info("Configuration chargée:")
        logger.info("  CLICRDV_API_URL: %s...", self.api_url[:50] if len(self.api_url) > 50 else self.api_url)
        logger.info("  BOOKING_URL: %s", self.booking_url)
        logger.info("  DISCORD_CHANNEL_ID: %s", self.discord_channel_id)
        logger.info("  CHECK_INTERVAL: %s secondes", self.check_interval)

        self.client = ClicRDVClient()
        self.notifier = AppointmentNotifier(self.discord_token, self.discord_channel_id)
        self.running = True
        # RUN_ONCE=1 : une vérification puis exit (pour Railway cron → pas de boucle = crédits économisés)
        self.run_once_mode = os.getenv("RUN_ONCE", "").strip().lower() in ("1", "true", "yes")

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        logger.info("Arrêt demandé...")
        self.running = False

    async def run(self):
        bot_task = asyncio.create_task(self.notifier.start())
        await asyncio.sleep(2)

        if not self.run_once_mode:
            await self.notifier.send_startup_message(
                self.booking_url,
                self.check_interval,
                api_mode=True,
            )
            logger.info("Surveillance API démarrée. Ctrl+C pour arrêter.")
        else:
            logger.info("Mode RUN_ONCE : une vérification puis exit (idéal Railway cron).")

        try:
            while self.running:
                new_slots = self.client.run_once()
                if new_slots:
                    logger.info("%d nouveau(x) créneau(x) → notification Discord", len(new_slots))
                    await self.notifier.send_notification(new_slots, self.booking_url)
                if self.run_once_mode:
                    break
                await asyncio.sleep(self.check_interval)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            logger.error("Erreur: %s", e)
        finally:
            logger.info("Arrêt du moniteur...")
            await self.notifier.close()
            bot_task.cancel()
            try:
                await bot_task
            except asyncio.CancelledError:
                pass


async def main():
    try:
        monitor = SlotMonitor()
        await monitor.run()
    except ValueError as e:
        logger.error("Configuration: %s", e)
        sys.exit(1)
    except Exception as e:
        logger.error("Erreur fatale: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
