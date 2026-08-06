import logging

import aiohttp

logger = logging.getLogger(__name__)

class GenericHttp:
    def __init__(self, config, session):
        self.config = config
        self.session = session

    async def get(self, **kwargs):
        url = kwargs["url"]
        await self.session.get(url)

    async def post(self, **kwargs):
        url = kwargs["url"]
        if "payload" not in kwargs:
            payload = {}
        else:
            payload = kwargs["payload"]
        await self.session.post(url, json=payload)
