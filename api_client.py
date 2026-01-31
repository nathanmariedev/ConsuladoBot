"""
Client API ClicRDV : surveillance des créneaux disponibles via l'API availabletimeslots.
"""
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

import requests
import logging
from typing import List, Dict

script_dir = Path(__file__).parent.absolute()
env_path = script_dir / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)
else:
    load_dotenv(override=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ClicRDVClient:
    """Client pour l'API ClicRDV availabletimeslots."""

    def __init__(self, api_url: str = None, days_ahead: int = None):
        self.api_url = (api_url or os.getenv("CLICRDV_API_URL", "")).strip()
        # Défaut 35 jours = 5 semaines à chaque exécution
        self.days_ahead = days_ahead if days_ahead is not None else int(os.getenv("CLICRDV_DAYS_AHEAD", "35"))
        self._previous_slot_ids = set()
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            }
        )

    def fetch_slots(self) -> List[Dict]:
        """
        Appelle l'API ClicRDV et retourne la liste des créneaux disponibles.
        Si l'URL contient {date}, interroge plusieurs dates (du jour à +days_ahead).
        """
        if not self.api_url:
            return []

        slots = []
        if "{date}" in self.api_url:
            today = datetime.now().date()
            logger.info("Interrogation API sur %d jours (du %s au %s)", self.days_ahead, today, today + timedelta(days=self.days_ahead - 1))
            for d in range(self.days_ahead):
                date_str = (today + timedelta(days=d)).strftime("%Y-%m-%d")
                url = self.api_url.replace("{date}", date_str)
                try:
                    r = self._session.get(url, timeout=15)
                    r.raise_for_status()
                    data = r.json()
                except (requests.RequestException, json.JSONDecodeError) as e:
                    logger.debug("API %s: %s", date_str, e)
                    continue
                for slot in data.get("availabletimeslots", []):
                    slots.append(self._slot_to_appointment(slot))
        else:
            try:
                r = self._session.get(self.api_url, timeout=15)
                r.raise_for_status()
                data = r.json()
            except (requests.RequestException, json.JSONDecodeError) as e:
                logger.error("Erreur API ClicRDV: %s", e)
                return []
            for slot in data.get("availabletimeslots", []):
                slots.append(self._slot_to_appointment(slot))

        return slots

    def _slot_to_appointment(self, slot: dict) -> Dict:
        start = slot.get("start", "")
        slot_id = slot.get("slot") or start
        return {
            "text": f"ClicRDV – {start}",
            "start": start,
            "slot_id": slot_id,
            "capacity": slot.get("capacity"),
            "timestamp": datetime.now().isoformat(),
        }

    def check_new_slots(self) -> List[Dict]:
        """
        Récupère les créneaux actuels et retourne uniquement les nouveaux
        (absents au dernier appel). Au premier appel, initialise la base sans notifier.
        """
        current = self.fetch_slots()
        current_ids = {apt.get("slot_id", apt["text"]) for apt in current}

        if not self._previous_slot_ids:
            self._previous_slot_ids = current_ids
            logger.info("Premier appel API : %d créneau(x) en base, pas de notification", len(current_ids))
            return []

        new_slots = [apt for apt in current if apt.get("slot_id", apt["text"]) not in self._previous_slot_ids]
        self._previous_slot_ids = current_ids
        return new_slots

    def run_once(self) -> List[Dict]:
        """Une vérification : retourne la liste des nouveaux créneaux détectés."""
        logger.info("Vérification des créneaux via API ClicRDV")
        new_slots = self.check_new_slots()
        if new_slots:
            logger.info("%d nouveau(x) créneau(x) détecté(s)", len(new_slots))
        else:
            logger.info("Aucun nouveau créneau")
        return new_slots


def main():
    """Test : affiche les créneaux disponibles."""
    client = ClicRDVClient()
    if not client.api_url:
        print("Définir CLICRDV_API_URL dans le fichier .env")
        return
    slots = client.fetch_slots()
    print(f"{len(slots)} créneau(x) disponible(s)")
    for s in slots:
        print(" ", s.get("start", s.get("text")))


if __name__ == "__main__":
    main()
