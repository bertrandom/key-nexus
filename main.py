import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Annotated, Union

import aiohttp
from appcfg import get_config
from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel
from sqlite_utils import Database

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

    modules = {
        "homeassistant": HomeAssistant(config, session),
        "hubitat": Hubitat(config, session),
        "sonos": Sonos(config, session, db),
        "openai": openai_client
    }
    yield
    await session.close()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def read_root():
    return {"ok": True}

@app.get("/say/{phrase_id}.mp3")
async def say(phrase_id):

    if phrase_id not in config["phrases"]:
        return {"ok": False, "error": "phrase not found"}

    client = modules["openai"]

    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=config["phrases"][phrase_id]
    )

    return StreamingResponse(response.iter_bytes())

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
        if args is None:
            await func()
        else:
            await func(**args)
    else:
        return {"ok": False, "error": "function not found"}

    return {"ok": True}
