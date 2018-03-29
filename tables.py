#/usr/bin/env python2.7
import tornado.web
import json
import logging
import preferences
import datetime
from twilio.rest import Client

import util
import db
import settings
import events

class TablesHandler(tornado.web.RequestHandler):
    def get(self):
        with db.getCur() as cur:
            cols     = ['Id', 'Playing', 'Started', 'x', 'y', 'Name', 'Tables.Type', 'TableTypes.Duration', 'ScheduledStart']
            colnames = ['Id', 'Playing', 'Started', 'x', 'y', 'Name', 'Type',        'Duration', 'ScheduledStart']
            cur.execute(
                    "SELECT {cols} FROM Tables "
                    " JOIN TableTypes ON TableTypes.Type = Tables.Type".format(cols=",".join(cols))
            )
            tables = [dict(zip(colnames, row)) for row in cur.fetchall()]
            for table in tables:
                table["Players"] = []
                if table ['Started'] is not None:
                    elapsed = (datetime.datetime.now() - datetime.datetime.strptime(table['Started'], '%Y-%m-%d %H:%M:%S')).total_seconds()
                    table['Elapsed'] = util.timeString(elapsed)
                    if elapsed > table['Duration'] * 60:
                        table['Overtime'] = True
                cur.execute(
                        "SELECT People.Id, Name, Phone, Added FROM People "
                        " INNER JOIN Players ON Players.PersonId = People.Id "
                        " WHERE Players.TableId = ? ORDER BY People.Added",
                        (table['Id'],)
                )

                for player in cur.fetchall():
                    table["Players"] += [{'Id': player[0],
                                            'Name': player[1],
                                            'HasPhone': player[2] is not None,
                                            'Added': str(player[3])}]
            self.write(json.dumps({'tables': tables}))
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        with db.getCur() as cur:
            cur.execute("SELECT Type FROM TableTypes")
            types = cur.fetchone()
            if len(types) == 0:
                result["message"] = "Please add some table types in admin panel"
            else:
                cur.execute(
                        "INSERT INTO Tables(Playing, Started, Name, Type) VALUES(?, NULL, ?, ?)",
                        (0, "Untitled", types[0])
                )
                result["status"] = "success"
                result["message"] = "Added table"

        if result["status"] == "success":
            events.logEvent('tablecreate', cur.lastrowid)
        self.write(json.dumps(result))

class StartTableHandler(tornado.web.RequestHandler):
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        table = self.get_argument("table", None)
        if table is not None:
            with db.getCur() as cur:
                cur.execute("UPDATE Tables SET Playing = 1, Started = datetime('now', 'localtime') WHERE Id = ?", (table,))
            result["status"] = "success"
            result["message"] = "Started table"
            events.logEvent('tablestart', table)
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

                cur.execute("INSERT INTO Players(TableId, PersonId)"
                        " SELECT ?, Queue.Person FROM Queue "
                        " INNER JOIN People ON People.Id = Queue.Person"
                        " WHERE Queue.Type = ? ORDER BY People.Added LIMIT ?", (table, tableType[0], playercount))

                cur.execute("DELETE FROM Queue WHERE Person IN (SELECT PersonId FROM Players)")
            result["status"] = "success"
            result["message"] = "Filled table"
            events.logEvent('tablefill', (table, playercount))
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
            events.logEvent('tableclear', table)
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
            events.logEvent('tabledelete', table)
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
            events.logEvent('tablerename', (table, newname))
        self.write(json.dumps(result))

class ScheduleTableHandler(tornado.web.RequestHandler):
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        table = self.get_argument("table", None)
        time = self.get_argument("time", None)
        if table is not None and time is not None:
            try:
                if time != "":
                    eta = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
                    with db.getCur() as cur:
                        cur.execute("UPDATE Tables SET ScheduledStart = ? WHERE Id = ?", (time, table))
                else:
                    with db.getCur() as cur:
                        cur.execute("UPDATE Tables SET ScheduledStart = NULL WHERE Id = ?", (table,))
                result["status"] = "success"
                result["message"] = "Scheduled time updated"
                events.logEvent('tableschedule', (table, time))
            except ValueError:
                result["message"] = "Failed to parse time"
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
            events.logEvent('tableretype', (table, tabletype))
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
