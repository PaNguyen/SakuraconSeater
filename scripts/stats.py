#!/usr/bin/env python

import sqlite3
import argparse
import json

parser = argparse.ArgumentParser(
    prog="stats",
    description="Gets helpful stats"
)
parser.add_argument('db_filename')
parser.add_argument('-c', '--csv' , default='stats.csv')
args = parser.parse_args()

con = sqlite3.connect(args.db_filename)
cur = con.cursor()

session = 0
tables: dict[int, dict[str, any]] = {}
players: dict[str, dict[str, any]] = {} # players ID'ed by session and id within a session
table_stats = []
for (event_type, time, data) in cur.execute("SELECT * FROM Events ORDER BY time ASC;"):
    print(event_type, time, data)
    if event_type == 'start':
        session = session + 1
        pass
    elif event_type == 'tablecreate':
        table_id = int(json.loads(data))
        if table_id in tables:
            print(f"WARNING overwriting table {table_id}")
        tables[table_id] = {'id': table_id, 'time_created': time, 'players': []}
        pass
    elif event_type == 'tabledelete':
        print(f"WARNING tabledelete({table_id}) encountered")
        table_id = int(json.loads(data))
        del tables[table_id]
        pass
    elif event_type == 'playerqueueadd':
        id, name, table_type, num_players = json.loads(data)
        player_id = f"{session}_{id}"
        if player_id in players:
            print(f"ERROR duplicate player {player_id}")
        # TODO is num_players worth tracking since players are also split into separate entries?
        players[player_id] = {'id': player_id, 'name': name, 'table_type': table_type, 'num_players': num_players, 'time_added_to_queue': time}
        pass
    elif event_type == 'playermovetotable':
        id, table_id = json.loads(data)
        player_id = f"{session}_{id}"
        table_id = int(table_id)
        tables[table_id]['players'].append(player_id)
        players[player_id]['time_added_to_table'] = time
        pass
    elif event_type == 'tablestart':
        table_id = int(json.loads(data))
        tables[table_id]['time_start'] = time
        pass
    elif event_type == 'tableclear':
        table_id = int(json.loads(data))
        table = tables[table_id]
        table['time_end'] = time
        table_stats.append(tables[table_id].copy())
        table['players'] = []
        del table['time_start']
        del table['time_end']
        pass
    elif event_type == 'playerdelete':
        id = json.loads(data)
        player_id = f"{session}_{id}"
        print(str(players))
        if player_id in players:
            players[player_id]['time_deleted'] = time
        pass
    elif event_type == 'tablefill':
        # TODO what is this?
        pass
    elif event_type == 'playerqueuemove':
        # TODO what is this?
        pass
    elif event_type == 'tableschedule':
        pass
    else:
        print(f"WARNING Unknown event {event_type}")

print(json.dumps(table_stats))
print(json.dumps(players))
