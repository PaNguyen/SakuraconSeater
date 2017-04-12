#/usr/bin/env python2.7
import tornado.web
import json
import logging
import preferences
import datetime

import util
import db
import settings

log = logging.getLogger("mahjong")

class TablesHandler(tornado.web.RequestHandler):
    def get(self):
        with db.getCur() as cur:
            tables = []
            cur.execute("SELECT Id, Playing, Started, x, y, Name, Type FROM Tables")
            for row in cur.fetchall():
                table = {'Id': row[0],
                            'Playing': row[1],
                            'Started': str(row[2]),
                            'x': row[3],
                            'y': row[4],
                            'Name': row[5],
                            'TableType': row[6],
                            'Players': []}
                if row[2] is not None:
                    elapsed = (datetime.datetime.now() - row[2]).total_seconds()
                    table['Duration'] = util.timeString(elapsed),
                    if elapsed > settings.GAME_DURATION:
                        table['Overtime'] = True
                cur.execute("SELECT People.Id, Name, Phone, Added FROM People INNER JOIN Players ON Players.PersonId = People.Id WHERE Players.TableId = ? ORDER BY People.Added", (row[0],))

                for player in cur.fetchall():
                    table["Players"] += [{'Id': player[0],
                                            'Name': player[1],
                                            'HasPhone': player[2] is not None,
                                            'Added': str(player[3])}]
                tables += [table]
            self.write(json.dumps({'tables': tables}))
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        with db.getCur() as cur:
            cur.execute("SELECT Type FROM TableTypes")
            types = cur.fetchall()
            if len(types) == 0:
                result["message"] = "Please add some table types in admin panel"
            else:
                cur.execute("INSERT INTO Tables(Playing, Started, Name, Type) VALUES(?, NULL, ?, ?)", (0, "Untitled", types[0][0]))
                log.info("Created new table with ID:" + str(cur.lastrowid))
                result["status"] = "success"
                result["message"] = "Added table"
        self.write(json.dumps(result))

class StartTableHandler(tornado.web.RequestHandler):
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        table = self.get_argument("table", None)
        if table is not None:
            with db.getCur() as cur:
                cur.execute("UPDATE Tables SET Playing = 1, Started = datetime('now', 'localtime') WHERE Id = ?", (table,))
                log.info("Starting table with ID:" + str(table))
                result["status"] = "success"
                result["message"] = "Started table"
        self.write(json.dumps(result))

class FillTableHandler(tornado.web.RequestHandler):
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        table = self.get_argument("table", None)
        if table is not None:
            with db.getCur() as cur:
                cur.execute("SELECT TableTypes.Type, Players FROM TableTypes INNER JOIN Tables ON Tables.Type = TableTypes.Type WHERE Id = ?", (table,))
                tableType = cur.fetchone()
                cur.execute("SELECT COUNT(*) FROM Players WHERE TableId = ?", (table,))
                playercount = tableType[1] - cur.fetchone()[0]

                cur.execute("INSERT INTO Players(TableId, PersonId) \
                        SELECT ?, Queue.Id FROM Queue INNER JOIN People ON People.Id = Queue.Id \
                        WHERE Queue.Type = ? ORDER BY People.Added LIMIT ?", (table, tableType[0], playercount))

                cur.execute("DELETE FROM Queue WHERE Id IN (SELECT PersonId FROM Players)")
                log.info("Filled table with ID:" + str(table) + " with " + str(playercount) + " queued players")

                result["status"] = "success"
                result["message"] = "Filled table"
        self.write(json.dumps(result))

class NotifyTableHandler(tornado.web.RequestHandler):
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        table = self.get_argument("table", None)
        if table is not None:
            with db.getCur() as cur:
                cur.execute("SELECT Phone FROM People INNER JOIN Players ON PersonId = People.Id WHERE TableId = ?", (table,))
                client = TwilioRestClient(settings.TWILIO_SID, settings.TWILIO_AUTH)
                phones = 0
                for phone in cur.fetchall():
                    phone = phone[0]
                    if phone is not None and phone != "":
                        client.messages.create(
                            to=phone,
                            from_="+14252767908",
                            body="Your mahjong table is opening up soon!",
                        )
                        phones += 1
                result["status"] = "success"
                result["message"] = "Notified " + str(phones) + " players"
                log.info("Notified " + str(phones) + " players from table with ID:" + str(table))
        self.write(json.dumps(result))

class ClearTableHandler(tornado.web.RequestHandler):
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        table = self.get_argument("table", None)
        if table is not None:
            with db.getCur() as cur:
                cur.execute("DELETE FROM Players WHERE TableId = ?", (table,))
                cur.execute("UPDATE Tables SET Playing = 0, Started = NULL WHERE Id = ?", (table,))
                result["status"] = "success"
                result["message"] = "Cleared table"
                log.info("Cleared table with ID:" + str(table))
        self.write(json.dumps(result))

class DeleteTableHandler(tornado.web.RequestHandler):
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        table = self.get_argument("table", None)
        if table is not None:
            with db.getCur() as cur:
                cur.execute("DELETE FROM Tables WHERE Id = ?", (table,))
                result["status"] = "success"
                result["message"] = "Deleted table"
                log.info("Deleted table with ID:" + str(table))
        self.write(json.dumps(result))

class TablePositionHandler(tornado.web.RequestHandler):
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        table = self.get_argument("table", None)
        x = self.get_argument("x", None)
        y = self.get_argument("y", None)
        if table is not None and x is not None and y is not None:
            with db.getCur() as cur:
                cur.execute("UPDATE Tables SET x = ?, y = ? WHERE Id = ?", (x, y, table))
                result["status"] = "success"
                result["message"] = "Moved table"
                log.info("Moved table with ID:" + str(table) + " to " + str(x) + "," + str(y))
        self.write(json.dumps(result))

class EditTableHandler(tornado.web.RequestHandler):
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        table = self.get_argument("table", None)
        newname = self.get_argument("newname", None)
        if table is not None and newname is not None:
            with db.getCur() as cur:
                cur.execute("UPDATE Tables SET Name = ? WHERE Id = ?", (newname, table))
                result["status"] = "success"
                result["message"] = "Updated table"
                log.info("Edited table with ID: " + str(table) + " to have name: " + str(newname))
        self.write(json.dumps(result))

class TableTypeHandler(tornado.web.RequestHandler):
    def get(self):
        with db.getCur() as cur:
            cur.execute("SELECT Type, Duration, Players FROM TableTypes")
            rows = cur.fetchall()
            types = []
            for row in rows:
                types += [{'Type': row[0], 'Duration': row[1], 'Players': row[2]}]
            self.write(json.dumps(types))
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        table = self.get_argument("table", None)
        tabletype = self.get_argument("type", None)
        if table is not None:
            with db.getCur() as cur:
                cur.execute("UPDATE Tables SET Type = ? WHERE Id = ?", (tabletype, table))
                result["status"] = "success"
                result["message"] = "TableType updated"
                log.info("Changed TableType of table with ID:" + str(table) + " to " + str(tabletype))
        self.write(json.dumps(result))

class AddTableTypeHandler(tornado.web.RequestHandler):
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        tabletype = self.get_argument("type", None)
        gameduration = self.get_argument("gameduration", None)
        numplayers = self.get_argument("numplayers", None)
        with db.getCur() as cur:
            cur.execute("INSERT INTO TableTypes(Type, Duration, Players) VALUES(?, ?, ?)", (tabletype, gameduration, numplayers))
            result['status'] = "Success"
            result['message'] = "Added game type"
        self.write(json.dumps(result))

class DeleteTableTypeHandler(tornado.web.RequestHandler):
    def post(self):
        tabletype = self.get_argument("type", None)
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        if tabletype is not None:
            with db.getCur() as cur:
                cur.execute("DELETE FROM TableTypes WHERE Type = ?", (tabletype,))
                result['status'] = "success"
                result['message'] = "Deleted table type"
        self.write(json.dumps(result))
