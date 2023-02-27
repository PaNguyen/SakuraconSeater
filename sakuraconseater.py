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
import events
import notifications

import tables
import queuehandlers
import announcement
import preferences

# import and define tornado-y things
from tornado.options import define, options
define("port", default=5000, type=int)
cookie_secret = util.randString(32)

class TablePlayerHandler(tornado.web.RequestHandler):
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        player = self.get_argument("player", None)
        table = self.get_argument("table", None)
        if player is not None and table is not None:
            with db.getCur() as cur:
                cur.execute("DELETE FROM Queue WHERE Person = ?", (player,))
                cur.execute("DELETE FROM Players WHERE PersonId = ?", (player,))
                cur.execute("INSERT INTO Players(TableId, PersonId) VALUES(?, ?)", (table, player))
            result["status"] = "success"
            result["message"] = "Moved player"
            events.logEvent("playermovetotable", (player, table))
        self.write(json.dumps(result))

class DeletePlayerHandler(tornado.web.RequestHandler):
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        player = self.get_argument("player", None)
        if player is not None:
            with db.getCur() as cur:
                cur.execute("DELETE FROM People WHERE Id = ?", (player,))
            result["status"] = "success"
            result["message"] = "Deleted player"
            events.logEvent("playerdelete", player)
        self.write(json.dumps(result))

class EditPlayerHandler(tornado.web.RequestHandler):
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        player  = self.get_argument("player", None)
        newname = self.get_argument("newname", None)
        if player is not None and newname is not None:
            with db.getCur() as cur:
                cur.execute("UPDATE People SET Name = ? WHERE Id = ?", (newname, player))
            result["status"] = "success"
            result["message"] = "Updated player"
            events.logEvent("playerrename", (player,newname))
        self.write(json.dumps(result))

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class ProjectorHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("projector.html")

class ManageHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("manage.html")

class AnnouncementHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("announcement.html")

class AdminHandler(tornado.web.RequestHandler):
    def get(self):
        with db.getCur() as cur:
            cur.execute("SELECT Type, Duration, Players FROM TableTypes")
            rows = cur.fetchall()
            types = []
            for row in rows:
                types += [{'Type': row[0], 'Duration': row[1], 'Players': row[2]}]

            eventTypes = {
                    'playerqueueadd': 'NewPlayers',
                    'textsent': 'TextsSent',
                    'tablestart': 'TablesStarted',
                    'tableclear': 'TablesCleared'
                }

            grouping = "strftime('%H', Time)"

            stats = {}
            timedstats = {}
            for event, stat in eventTypes.items():
                cur.execute("SELECT COUNT(*) FROM Events WHERE Type = ?", (event,))
                stats[stat] = cur.fetchone()[0]

                cur.execute("SELECT {grouping}, COUNT(*) FROM Events WHERE Type = ? GROUP BY {grouping};".format(grouping = grouping), (event,))
                counts = cur.fetchall()
                for count in counts:
                    if count[0] not in timedstats:
                        timedstats[count[0]] = {}
                    timedstats[count[0]][stat] = count[1]

            self.render("admin.html",
                    tabletypes = types,
                    stats = stats,
                    timedstats = timedstats
                )

class Application(tornado.web.Application):
    def __init__(self):
        db.init()
        events.logEvent('start')

        if getattr(sys, 'frozen', False):
            curdirname = os.path.dirname(sys.executable)
        else:
            curdirname = os.path.dirname(os.path.realpath(__file__))

        handlers = [
                (r"/", MainHandler),
                (r"/projector", ProjectorHandler),
                (r"/manage", ManageHandler),
                (r"/announcement", AnnouncementHandler),
                (r"/admin", AdminHandler),
                (r"/api/preferences", preferences.PreferencesHandler),
                (r"/api/preference/(.*)", preferences.PreferenceHandler),
                (r"/api/tables", tables.TablesHandler),
                (r"/api/starttable", tables.StartTableHandler),
                (r"/api/filltable", tables.FillTableHandler),
                (r"/api/notifytable", notifications.NotifyTableHandler),
                (r"/api/notifyplayer", notifications.NotifyPlayerHandler),
                (r"/api/cleartable", tables.ClearTableHandler),
                (r"/api/deletetable", tables.DeleteTableHandler),
                (r"/api/tabletype", tables.TableTypeHandler),
                (r"/api/tableschedule", tables.ScheduleTableHandler),
                (r"/api/addgametype", tables.AddTableTypeHandler),
                (r"/api/deletetabletype", tables.DeleteTableTypeHandler),
                (r"/api/edittable", tables.EditTableHandler),
                (r"/api/tableposition", tables.TablePositionHandler),
                (r"/api/queue", queuehandlers.QueueHandler),
                (r"/api/queueplayer", queuehandlers.QueuePlayerHandler),
                (r"/api/tableplayer", TablePlayerHandler),
                (r"/api/deleteplayer", DeletePlayerHandler),
                (r"/api/editplayer", EditPlayerHandler),
                (r"/api/announcement", announcement.CurrentAnnouncementHandler),
                (r"/api/teachingsessions", announcement.TeachingSessionsHandler),
                (r"/api/deleteteachingsession", announcement.DeleteTeachingSessionHandler),
        ]
        settings = dict(
                template_path = os.path.join(curdirname, "templates"),
                static_path = os.path.join(curdirname, "static"),
                cookie_secret = cookie_secret
        )
        tornado.web.Application.__init__(self, handlers, **settings)

def periodic():
    with db.getCur() as cur:
        # cleanup
        cur.execute("DELETE FROM People WHERE Id NOT IN (SELECT PersonId FROM Players) AND Id NOT IN (SELECT Person FROM Queue);");
    notifications.sendNotifications()

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
    tornado.ioloop.PeriodicCallback(periodic, 10 * 1000).start()
    tornado.ioloop.IOLoop.instance().start()

def sigint_handler(signum, frame):
    tornado.ioloop.IOLoop.instance().stop()

if __name__ == "__main__":
    main()
