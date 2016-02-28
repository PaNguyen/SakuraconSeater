#!/usr/bin/env python2.7

import random
import string

# convert timedelta object to # of seconds
def get_total_seconds(td):
	return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 1e6) / 1e6

def secondsToEnglish(seconds):
	if seconds >= 60 * 60 * 24 * 365.25:
		seconds = seconds / (60 * 60 * 24 * 365.25)
		unit = "year"
	elif seconds >= 60 * 60 * 24 * 30.4375:
		seconds = seconds / (60 * 60 * 24 * 30.4375)
		unit = "month"
	elif seconds >= 60 * 60 * 24 * 7:
		seconds = seconds / (60 * 60 * 24 * 7)
		unit = "week"
	elif seconds >= 60 * 60 * 24:
		seconds = seconds / (60 * 60 * 24)
		unit = "day"
	elif seconds >= 60 * 60:
		seconds = seconds / (60 * 60)
		unit = "hour"
	elif seconds >= 60:
		seconds = seconds / (60)
		unit = "minute"
	else:
		seconds = seconds
		unit = "second"

	seconds = round(seconds, 1)

	if seconds == 1:
		seconds = str(seconds) + " " + unit
	else:
		seconds = str(seconds) + " " + unit + "s"

	return seconds

def randString(length):
	return ''.join(random.SystemRandom().choice(string.letters + string.digits) for x in range(length))
