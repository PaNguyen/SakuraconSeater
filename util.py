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

def prompt(msg, default=None):
    resp = None
    accepted_responses = ['y', 'Y', 'yes', 'Yes', 'n', 'N', 'no', 'No']
    guide = "[y/n]"
    if default and default in accepted_responses:
        accepted_responses.append('')
        guide = "[Y/n]" if default.lower().startswith('y') else "[y/N]"
    while resp not in accepted_responses:
        resp = input("{0} {1}? ".format(msg, guide))
        if resp not in accepted_responses:
            print("Unrecognized response, '{0}'.\nPlease choose among {1}".
                  format(resp, accepted_responses))
    return (resp.lower().startswith('y') if len(resp) > 0 or default == None
            else default.lower().startswith('y'))
