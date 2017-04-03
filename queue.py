#!/usr/bin/env python2.7

import tornado.web
import json
import datetime
import logging

import db
import util

log = logging.getLogger("mahjong")

class QueueHandler(tornado.web.RequestHandler):
    def get(self):
        with db.getCur() as cur:
            now = datetime.datetime.now()
            cur.execute("SELECT People.Id, Name, Phone, Added FROM People INNER JOIN Queue ON Queue.Id = People.Id ORDER BY People.Added")
            rows = cur.fetchall()
            cur.execute("SELECT Started, Playing FROM Tables WHERE NOT Beginner ORDER BY Playing ASC, Started ASC")
            tables = cur.fetchall()
            queue = []
            position = 0
            for row in rows:
                eta = now
                table = int(position / 4)
                if len(tables) > 0:
                    if tables[table % len(tables)][1]:
                        eta = tables[table % len(tables)][0] + datetime.timedelta(minutes = 70)
                    eta += datetime.timedelta(minutes = int(table / len(tables)) * 70)
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
            table = int(position / 4)
            if len(tables) > 0 and tables[table % len(tables)][1]:
                neweta = tables[table % len(tables)][0] + datetime.timedelta(minutes = 70)
                neweta += datetime.timedelta(minutes = int(table / len(tables)) * 70)
            newremaining = util.timeString((neweta - now).total_seconds())
            cur.execute("SELECT People.Id, Name, Phone, Added FROM People INNER JOIN BeginnerQueue ON BeginnerQueue.Id = People.Id ORDER BY People.Added")
            rows = cur.fetchall()
            cur.execute("SELECT Started, Playing FROM Tables WHERE Beginner ORDER BY Started ASC")
            tables = cur.fetchall()
            beginnerqueue = []
            position = 0
            if len(tables) > 0:
                for row in rows:
                    eta = now
                    table = int(position / 4)
                    if tables[table % len(tables)][1]:
                        eta = tables[table % len(tables)][0] + datetime.timedelta(minutes = 70)
                    eta = eta + datetime.timedelta(minutes = int(table / len(tables)) * 70)
                    remaining = (eta - now).total_seconds()
                    beginnerqueue += [{'Id': row[0],
                                'Name': row[1],
                                'HasPhone': row[2] is not None,
                                'ETA': str(eta),
                                'Remaining':util.timeString(remaining)}]
                    position += 1
                beginnereta = now
                table = int(position / 4)
                if tables[table % len(tables)][1]:
                    beginnereta = tables[table % len(tables)][0] + datetime.timedelta(minutes = 70)
                beginnereta += datetime.timedelta(minutes = int(table / len(tables)) * 70)
            else:
                beginnereta = now
            beginnerremaining = util.timeString((beginnereta - now).total_seconds())
            self.write(json.dumps({
                'queue': queue,
                'beginnerqueue': beginnerqueue,
                'ETA': str(neweta),
                'BeginnerETA': str(beginnereta),
                'Remaining': newremaining,
                'BeginnerRemaining': beginnerremaining
            }))
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        name = self.get_argument("name", None)
        phone = self.get_argument("phone", None)
        beginner = self.get_argument("beginner", False)
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
                    if beginner:
                        cur.execute("INSERT INTO BeginnerQueue(Id) VALUES(?)", (cur.lastrowid,))
                        log.info("Added player with ID: " + str(cur.lastrowid) + " to beginner queue")
                    else:
                        cur.execute("INSERT INTO Queue(Id) VALUES(?)", (cur.lastrowid,))
                        log.info("Added player with ID: " + str(cur.lastrowid) + " to queue")
                result["status"] = "success"
                result["message"] = "Added player"
        self.write(json.dumps(result))

class QueuePlayerHandler(tornado.web.RequestHandler):
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        player = self.get_argument("player", None)
        if player is not None:
            with db.getCur() as cur:
                cur.execute("DELETE FROM Queue WHERE Id = ?", (player,))
                cur.execute("DELETE FROM BeginnerQueue WHERE Id = ?", (player,))
                cur.execute("DELETE FROM Players WHERE PersonId = ?", (player,))
                cur.execute("INSERT INTO Queue(Id) VALUES(?)", (player,))
                log.info("Moved player with ID: " + str(player) + " to queue")
                result["status"] = "success"
                result["message"] = "Moved player"
        self.write(json.dumps(result))

class BeginnerQueuePlayerHandler(tornado.web.RequestHandler):
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        player = self.get_argument("player", None)
        if player is not None:
            with db.getCur() as cur:
                cur.execute("DELETE FROM BeginnerQueue WHERE Id = ?", (player,))
                cur.execute("DELETE FROM Queue WHERE Id = ?", (player,))
                cur.execute("DELETE FROM Players WHERE PersonId = ?", (player,))
                cur.execute("INSERT INTO BeginnerQueue(Id) VALUES(?)", (player,))
                result["status"] = "success"
                result["message"] = "Moved player"
                log.info("Moved player with ID: " + str(player) + " to beginner queue")
        self.write(json.dumps(result))
