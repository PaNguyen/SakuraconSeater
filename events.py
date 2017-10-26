#!/usr/bin/env python3

import json
import logging
import datetime

import db

log = logging.getLogger("mahjong")
logging.basicConfig(filename = "mahjong.log", level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())

def logEvent(eventType, data = None):
    if data is not None:
        data = json.dumps(data)
    else:
        data = ""
    with db.getCur() as cur:
        cur.execute(
                "INSERT INTO Events(Type, Time, Data) VALUES (?, datetime('now', 'localtime'), ?)",
                (eventType, data))
    log.info(str(datetime.datetime.now()) + "|" + eventType + "|" + data)
