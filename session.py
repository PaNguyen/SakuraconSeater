#!/usr/bin/env python2.7

import string
import random
import tornado.web
import db
import hashlib
import datetime
import util
from passlib.hash import pbkdf2_sha256

import settings

def login(cookie, password):
    with db.getCur() as cur:
        if pbkdf2_sha256.verify(password, settings.PASSWORD):
            cur.execute("REPLACE INTO Sessions(Id, Expires) VALUES(?, ?)", (cookie, (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat()))
            return True
    return False

def loggedIn(cookie):
	with db.getCur() as cur:
		cur.execute("SELECT EXISTS(SELECT * FROM Sessions WHERE Id = ? AND Expires > datetime('now'))", (cookie,))
		return cur.fetchone()[0] == 1

def getSession(self):
	cookie = self.get_secure_cookie('session-id')

	if cookie is None:
		cookie = newCookie()
		self.set_secure_cookie('session-id', cookie)

	return cookie


def newCookie():
	return util.randString(16)
