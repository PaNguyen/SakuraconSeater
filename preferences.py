#!/usr/bin/env python3

import tornado.web
import json

import db

class PreferencesHandler(tornado.web.RequestHandler):
    def get(self):
        result = { 'status': "error",
                    'data': {}}
        with db.getCur() as cur:
            cur.execute("SELECT Key, Val FROM Preferences")
            rows = cur.fetchall()
            for row in rows:
                result["data"][row[0]] =  row[1];
            result["status"] = "success"
        self.write(json.dumps(result))
    def post(self):
        result = { 'status': "error",
                    'message': "Unknown error occurred"}
        preferences = self.get_argument("preferences", None)
        if preferences is not None:
            preferences = json.loads(preferences)
            print(preferences)
            if len(preferences.keys()) > 0:
                with db.getCur() as cur:
                    query = "DELETE FROM Preferences WHERE Key IN ("
                    query += "?"
                    query += ", ?" * (len(preferences.keys())  -  1)
                    query += ")"
                    args = preferences.keys()
                    cur.execute(query, args)
                    args = []
                    query = "INSERT INTO Preferences(Key, Val) VALUES"
                    query += "(?, ?)"
                    query += ", (?, ?)" * (len(preferences.keys())  -  1)
                    for key,val in  preferences.iteritems():
                        args += [key]
                        args += [val]
                    print(query)
                    print(args)
                    cur.execute(query, args)
                result = { 'status': "success",
                            'message': "Preferences updated"}
        self.write(json.dumps(result))

class PreferenceHandler(tornado.web.RequestHandler):
    def get(self, q):
        result = { 'status': "success",
                    'value': getPreference(q)}
        self.write(json.dumps(result))

def getPreference(key):
    with db.getCur() as  cur:
        cur.execute("SELECT Val FROM Preferences WHERE Key = ?", (key,))
        row = cur.fetchone()
        if row is not None:
            return row[0]
        else:
            return None
