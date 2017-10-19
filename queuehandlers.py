#!/usr/bin/env python3

import tornado.web
import json
import datetime
import logging

import db
import util

log = logging.getLogger("mahjong")

def getTypeQueue(tableType):
    with db.getCur() as cur:

        cur.execute("SELECT Duration, Players FROM TableTypes WHERE Type = ?", (tableType,))
        typeData = cur.fetchone()
        duration = typeData[0]
        playercount = typeData[1]

        cur.execute("SELECT People.Id, Name, Phone, Added FROM People \
                INNER JOIN Queue ON Queue.Id = People.Id WHERE Queue.Type = ? ORDER BY People.Added", (tableType,))
        rows = cur.fetchall()

        cur.execute("SELECT Started, Playing FROM Tables WHERE Type = ? ORDER BY Playing ASC, Started ASC", (tableType,))
        tables = cur.fetchall()

        now = datetime.datetime.now()
        queue = []
        position = 0
        for row in rows:
            eta = now
            table = int(position / playercount)
            if len(tables) > 0:
                if tables[table % len(tables)][1]:
                    eta = tables[table % len(tables)][0] + datetime.timedelta(minutes = duration)
                eta += datetime.timedelta(minutes = int(table / len(tables)) * duration)
            else:
                neweta = now
            remaining = (eta - now).total_seconds()
            queue += [{'Id': row[0],
                        'Name': row[1],
                        'HasPhone': row[2] is not None,
                        'ETA': str(eta),
                        'Remaining':util.timeString(remaining)}]
            position += 1
        neweta = now
        table = int(position / playercount)
        if len(tables) > 0 and tables[table % len(tables)][1]:
            neweta = datetime.datetime.strptime(tables[table % len(tables)][0], '%Y-%m-%d %H:%M:%S')
            neweta += datetime.timedelta(minutes = duration)
            neweta += datetime.timedelta(minutes = int(table / len(tables)) * duration)
        newremaining = util.timeString((neweta - now).total_seconds())
        return {
            'Type': tableType,
            'Queue': queue,
            'ETA': str(neweta),
            'Remaining': newremaining
        }

class QueueHandler(tornado.web.RequestHandler):
    def get(self):
        with db.getCur() as cur:
            cur.execute("SELECT Type FROM TableTypes")
            rows = cur.fetchall()
        queues = []
        for row in rows:
            queues += [getTypeQueue(row[0])]
        self.write(json.dumps({'Queues':queues}))
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        name = self.get_argument("name", None)
        phone = self.get_argument("phone", None)
        tableType = self.get_argument("type", False)
        numplayers = int(self.get_argument("numplayers", "1"))
        if name is None or name == "":
            result["message"] = "Please enter a name"
        else:
            if phone == "":
                phone = None
            with db.getCur() as cur:
                for i in range(numplayers):
                    n = name
                    if i > 0:
                        n += " (" + str(i) + ")"
                        phone = None
                    cur.execute("INSERT INTO People(Name, Phone, Added) VALUES(?, ?, datetime('now', 'localtime'))", (n, phone))
                    cur.execute("INSERT INTO Queue(Id, Type) VALUES(?, ?)", (cur.lastrowid, tableType))
                    log.info("Added player with ID: " + str(cur.lastrowid) + " to " + tableType + " queue")
                result["status"] = "success"
                result["message"] = "Added player"
        self.write(json.dumps(result))

class QueuePlayerHandler(tornado.web.RequestHandler):
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        player = self.get_argument("player", None)
        tableType = self.get_argument("type", None)
        if player is not None:
            with db.getCur() as cur:
                cur.execute("DELETE FROM Queue WHERE Id = ?", (player,))
                cur.execute("DELETE FROM Players WHERE PersonId = ?", (player,))
                cur.execute("INSERT INTO Queue(Id, Type) VALUES(?, ?)", (player, tableType))
                log.info("Moved player with ID: " + str(player) + " to " + tableType + " queue")
                result["status"] = "success"
                result["message"] = "Moved player"
        self.write(json.dumps(result))
