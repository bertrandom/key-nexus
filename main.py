import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Annotated, Union

import aiohttp
from appcfg import get_config
from fastapi import Depends, FastAPI
from pydantic import BaseModel

from modules.hubitat import Hubitat


class Keypress(BaseModel):
    client_id: str
    key: str

logger = logging.getLogger(__name__)

config = get_config(__name__)

modules = {}

@asynccontextmanager
async def lifespan(app: FastAPI):

    global modules
    session = aiohttp.ClientSession()
    modules = {
        "hubitat": Hubitat(config, session),
    }
    yield
    await session.close()

app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"ok": True}

@app.post("/key/press")
async def press_key(keypress: Keypress):

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

    if hasattr(module, function) and callable(func := getattr(module, function)):
        await func()
    else:
        return {"ok": False, "error": "function not found"}

    return {"ok": True}
