import base64
import datetime
import logging

from sqlite_utils.db import NotFoundError

logger = logging.getLogger(__name__)

class Sonos:
    def __init__(self, config, session, db):
        self.config = config
        self.session = session
        self.db = db

        db["sonos_access_tokens"].create({
            "id": int,
            "token": str,
            "expires_at": datetime.datetime 
        }, pk="id", if_not_exists=True)

        table = db["sonos_access_tokens"]
        self.table = table

    async def getAccessToken(self):
        try:
            row = self.table.get(1)
        except NotFoundError:
            row = None

        if row is not None and datetime.datetime.fromisoformat(row["expires_at"]) > datetime.datetime.now(datetime.UTC):
            return row["token"]

        sonos_access_token = await self.refreshAccessToken()
        if sonos_access_token is None:
            return
        self.table.upsert(sonos_access_token, pk="id")
        return sonos_access_token["token"]

    def getAuthorizationHeader(self):
        client_string = f"{self.config['sonos']['client_id']}:{self.config['sonos']['client_secret']}"
        client_bytes = client_string.encode('utf-8')
        client_base64_bytes = base64.b64encode(client_bytes)
        client_base64_string = client_base64_bytes.decode('utf-8')
        return f"Basic {client_base64_string}"

    async def refreshAccessToken(self):
        async with self.session.post("https://api.sonos.com/login/v3/oauth/access", headers={
            "Authorization": self.getAuthorizationHeader()
        }, data={
            "grant_type": "refresh_token",
            "refresh_token": self.config["sonos"]["refresh_token"]
        }) as resp:
            response = await resp.json()
            if "error" in response:
                logger.error(response)
                return

            access_token = response["access_token"]
            expires_in = response["expires_in"]
            expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=expires_in)

            return {
                "id": 1,
                "token": access_token,
                "expires_at": expires_at
            }