import base64
import datetime
import logging

from sqlite_utils.db import NotFoundError

logger = logging.getLogger(__name__)

class Sonos:

    urls = {
        "audioClip": {
            "loadAudioClip": 'https://api.ws.sonos.com/control/api/v1/players/{playerId}/audioClip',
        },
        "groups": {
            "getGroups": 'https://api.ws.sonos.com/control/api/v1/households/{householdId}/groups',
        },
        "playback": {
            "togglePlayPause": 'https://api.ws.sonos.com/control/api/v1/groups/{groupId}/playback/togglePlayPause',
            "skipToPreviousTrack": "https://api.ws.sonos.com/control/api/v1/groups/{groupId}/playback/skipToPreviousTrack",
            "skipToNextTrack": "https://api.ws.sonos.com/control/api/v1/groups/{groupId}/playback/skipToNextTrack",
            "lineIn": 'https://api.ws.sonos.com/control/api/v1/groups/{groupId}/playback/lineIn',
            "play": 'https://api.ws.sonos.com/control/api/v1/groups/{groupId}/playback/play',
        },
        "playerVolume": {
            "getVolume": 'https://api.ws.sonos.com/control/api/v1/players/{playerId}/playerVolume',
            "setMute": 'https://api.ws.sonos.com/control/api/v1/players/{playerId}/playerVolume/mute',
            "setRelativeVolume": 'https://api.ws.sonos.com/control/api/v1/players/{playerId}/playerVolume/relative'
        },
        "groupVolume": {
            "groupVolume": 'https://api.ws.sonos.com/control/api/v1/groups/{groupId}/groupVolume',
        },
        "players": {
            "homeTheater": 'https://api.ws.sonos.com/control/api/v1/players/{playerId}/homeTheater',
        }
    }

    def __init__(self, config, session, db):
        self.config = config
        self.session = session
        self.db = db

        db["sonos_access_tokens"].create({
            "id": int,
            "token": str,
            "expires_at": datetime.datetime 
        }, pk="id", if_not_exists=True)

        db["sonos_groups"].create({
            "id": int,
            "group_id": str,
            "group_name": str,
            "updated_at": datetime.datetime
        }, pk="id", if_not_exists=True)

    def getSpeaker(self, name):
        if name not in self.config["sonos"]["speakers"]:
            return None

        speaker = self.config["sonos"]["speakers"][name]
        rows = self.db["sonos_groups"].rows_where("group_name = :group_name", {"group_name": speaker["name"]}, limit=1)
        for row in rows:
            speaker["groupId"] = row["group_id"]

        return speaker

    async def getAccessToken(self):
        try:
            row = self.db["sonos_access_tokens"].get(1)
        except NotFoundError:
            row = None

        if row is not None and datetime.datetime.fromisoformat(row["expires_at"]) > datetime.datetime.now(datetime.UTC):
            return row["token"]

        sonos_access_token = await self.refreshAccessToken()
        if sonos_access_token is None:
            return
        self.db["sonos_access_tokens"].upsert(sonos_access_token, pk="id")
        return sonos_access_token["token"]

    async def updateGroups(self):
        access_token = await self.getAccessToken()
        url = self.urls["groups"]["getGroups"].format(householdId=self.config["sonos"]["household_id"])

        headers = {
            "authorization": f"Bearer {access_token}"
        }

        async with self.session.get(url, headers=headers) as resp:
            response = await resp.json()

            now = datetime.datetime.now(datetime.UTC)

            for group in response['groups']:

                rows = self.db["sonos_groups"].rows_where("group_name = :group_name", {"group_name": group["name"]}, limit=1)
                exists = False

                for row in rows:
                    exists = True
                    if row["group_id"] != group["id"]:
                        self.db["sonos_groups"].update(row["id"], {"group_id": group["id"], "updated_at": now})

                if not exists:
                    self.db["sonos_groups"].insert({
                        "group_id": group["id"],
                        "group_name": group["name"],
                        "updated_at": now
                    })

            return response

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
        
    async def playPause(self, **kwargs):
        speaker = self.getSpeaker(kwargs["speaker"])
        access_token = await self.getAccessToken()
        url = self.urls["playback"]["togglePlayPause"].format(groupId=speaker["groupId"])
        headers = {
            "authorization": f"Bearer {access_token}"
        }

        async with self.session.post(url, headers=headers) as resp:
            response = await resp.json()
            logger.info(response)

    async def skipToPreviousTrack(self, **kwargs):
        speaker = self.getSpeaker(kwargs["speaker"])
        access_token = await self.getAccessToken()
        url = self.urls["playback"]["skipToPreviousTrack"].format(groupId=speaker["groupId"])
        headers = {
            "authorization": f"Bearer {access_token}"
        }

        async with self.session.post(url, headers=headers) as resp:
            response = await resp.json()
            logger.info(response)

    async def skipToNextTrack(self, **kwargs):
        speaker = self.getSpeaker(kwargs["speaker"])
        access_token = await self.getAccessToken()
        url = self.urls["playback"]["skipToNextTrack"].format(groupId=speaker["groupId"])
        headers = {
            "authorization": f"Bearer {access_token}"
        }

        async with self.session.post(url, headers=headers) as resp:
            response = await resp.json()
            logger.info(response)

    async def volumeUp(self, **kwargs):
        speaker = self.getSpeaker(kwargs["speaker"])
        access_token = await self.getAccessToken()
        url = self.urls["playerVolume"]["setRelativeVolume"].format(playerId=speaker["playerId"])
        payload = { "volumeDelta": 2 }
        headers = {
            "authorization": f"Bearer {access_token}"
        }

        async with self.session.post(url, headers=headers, json=payload) as resp:
            response = await resp.json()
            logger.info(response)


    async def volumeDown(self, **kwargs):
        speaker = self.getSpeaker(kwargs["speaker"])
        access_token = await self.getAccessToken()
        url = self.urls["playerVolume"]["setRelativeVolume"].format(playerId=speaker["playerId"])
        payload = { "volumeDelta": -2 }
        headers = {
            "authorization": f"Bearer {access_token}"
        }

        async with self.session.post(url, headers=headers, json=payload) as resp:
            response = await resp.json()
            logger.info(response)

    async def toggleMute(self, **kwargs):
        speaker = self.getSpeaker(kwargs["speaker"])
        access_token = await self.getAccessToken()
        url = self.urls["playerVolume"]["getVolume"].format(playerId=speaker["playerId"])

        headers = {
            "authorization": f"Bearer {access_token}"
        }

        async with self.session.get(url, headers=headers) as resp:
            response = await resp.json()
            logger.info(response)

            if "muted" not in response:
                return

            muted = response["muted"]
            muted = not muted

            url = self.urls["playerVolume"]["setMute"].format(playerId=speaker["playerId"])
            payload = { "muted": muted }
            headers = {
                "authorization": f"Bearer {access_token}"
            }

            async with self.session.post(url, headers=headers, json=payload) as resp:
                response = await resp.json()
                logger.info(response)
    
    async def playAudioClip(self, **kwargs):
        speaker = self.getSpeaker(kwargs["speaker"])
        access_token = await self.getAccessToken()
        url = self.urls["audioClip"]["loadAudioClip"].format(playerId=speaker["playerId"])

        headers = {
            "authorization": f"Bearer {access_token}"
        }

        phrase = kwargs["phrase"]

        payload = {
            "clipLEDBehavior": "NONE",
            "name": phrase,
            "appId": "org.bert.sonos",
            "priority": "HIGH",
            "streamUrl": f'http://nuke.smittn.com/sounds/{phrase}.mp3',
            "volume": 40
        }
        headers = {
            "authorization": f"Bearer {access_token}"
        }

        async with self.session.post(url, headers=headers, json=payload) as resp:
            response = await resp.json()
            logger.info(response)

    async def switchToRecordPlayer(self, **kwargs):
        access_token = await self.getAccessToken()
        await self.playAudioClip(speaker="living_room", phrase="sonos_input_record_player")

        speakerRecordPlayer = self.getSpeaker("record_player")

        speaker = self.getSpeaker("living_room")
        url = self.urls["playback"]["lineIn"].format(groupId=speaker["groupId"])
        headers = {
            "authorization": f"Bearer {access_token}"
        }

        logger.info(url)
        logger.info({
            "deviceId": speakerRecordPlayer["playerId"],
        })

        async with self.session.post(url, headers=headers, json={
            "deviceId": speakerRecordPlayer["playerId"],
        }) as resp:
            response = await resp.json()
            logger.info(response)

        url = self.urls["playback"]["play"].format(groupId=speaker["groupId"])

        async with self.session.post(url, headers=headers, json={
            "deviceId": speakerRecordPlayer["playerId"],
        }) as resp:
            response = await resp.json()
            logger.info(response)


        url = self.urls["groupVolume"]["groupVolume"].format(groupId=speaker["groupId"])

        async with self.session.post(url, headers=headers, json={
            "volume": 55,
        }) as resp:
            response = await resp.json()
            logger.info(response)

    async def switchToTV(self, **kwargs):
        access_token = await self.getAccessToken()
        await self.playAudioClip(speaker="living_room", phrase="sonos_input_tv")

        speaker = self.getSpeaker("living_room")
        url = self.urls["players"]["homeTheater"].format(playerId=speaker["playerId"])
        headers = {
            "authorization": f"Bearer {access_token}"
        }

        async with self.session.post(url, headers=headers) as resp:
            response = await resp.json()
            logger.info(response)

        url = self.urls["groupVolume"]["groupVolume"].format(groupId=speaker["groupId"])

        async with self.session.post(url, headers=headers, json={
            "volume": 50,
        }) as resp:
            response = await resp.json()
            logger.info(response)
