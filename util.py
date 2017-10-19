#!/usr/bin/env python2.7

import random
import string

# convert timedelta object to # of seconds
def get_total_seconds(td):
	return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 1e6) / 1e6

def timeString(time):
    if time == 0:
        return "NOW"
    time = int(time / 60)
    minutes = time % 60
    hours = int(time / 60)
    return ("0" + str(hours))[-2:] + ":" + ("0" + str(minutes))[-2:]

def randString(length):
	return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for x in range(length))
