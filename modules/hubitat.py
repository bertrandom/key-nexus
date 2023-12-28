import aiohttp


class Hubitat:
    def __init__(self, config, session):
        self.config = config
        self.session = session

        self.host = self.config["hubitat"]["host"]
        self.access_token = self.config["hubitat"]["access_token"]

    async def toggleBedroomLights(self):
        async with self.session.get(f"http://{self.host}/apps/api/88/devices/36?access_token={self.access_token}") as resp:
            response = await resp.json()

            levelAttribute = None
            for attribute in response["attributes"]:
                if attribute['name'] == 'level':
                    levelAttribute = attribute

            switchAttribute = None
            for attribute in response["attributes"]:
                if attribute['name'] == 'switch':
                    switchAttribute = attribute

            if switchAttribute['currentValue'] == 'off':
                await self.session.get(f"http://{self.host}/apps/api/88/devices/36/setLevel/25?access_token={self.access_token}")
            else:
                if levelAttribute['currentValue'] == 25:
                    await self.session.get(f"http://{self.host}/apps/api/88/devices/36/setLevel/100?access_token={self.access_token}")
                else:
                    await self.session.get(f"http://{self.host}/apps/api/88/devices/36/off?access_token={self.access_token}")
