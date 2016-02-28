#!/usr/bin/env python3

import sys
import os.path
import os
import math
import tornado.httpserver
from tornado.httpclient import AsyncHTTPClient
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.template
import signal
import json
import datetime

import util
import settings
import db
import session

# import and define tornado-y things
from tornado.options import define, options
define("port", default=5000, type=int)
cookie_secret = util.randString(32)


class TablesHandler(session.AuthenticatedHandler):
    def get(self):
        with db.getCur() as cur:
            tables = []
            cur.execute("SELECT Id, Playing, Started FROM Tables")
            for row in cur.fetchall():
                table = {'Id': row[0],
                            'Playing': row[1],
                            'Started': row[2],
                            'Players': []}
                cur.execute("SELECT People.Id, Name, Phone, Added FROM People INNER JOIN Players ON Players.PersonId = People.Id WHERE Players.TableId = ?", (row[0],))

                for player in cur.fetchall():
                    table["Players"] += [{'Id': player[0],
                                            'Name': player[1],
                                            'HasPhone': player[2] is not None,
                                            'Added': player[3]}]
                tables += [table]
            self.write(json.dumps({'tables': tables}))
    def handlepost(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        with db.getCur() as cur:
            cur.execute("INSERT INTO Tables(Playing, Started) VALUES(0, NULL, NULL)")
            result["status"] = "success"
            result["message"] = "Added table"
        self.write(json.dumps(result))

class StartTableHandler(session.AuthenticatedHandler):
    def handlepost(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        table = self.get_argument("table", None)
        if table is not None:
            with db.getCur() as cur:
                cur.execute("UPDATE Tables SET Playing = 1, Started = datetime('now', 'localtime') WHERE Id = ?", (table,))
                result["status"] = "success"
                result["message"] = "Started table"
        self.write(json.dumps(result))

class ClearTableHandler(session.AuthenticatedHandler):
    def handlepost(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        table = self.get_argument("table", None)
        if table is not None:
            with db.getCur() as cur:
                cur.execute("DELETE FROM Players WHERE TableId = ?", (table,))
                cur.execute("UPDATE Tables SET Playing = 0, Started = NULL WHERE Id = ?", (table,))
                result["status"] = "success"
                result["message"] = "Cleared table"
        self.write(json.dumps(result))

class DeleteTableHandler(session.AuthenticatedHandler):
    def handlepost(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        table = self.get_argument("table", None)
        if table is not None:
            with db.getCur() as cur:
                cur.execute("DELETE FROM Tables WHERE Id = ?", (table))
                result["status"] = "success"
                result["message"] = "Deleted table"
        self.write(json.dumps(result))

class QueueHandler(session.AuthenticatedHandler):
    def get(self):
        with db.getCur() as cur:
            queue= []
            cur.execute("SELECT People.Id, Name, Phone, Added FROM People INNER JOIN Queue ON Queue.Id = People.Id")
            for row in cur.fetchall():
                queue += [{'Id': row[0],
                            'Name': row[1],
                            'HasPhone': row[2] is not None,
                            'Added': row[2]}]
            self.write(json.dumps({'queue': queue}))
    def handlepost(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        name = self.get_argument("name", None)
        phone = self.get_argument("phone", None)
        if name is None or name == "":
            result["message"] = "Please enter a name"
        else:
            if phone == "":
                phone = None
            with db.getCur() as cur:
                cur.execute("INSERT INTO People(Name, Phone, Added) VALUES(?, ?, datetime('now', 'localtime'))", (name, phone))
                cur.execute("INSERT INTO Queue(Id) VALUES(?)", (cur.lastrowid,))
                result["status"] = "success"
                result["message"] = "Added player"
        self.write(json.dumps(result))

class NotifyPlayerHandler(session.AuthenticatedHandler):
    def handlepost(self):
        pass

class TablePlayerHandler(session.AuthenticatedHandler):
    def handlepost(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        player = self.get_argument("player", None)
        table = self.get_argument("table", None)
        if player is not None and table is not None:
            with db.getCur() as cur:
                cur.execute("DELETE FROM Queue WHERE Id = ?", (player,))
                cur.execute("DELETE FROM Players WHERE PersonId = ?", (player,))
                cur.execute("INSERT INTO Players(TableId, PersonId) VALUES(?, ?)", (table, player))
                result["status"] = "success"
                result["message"] = "Moved player"
        self.write(json.dumps(result))

class QueuePlayerHandler(session.AuthenticatedHandler):
    def handlepost(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        player = self.get_argument("player", None)
        if player is not None:
            with db.getCur() as cur:
                cur.execute("DELETE FROM Queue WHERE Id = ?", (player,))
                cur.execute("DELETE FROM Players WHERE PersonId = ?", (player,))
                cur.execute("INSERT INTO Queue(Id) VALUES(?)", (player,))
                result["status"] = "success"
                result["message"] = "Moved player"
        self.write(json.dumps(result))

class DeletePlayerHandler(session.AuthenticatedHandler):
    def handlepost(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        player = self.get_argument("player", None)
        if player is not None:
            with db.getCur() as cur:
                cur.execute("DELETE FROM People WHERE Id = ?", (player,))
                result["status"] = "success"
                result["message"] = "Deleted player"
        self.write(json.dumps(result))

class LoginHandler(tornado.web.RequestHandler):
    def get(self):
        cookie = session.getSession(self)
        self.write(json.dumps({'loggedIn': True if session.loggedIn(cookie) else False}))
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}

        try:
            cookie = session.getSession(self)
            if not session.loggedIn(cookie):
                password = self.get_argument('password', None)
                if password is None or password == "":
                    result["message"] = "Please enter a password"
                else:
                    if session.login(cookie, password):
                        result["status"] = "success"
                        result["message"] = "Successfully logged in"
                    else:
                        result["message"] = "Incorrect login details"
            else:
                result["status"] = "success"
                result["message"] = "Already logged in"
        except Exception, e:
            result["message"] = ": " + str(e)

        self.write(json.dumps(result))

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class Application(tornado.web.Application):
    def __init__(self):
        db.init()

        handlers = [
                (r"/", MainHandler),
                (r"/api/login", LoginHandler),
                (r"/api/tables", TablesHandler),
                (r"/api/starttable", StartTableHandler),
                (r"/api/cleartable", ClearTableHandler),
                (r"/api/deletetable", DeleteTableHandler),
                (r"/api/queue", QueueHandler),
                (r"/api/queueplayer", QueuePlayerHandler),
                (r"/api/tableplayer", TablePlayerHandler),
                (r"/api/notifyplayer", NotifyPlayerHandler),
                (r"/api/deleteplayer", DeletePlayerHandler),
        ]
        settings = dict(
                template_path = os.path.join(os.path.dirname(__file__), "templates"),
                static_path = os.path.join(os.path.dirname(__file__), "static"),
                debug = True,
                cookie_secret = cookie_secret
        )
        tornado.web.Application.__init__(self, handlers, **settings)


def periodicCleanup():
    with db.getCur() as cur:
        cur.execute("DELETE FROM Sessions WHERE Expires <= NOW();")
        cur.execute("DELETE FROM People WHERE Id NOT IN (SELECT PersonId FROM Players) AND Id NOT IN (SELECT Id FROM Qeueue);");

def main():
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except:
            port = 5000
    else:
        port = 5000

    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application(), max_buffer_size=24*1024**3)
    http_server.listen(os.environ.get("PORT", port))

    signal.signal(signal.SIGINT, sigint_handler)

    # start it up
    tornado.ioloop.PeriodicCallback(periodicCleanup, 60 * 60 * 1000).start() # run periodicCleanup once an hour
    tornado.ioloop.IOLoop.instance().start()
    qm.end()

def sigint_handler(signum, frame):
    tornado.ioloop.IOLoop.instance().stop()

if __name__ == "__main__":
    main()
