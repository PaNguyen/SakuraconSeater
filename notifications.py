#!/usr/bin/env python3

from twilio.rest import Client
import tornado.web

import sys

import settings
import events
import db

def sendNotifications():
    with db.getCur() as cur:
        # message players to be seated soon
        cur.execute(
            "SELECT Tables.Type, TableTypes.Players, COUNT(*) FROM Tables "
            " INNER JOIN TableTypes ON Tables.Type = TableTypes.Type "
            " WHERE "
            " (ScheduledStart IS NULL AND (NOT Playing OR"
            "   strftime('%s', datetime('now', 'localtime')) - strftime('%s', Started) > 60 * (TableTypes.Duration - ?))) "
            " OR (ScheduledStart IS NOT NULL AND strftime('%s', ScheduledStart) - strftime('%s', datetime('now', 'localtime')) < ?) "
            " GROUP BY Tables.Type ",
            (settings.NOTIFY_MINUTES, settings.NOTIFY_MINUTES)
        )
        tablecounts = cur.fetchall()
        playersToNotify = []
        for tabletype, count, playercount in tablecounts:
            cols = ['Id', 'Phone', 'Notified']
            cur.execute(
                "SELECT {cols} FROM Queue "
                " INNER JOIN People ON Queue.Person = People.Id "
                " WHERE Queue.Type = ? "
                " ORDER BY Added LIMIT ?".format(cols=",".join(cols)),
                (tabletype, count * playercount)
            )
            playersToNotify += [dict(zip(cols, row)) for row in cur.fetchall()]
    playersToNotify = [row for row in playersToNotify if not row['Notified'] and row['Phone'] and row['Phone'] != ""]
    if settings.TWILIO_SID != "" and settings.TWILIO_AUTH != "" and settings.TWILIO_NUMBER != "":
        try:
            client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH)
            texted = []
            for player in playersToNotify:
                try:
                    message=settings.TEXT_FMT.format("in about {} minutes!".format(settings.NOTIFY_MINUTES))
                    client.messages.create(
                        to=player['Phone'],
                        from_=settings.TWILIO_NUMBER,
                        body=message
                    )
                    events.logEvent("textsent", player['Id'])
                    texted += [(player['Id'],)]
                except:
                    print("Error sending Twilio message: ", sys.exc_info()[0])
                    events.logEvent("textfailed", player['Id'])
            if len(texted) > 0:
                with db.getCur() as cur:
                    cur.executemany("UPDATE People SET Notified = 1 WHERE Id = ?", texted)
        except:
            print("Error sending Twilio message: ", sys.exc_info()[0])
            events.logEvent("twiliofailed")

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
            client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH)

            try:
                client.messages.create(
                    to=phone,
                    from_="+14252767908",
                    body="Your mahjong table is opening up soon!",
                )
                result["status"] = "success"
                result["message"] = "Notified player"
                events.logEvent("textsent", player)
            except:
                events.logEvent("textfailed", player)
                result["message"] = "Failed to notify player"
        self.write(json.dumps(result))

class NotifyTableHandler(tornado.web.RequestHandler):
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        table = self.get_argument("table", None)
        if table is not None:
            with db.getCur() as cur:
                cur.execute("SELECT Phone FROM People INNER JOIN Players ON PersonId = People.Id WHERE TableId = ?", (table,))
                client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH)
                phones = 0
                for phone in cur.fetchall():
                    phone = phone[0]
                    if phone is not None and phone != "":
                        message = settings.TEXT_FMT.format("soon!")
                        client.messages.create(
                            to=phone,
                            from_=settings.TWILIO_NUMBER,
                            body=message,
                        )
                        phones += 1
            result["status"] = "success"
            result["message"] = "Notified " + str(phones) + " players"
            events.logEvent('tablenotify', (table, phones))
        self.write(json.dumps(result))

