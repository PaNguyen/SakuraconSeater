#!/usr/bin/env python2.7

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
from twilio.rest import TwilioRestClient
import logging

import util
import settings
import db

import tables
import queue
import announcement
import preferences

# import and define tornado-y things
from tornado.options import define, options
define("port", default=5000, type=int)
cookie_secret = util.randString(32)
log = logging.getLogger("mahjong")

class NotifyPlayerHandler(tornado.web.RequestHandler):
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        player = self.get_argument("player", None)
        if player is not None:
            with db.getCur() as cur:
                cur.execute("SELECT Phone FROM People WHERE Id = ?", (player,))
                row = cur.fetchone()
                phone = row[0]
                if phone is not None:
                    client = TwilioRestClient(settings.TWILIO_SID, settings.TWILIO_AUTH)

                    try:
                        client.messages.create(
                            to=phone,
                            from_="+14252767908",
                            body="Your mahjong table is opening up soon!",
                        )
                        log.info("Notified player with ID: " + str(player))
                        result["status"] = "success"
                        result["message"] = "Notified player"
                    except:
                        log.info("Failed to notify player with ID: " + str(player))
                        result["message"] = "Failed to notify player"
        self.write(json.dumps(result))

class TablePlayerHandler(tornado.web.RequestHandler):
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        player = self.get_argument("player", None)
        table = self.get_argument("table", None)
        if player is not None and table is not None:
            with db.getCur() as cur:
                cur.execute("DELETE FROM Queue WHERE Id = ?", (player,))
                cur.execute("DELETE FROM BeginnerQueue WHERE Id = ?", (player,))
                cur.execute("DELETE FROM Players WHERE PersonId = ?", (player,))
                cur.execute("INSERT INTO Players(TableId, PersonId) VALUES(?, ?)", (table, player))
                log.info("Moved player with ID: " + str(player) + " to table with ID: " + str(table))
                result["status"] = "success"
                result["message"] = "Moved player"
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
                log.info("Deleted player with ID: " + str(player))
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
                log.info("Edited player with ID: " + str(player) + " to have name: " + str(newname))
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
            self.render("admin.html", tabletypes=types)

class Application(tornado.web.Application):
    def __init__(self):
        db.init()

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
                (r"/api/notifytable", tables.NotifyTableHandler),
                (r"/api/cleartable", tables.ClearTableHandler),
                (r"/api/deletetable", tables.DeleteTableHandler),
                (r"/api/beginnertable", tables.BeginnerTableHandler),
                (r"/api/tabletype", tables.TableTypeHandler),
                (r"/api/addgametype", tables.AddTableTypeHandler),
                (r"/api/deletetabletype", tables.DeleteTableTypeHandler),
                (r"/api/edittable", tables.EditTableHandler),
                (r"/api/tableposition", tables.TablePositionHandler),
                (r"/api/queue", queue.QueueHandler),
                (r"/api/queueplayer", queue.QueuePlayerHandler),
                (r"/api/beginnerqueueplayer", queue.BeginnerQueuePlayerHandler),
                (r"/api/tableplayer", TablePlayerHandler),
                (r"/api/notifyplayer", NotifyPlayerHandler),
                (r"/api/deleteplayer", DeletePlayerHandler),
                (r"/api/editplayer", EditPlayerHandler),
                (r"/api/announcement", announcement.CurrentAnnouncementHandler),
        ]
        settings = dict(
                template_path = os.path.join(os.path.dirname(__file__), "templates"),
                static_path = os.path.join(os.path.dirname(__file__), "static"),
                debug = True,
                cookie_secret = cookie_secret
        )
        tornado.web.Application.__init__(self, handlers, **settings)

def periodic():
    with db.getCur() as cur:
        # cleanup
        cur.execute("DELETE FROM People WHERE Id NOT IN (SELECT PersonId FROM Players) AND Id NOT IN (SELECT Id FROM Queue) AND Id NOT IN (SELECT Id FROM BeginnerQueue);");

        # message players to be seated soon
        cur.execute("SELECT COUNT(*) FROM Tables WHERE NOT Playing OR strftime('%s', datetime('now', 'localtime')) - strftime('%s', Started) > 50 * 60")
        tablecount = cur.fetchone()[0]
        cur.execute("SELECT Phone,Notified,Id FROM People ORDER BY Added LIMIT ?", (tablecount * 4,))
        rows = cur.fetchall()
        client = TwilioRestClient(settings.TWILIO_SID, settings.TWILIO_AUTH)
        texted = []
        for i in [i for i in rows if not i[1] and i[0] and i[0] != ""]:
            try:
                client.messages.create(
                    to=i[0],
                    from_="+14252767908",
                    body="Your mahjong table is opening up in about 10 minutes!",
                )
                log.info("Texted player with ID: " + str(i[2]))
                texted += [i[2]]
            except:
                log.info("Failed to text player with ID: " + str(i[2]))
        if len(texted) > 0:
            placeholder = '?'
            placeholders = ', '.join(placeholder for _ in texted)
            notified = "UPDATE People SET Notified = 1 WHERE Id IN (%s)" % placeholders
            cur.execute(notified, texted)


def main():
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except:
            port = 5000
    else:
        port = 5000

    logging.basicConfig(filename = "mahjong.log", level=logging.INFO)
    logging.getLogger().addHandler(logging.StreamHandler())
    log.info("Server started")
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
