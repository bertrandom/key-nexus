import logging

import aiohttp

logger = logging.getLogger(__name__)

class ElectricObjects:
    def __init__(self, config, session):
        self.config = config
        self.session = session

    async def resume(self, **kwargs):
        frame = kwargs["frame"]
        url = f"http://{frame}.smittn.com:12345/resume"
        await self.session.get(url)
