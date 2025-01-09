import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)


class RemiAPI:
    BASE_URL = "https://remi2.urbanhello.com/parse"

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session_token = None
        self.remis = []
        self.cache = {}  # Stocke les données pour chaque Remi
        self.cache_expiry = {}  # Stocke l'heure d'expiration du cache
        self.cache_duration = 60  # Durée de vie du cache en secondes
        self.faces = {}  # Stocke les faces disponibles par nom

    async def login(self):
        """Authenticate with the Rémi API and retrieve available devices."""
        url = f"{self.BASE_URL}/login"
        payload = {"username": self.username, "password": self.password}
        headers = {
            "x-parse-application-id": "jf1a0bADt5fq",
            "content-type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"Login failed: {response.status}")
                data = await response.json()
                self.session_token = data["sessionToken"]
                self.remis = data.get("remis", [])
                _LOGGER.debug("Login successful, devices available: %s", self.remis)
                # Récupérer les faces après le login
                await self.get_faces()
                return data

    async def get_faces(self):
        """Retrieve available faces and their objectId."""
        url = f"{self.BASE_URL}/classes/Face"
        headers = {
            "x-parse-session-token": self.session_token,
            "x-parse-application-id": "jf1a0bADt5fq",
            "content-type": "application/json",
        }
        payload = {"order": "index", "_method": "GET"}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"Failed to retrieve faces: {response.status}")
                data = await response.json()

                # Stocker les faces par nom pour un accès rapide
                self.faces = {face["name"]: face["objectId"] for face in data.get("results", [])}
                return self.faces

    async def get_remi_info(self, object_id):
        """Retrieve all information for a specific Rémi device."""
        url = f"{self.BASE_URL}/classes/Remi/{object_id}"
        headers = {
            "x-parse-session-token": self.session_token,
            "x-parse-application-id": "jf1a0bADt5fq",
            "content-type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"Failed to retrieve Remi info: {response.status}")
                data = await response.json()
                return {
                    "temperature": data.get("temp", 0) + 40,
                    "luminosity": data.get("luminosity", 0),
                    "face": data.get("face", {}).get("objectId"),
                    "name": data.get("name"),
                }

    async def set_brightness(self, object_id, brightness):
        """Set the brightness of a specific Rémi device."""
        url = f"{self.BASE_URL}/classes/Remi/{object_id}"
        headers = {
            "x-parse-session-token": self.session_token,
            "x-parse-application-id": "jf1a0bADt5fq",
            "content-type": "application/json",
        }
        payload = {"luminosity": brightness}

        async with aiohttp.ClientSession() as session:
            async with session.put(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"Failed to set brightness: {response.status}")
                return await response.json()

    async def turn_on(self, object_id):
        """Turn on the light using the sleepyFace."""
        face_id = self.faces.get("sleepyFace")
        if not face_id:
            raise Exception("sleepyFace not found")

        url = f"{self.BASE_URL}/classes/Remi/{object_id}"
        headers = {
            "x-parse-session-token": self.session_token,
            "x-parse-application-id": "jf1a0bADt5fq",
            "content-type": "application/json",
        }
        payload = {"face": {"__type": "Pointer", "className": "Face", "objectId": face_id}}

        async with aiohttp.ClientSession() as session:
            async with session.put(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"Failed to turn on: {response.status}")
                return await response.json()

    async def turn_off(self, object_id):
        """Turn off the light using the awakeFace."""
        face_id = self.faces.get("awakeFace")
        if not face_id:
            raise Exception("awakeFace not found")

        url = f"{self.BASE_URL}/classes/Remi/{object_id}"
        headers = {
            "x-parse-session-token": self.session_token,
            "x-parse-application-id": "jf1a0bADt5fq",
            "content-type": "application/json",
        }
        payload = {"face": {"__type": "Pointer", "className": "Face", "objectId": face_id}}

        async with aiohttp.ClientSession() as session:
            async with session.put(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"Failed to turn off: {response.status}")
                return await response.json()