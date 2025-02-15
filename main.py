import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Annotated, Union

import aiohttp
import paho.mqtt.client as mqtt
from appcfg import get_config
from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel
from sqlite_utils import Database

from modules.eo import ElectricObjects
from modules.flipdisc import FlipDisc
from modules.generic_mqtt import GenericMqtt
from modules.homeassistant import HomeAssistant
from modules.hubitat import Hubitat
from modules.sonos import Sonos


class Keypress(BaseModel):
    client_id: str
    key: str

logger = logging.getLogger(__name__)

config = get_config(__name__)

modules = {}

cwd = os.path.dirname(__file__)
db_path = (cwd + "/data/nexus.db")

@asynccontextmanager
async def lifespan(app: FastAPI):

    global modules
    session = aiohttp.ClientSession()

    db = Database(db_path)
    db.enable_wal()

    openai_client = OpenAI(
        api_key=config["openai"]["api_key"],
    )

    def on_connect(client, userdata, flags, reason_code, properties):
        logger.info(f"Connected to MQTT with result code {reason_code}")

    def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
        if reason_code != 0:
            logger.info("Unexpected MQTT disconnection. Will auto-reconnect")

    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqttc.username_pw_set(config["mqtt"]["username"], config["mqtt"]["password"])
    mqttc.on_connect = on_connect
    mqttc.on_disconnect = on_disconnect
    mqttc.connect(config["mqtt"]["host"], config["mqtt"]["port"], 60)    
    mqttc.loop_start()

    modules = {
        "homeassistant": HomeAssistant(config, session),
        "hubitat": Hubitat(config, session),
        "sonos": Sonos(config, session, db),
        "eo": ElectricObjects(config, session),
        "openai": openai_client,
        "flipdisc": FlipDisc(config, mqttc),
        "generic_mqtt": GenericMqtt(config, mqttc)
    }
    yield
    await session.close()

app = FastAPI(lifespan=lifespan)
app.mount("/sounds", StaticFiles(directory="sounds"), name="sounds")

@app.get("/")
async def read_root():
    return {"ok": True}

@app.post("/key/press")
async def press_key(keypress: Keypress):

    logger.info(keypress)
    if keypress.client_id not in config["mapping"]:
        return {"ok": False, "error": "client not found"}

    mapping = config["mapping"][keypress.client_id]
    if keypress.key not in mapping:
        return {"ok": False, "error": "key not found"}

    selection = mapping[keypress.key]

    if selection["module"] not in modules:
        return {"ok": False, "error": "module not found"}

    module = modules[selection["module"]]
    function = selection["function"]

    args = None
    if "args" in selection:
        args = selection["args"]

    if hasattr(module, function) and callable(func := getattr(module, function)):
        logger.info(f"{selection['module']}.{function}({args})")
        try:
            if args is None:
                await func()
            else:
                await func(**args)
        except Exception as e:
            return {"ok": False, "error": str(e)}
    else:
        return {"ok": False, "error": "function not found"}

    return {"ok": True}

@app.get("/sonos/groups/update")
async def update_sonos_groups():
    try:
        await modules["sonos"].updateGroups()
    except Exception as e:
        logger.error("Error updating Sonos groups: %s", str(e))
        return {"ok": False, "error": str(e)}
    return {"ok": True}
