#!/usr/bin/env python3

import tornado.web
import json
import datetime

import db
import util
import events

def getTypeQueue(tableType):
    with db.getCur() as cur:
        cur.execute("SELECT Duration, Players FROM TableTypes WHERE Type = ?", (tableType,))
        typeData = cur.fetchone()
        duration = typeData[0]
        playercount = typeData[1]

        cur.execute(
                "SELECT People.Id, Name, Phone, Added FROM People "
                " INNER JOIN Queue ON Queue.Person = People.Id "
                " WHERE Queue.Type = ? ORDER BY People.Added", (tableType,))
        rows = cur.fetchall()

        cols = ['Started','Playing','ScheduledStart']
        cur.execute(
                "SELECT {cols} FROM Tables "
                " WHERE Type = ? AND ScheduledStart IS NULL"
                " ORDER BY Playing ASC, Started ASC".format(cols=",".join(cols)),
                (tableType,)
        )
        tables = [dict(zip(cols,row)) for row in cur.fetchall()]

        cur.execute(
                "SELECT {cols} FROM Tables "
                " WHERE Type = ? AND ScheduledStart IS NOT NULL"
                " ORDER BY Playing ASC, Started ASC".format(cols=",".join(cols)),
                (tableType,)
        )
        scheduledtables = [dict(zip(cols,row)) for row in cur.fetchall()]

        now = datetime.datetime.now()
        queue = []
        position = 0
        for row in rows:
            eta = now
            table = int(position / playercount)
            if len(tables) > 0:
                if tables[table % len(tables)]['Started'] is not None:
                    eta = datetime.datetime.strptime(tables[table % len(tables)]['Started'], '%Y-%m-%d %H:%M:%S')
                    eta += datetime.timedelta(minutes = duration)
                eta += datetime.timedelta(minutes = int(table / len(tables)) * duration)
            elif len(scheduledtables) > 0:
                if scheduledtables[0]['ScheduledStart'] is None or table >= 1:
                    eta = None
                else:
                    eta = datetime.datetime.strptime(scheduledtables[0]['ScheduledStart'], '%Y-%m-%d %H:%M:%S')
            else:
                eta = None
            remaining = (eta - now).total_seconds()
            if remaining > 0:
                remaining = util.timeString(remaining)
            else:
                remaining = "NOW"
            queue += [{'Id': row[0],
                        'Name': row[1],
                        'HasPhone': row[2] is not None,
                        'ETA': str(eta),
                        'Remaining': remaining}]
            position += 1
        table = int(position / playercount)
        neweta = None
        if len(tables) > 0:
            if tables[table % len(tables)]['Playing']:
                neweta = datetime.datetime.strptime(tables[table % len(tables)]['Started'], '%Y-%m-%d %H:%M:%S')
                neweta += datetime.timedelta(minutes = duration)
            else:
                neweta = now
            neweta += datetime.timedelta(minutes = int(table / len(tables)) * duration)
        elif len(scheduledtables) > 0:
            if table >= 1:
                neweta = None
            else:
                if scheduledtables[0]['ScheduledStart'] is not None:
                    neweta = datetime.datetime.strptime(scheduledtables[0]['ScheduledStart'], '%Y-%m-%d %H:%M:%S')
        if neweta is not None:
            newRemaining = (neweta - now).total_seconds()
            if newRemaining > 0:
                newRemaining = util.timeString(newRemaining)
            else:
                newRemaining = "NOW"
        else:
            newRemaining = "NEVER"
        return {
            'Type': tableType,
            'Queue': queue,
            'ETA': str(neweta),
            'Remaining': newRemaining
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
            players = []
            with db.getCur() as cur:
                for i in range(numplayers):
                    n = name
                    if i > 0:
                        n += " (" + str(i) + ")"
                        phone = None
                    cur.execute("INSERT INTO People(Name, Phone, Added) VALUES(?, ?, datetime('now', 'localtime'))", (n, phone))
                    cur.execute("INSERT INTO Queue(Person, Type) VALUES(?, ?)", (cur.lastrowid, tableType))
                    players += [(cur.lastrowid, n)]
            for player in players:
                events.logEvent('playerqueueadd', (player[0], player[1], tableType, numplayers))
            result["status"] = "success"
            result["message"] = "Added " + str(numplayers) + "players"
        self.write(json.dumps(result))

class QueuePlayerHandler(tornado.web.RequestHandler):
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        player = self.get_argument("player", None)
        tableType = self.get_argument("type", None)
        if player is not None:
            with db.getCur() as cur:
                cur.execute("DELETE FROM Queue WHERE Person = ?", (player,))
                cur.execute("DELETE FROM Players WHERE PersonId = ?", (player,))
                cur.execute("INSERT INTO Queue(Person, Type) VALUES(?, ?)", (player, tableType))
            events.logEvent('playerqueuemove', (player, tableType))
            result["status"] = "success"
            result["message"] = "Moved player"
        self.write(json.dumps(result))
