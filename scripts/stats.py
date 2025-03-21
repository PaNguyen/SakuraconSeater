#!/usr/bin/env python

import sqlite3
import argparse
import json
import pandas as pd
from datetime import datetime

parser = argparse.ArgumentParser(
    prog="stats",
    description="Gets helpful stats"
)
parser.add_argument('db_filename')
parser.add_argument('-x', '--excel' , default='stats.xlsx')
args = parser.parse_args()
db_file = args.db_filename
excel_file = args.excel
print(excel_file)

con = sqlite3.connect(db_file)
cur = con.cursor()
res = cur.execute("SELECT * FROM Events ORDER BY time ASC;").fetchall()

tables: dict[int, dict[str, any]] = {} # table_id -> {id, name, time_created, table_type, players}
players: dict[int, dict[str, any]] = {} # player_id -> {id, name, table_type, num_players, time_added_to_queue, table_start_time, table_clear_time, time_deleted}
table_stats = []
player_stats = []
for (event_type, time, data) in res:
    print(event_type, time, data)
    if event_type == 'start':
        pass
    elif event_type == 'tablecreate':
        table_id = int(json.loads(data))
        if table_id in tables:
            print(f"WARNING overwriting table {table_id}")
        tables[table_id] = {'id': table_id, 'name': '', 'time_created': time, 'table_type': "default", 'players': []}
        pass
    elif event_type == 'tabledelete':
        print(f"WARNING tabledelete({table_id}) encountered")
        table_id = int(json.loads(data))
        del tables[table_id]
        pass
    elif event_type == 'tableretype':
        table_id, table_type = json.loads(data)
        tables[int(table_id)]['table_type'] = table_type
    elif event_type == 'playerqueueadd':
        player_id, name, table_type, num_players = json.loads(data)
        if player_id in players:
            print(f"WARNING overwriting player {player_id}")
            for tid in tables:
                if player_id in tables[tid]['players']:
                    print(f"Removing player {player_id} from table {tid}")
                    tables[tid]['players'].remove(player_id)
        # TODO is num_players worth tracking since players are also split into separate entries?
        players[player_id] = {'id': player_id, 'name': name, 'table_type': table_type, 'num_players': num_players, 'time_added_to_queue': time}
        pass
    elif event_type == 'playermovetotable':
        player_id, table_id = json.loads(data)
        player_id = int(player_id)
        table_id = int(table_id)
        for tid in tables:
            if player_id in tables[tid]['players']:
                tables[tid]['players'].remove(player_id)
        if player_id not in tables[table_id]['players']:
            tables[table_id]['players'].append(player_id)
            players[player_id]['time_added_to_table'] = time
            players[player_id]['table_added_to'] = table_id
        else:
            print(f"WARNING player {player_id} already in table {table_id}")
        pass
    elif event_type == 'tablestart':
        table_id = int(json.loads(data))
        tables[table_id]['time_start'] = time
        for player_id in tables[table_id]['players']:
            if player_id in players:
                players[player_id]['table_start_time'] = time
                players[player_id]['table_clear_time'] = None
        pass
    elif event_type == 'tableclear':
        table_id = int(json.loads(data))
        table = tables[table_id]
        if table['time_start'] is None:
            continue
        table['time_end'] = time
        for player_id in table['players']:
            # if player_id in players:
                players[player_id]['table_clear_time'] = time
                player_stats.append(players[player_id].copy())
                players[player_id]['table_start_time'] = None
                players[player_id]['table_clear_time'] = None
        table_stats.append(tables[table_id].copy())
        table['players'] = []
        table['time_start'] = None
        table['time_end'] = None
        pass
    elif event_type == 'playerdelete':
        player_id = int(json.loads(data))
        for table_id in tables:
            if player_id in tables[table_id]['players']:
                tables[table_id]['players'].remove(player_id)
        if player_id in players:
            players[player_id]['time_deleted'] = time
            player_stats.append(players[player_id].copy())
            del players[player_id]
        pass
    elif event_type == 'tablerename':
        table_id, table_name = json.loads(data)
        tables[int(table_id)]['name'] = table_name
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
print(json.dumps(player_stats))

def to_dataframe(arr, columns):
    data = {}
    for c in columns:
        data[c] = []
    for a in arr:
        for c in columns:
            if c in a:
                data[c].append(a[c])
            else:
                data[c].append(None)
    return pd.DataFrame(data)
def convert_datetime(df, columns):
    for c in columns:
        df[c] = pd.to_datetime(df[c])

raw_df = pd.DataFrame(res, columns=['event', 'time', 'data'])

table_df_cols = ["id", "table_type", "players", "time_start", "time_end"]
# Omitting time_created because it's not useful
table_df = to_dataframe(table_stats, table_df_cols)
convert_datetime(table_df, ['time_start', 'time_end'])

player_df_cols = ["id", "name", "table_type", "time_added_to_queue", "time_added_to_table", "table_added_to", "table_start_time", "table_clear_time", "time_deleted"]
player_df = to_dataframe(player_stats, player_df_cols)
convert_datetime(player_df, ['time_added_to_queue', 'time_added_to_table', 'table_start_time', 'table_clear_time', 'time_deleted'])

# Table stats by hour
table_hour_grouping = table_df.groupby([pd.Grouper(key='time_start', freq='h'), 'table_type'])
table_hour_df = table_hour_grouping.count()
table_hour_df = table_hour_df.rename(columns={'id': 'Number Started'})
table_hour_df = table_hour_df.rename_axis(['Times', 'Table Type'])
table_hour_df = table_hour_df.drop(columns=table_df_cols, errors='ignore')

# Table stats by table type
table_type_grouping = table_df.groupby('table_type')
durations = table_type_grouping.apply(lambda group: group['time_end'].sub(group['time_start']).mean().total_seconds() / 60, include_groups=False)
durations.name = 'Avg Duration (mins)'
table_stats_df = pd.DataFrame(durations).rename_axis('Table Type')

# Player stats by hour
player_hour_grouping = player_df.groupby([pd.Grouper(key='time_added_to_queue', freq='h'), 'table_type'])
player_hour_df = player_hour_grouping.count()
player_hour_df = player_hour_df.rename(columns={'id': 'Number Queued', 'time_added_to_table': 'Number Seated', 'time_deleted': 'Number Unqueued'})
player_hour_df = player_hour_df.rename_axis(['Times', 'Table type'])
player_hour_df = player_hour_df.drop(columns=player_df_cols, errors='ignore')


with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
    raw_df.to_excel(writer, sheet_name='Raw Events', index=False)
    table_df.to_excel(writer, sheet_name='Table Data', index=False)
    player_df.to_excel(writer, sheet_name='Player Data', index=False)
    table_hour_df.to_excel(writer, sheet_name='Table Stats by Hour')
    table_stats_df.to_excel(writer, sheet_name='Table Stats by Type')
    player_hour_df.to_excel(writer, sheet_name='Player Stats By Hour')
