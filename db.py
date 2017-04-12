#!/usr/bin/env python3

import warnings
import sqlite3
import random

class getCur():
    con = None
    cur = None
    def __enter__(self):
        self.con = sqlite3.connect("tables.db", detect_types=sqlite3.PARSE_DECLTYPES)
        self.con.execute("PRAGMA foreign_keys = ON")
        self.cur = self.con.cursor()
        return self.cur
    def __exit__(self, type, value, traceback):
        if self.cur and self.con and not value:
            self.cur.close()
            self.con.commit()
            self.con.close()

        return False

class getCon():
    con = None
    def __enter__(self):
        self.con = sqlite3.connect("tables.db", detect_types=sqlite3.PARSE_DECLTYPES)
        self.con.execute("PRAGMA foreign_keys = ON")
        return self.con
    def __exit__(self, type, value, traceback):
        if self.con and not value:
            self.con.commit()
            self.con.close()

            return False

def init():
    warnings.filterwarnings('ignore', r'Table \'[^\']*\' already exists')

    with getCur() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS TableTypes(Type VARCHAR(255) PRIMARY KEY NOT NULL, Duration INTEGER, Players INTEGER);")

        cur.execute("CREATE TABLE IF NOT EXISTS Tables(Id INTEGER PRIMARY KEY NOT NULL, \
                Name VARCHAR(255) NOT NULL, \
                Playing BOOLEAN NOT NULL, \
                x INTEGER, y INTEGER, \
                Type VARCHAR(255) NOT NULL, \
                Started TIMESTAMP, \
                FOREIGN KEY (Type) REFERENCES TableTypes(Type));")

        cur.execute("CREATE TABLE IF NOT EXISTS People(Id INTEGER PRIMARY KEY NOT NULL, \
                Name VARCHAR(255) NOT NULL, \
                Phone VARCHAR(255) DEFAULT NULL, \
                Notified BOOLEAN NOT NULL DEFAULT 0,\
                Added TIMESTAMP NOT NULL)")

        cur.execute("CREATE TABLE IF NOT EXISTS Players(Id INTEGER PRIMARY KEY NOT NULL, \
                TableId INTEGER NOT NULL, \
                PersonId INTEGER NOT NULL, \
                FOREIGN KEY(TableId) REFERENCES Tables(Id) ON DELETE CASCADE, \
                FOREIGN KEY(PersonId) REFERENCES People(Id) ON DELETE CASCADE);")

        cur.execute("CREATE TABLE IF NOT EXISTS Queue(Id INTEGER PRIMARY KEY NOT NULL, \
                Type VARCHAR(255) NOT NULL,\
                FOREIGN KEY(Type) REFERENCES TableTypes(Type) ON DELETE CASCADE, \
                FOREIGN KEY(Id) REFERENCES People(Id) ON DELETE CASCADE);")

        cur.execute("CREATE TABLE IF NOT EXISTS Sessions(Id CHAR(16) PRIMARY KEY NOT NULL, \
                Expires DATE)")

        cur.execute("CREATE TABLE IF NOT EXISTS Messages(Message VARCHAR(255) NOT NULL, \
                Date DATE)")
