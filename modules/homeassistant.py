import logging

import aiohttp

logger = logging.getLogger(__name__)

class HomeAssistant:
    def __init__(self, config, session):
        self.config = config
        self.session = session

        self.host = self.config["homeassistant"]["host"]
        self.port = self.config["homeassistant"]["port"]

        self.api_key = self.config["homeassistant"]["api_key"]

    async def triggerWebhook(self, webhook_name):
        if self.config["homeassistant"]["webhooks"][webhook_name] is None:
            return

        webhook_id = self.config["homeassistant"]["webhooks"][webhook_name]
        url = f"http://{self.host}:{self.port}/api/webhook/{webhook_id}"
        result = await self.session.post(url)
        logger.info(result)

    async def toggleEgyptLight(self):
        await self.triggerWebhook("toggle_egypt_light")

    async def turnOnAurorasNightLight(self):
        await self.triggerWebhook("turn_on_auroras_night_light_for_30_min")

    async def toggleGarageDoor(self):
        await self.triggerWebhook("toggle_garage_door")

    async def openGarageDoor(self):
        await self.triggerWebhook("open_garage_door")

    async def closeGarageDoor(self):
        await self.triggerWebhook("close_garage_door")

    async def toggleNixie(self):
        url = f"http://{self.host}:{self.port}/api/services/switch/toggle"
        await self.session.post(f"http://{self.host}:{self.port}/api/services/switch/toggle", json={
            "entity_id": "switch.nixie_bulb_skinny_2"
        }, headers={
            "Authorization": f"Bearer {self.api_key}"
        })