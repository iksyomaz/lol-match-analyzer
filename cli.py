import requests
import urllib.parse
import pandas as pd
import sqlite3
import json
import os
from config import API_KEY, REGION, CACHE_DB, load_custom_summoners, save_custom_summoner
from datetime import datetime

def get_summoner_by_riot_id(game_name, tag_line):
    """
    Retrieve account info (including puuid) using the Riot Account API v1.
    This endpoint requires both gameName and tagLine.
    """
    encoded_game_name = urllib.parse.quote(game_name)
    encoded_tag_line = urllib.parse.quote(tag_line)
    url = f"https://{REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{encoded_game_name}/{encoded_tag_line}"
    headers = {"X-Riot-Token": API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def init_db():
    """Initialize the SQLite database and create tables if they do not exist."""
    conn = sqlite3.connect(CACHE_DB)
    c = conn.cursor()

    # Table for raw caching (optional)
    c.execute('''
        CREATE TABLE IF NOT EXISTS timeline (
            match_id TEXT PRIMARY KEY,
            data TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS match_details (
            match_id TEXT PRIMARY KEY,
            data TEXT
        )
    ''')

    # Table for final analysis results (added game_duration for total game time)
    c.execute('''
        CREATE TABLE IF NOT EXISTS analysis (
            summoner_name TEXT,
            match_id TEXT,
            game_datetime TEXT,
            game_duration INTEGER,
            champion TEXT,
            gameMode TEXT,
            minions_at_10 INTEGER,
            kill_participation REAL,
            first_structure_ts REAL,
            assists INTEGER,
            scuttle_crabs INTEGER,
            abilityUses INTEGER,
            total_damage_dealt INTEGER,
            PRIMARY KEY (summoner_name, match_id)
        )
    ''')
    conn.commit()
    conn.close()

def cache_get(table, match_id):
    conn = sqlite3.connect(CACHE_DB)
    c = conn.cursor()
    c.execute(f"SELECT data FROM {table} WHERE match_id = ?", (match_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None

def cache_set(table, match_id, data):
    conn = sqlite3.connect(CACHE_DB)
    c = conn.cursor()
    c.execute(f"REPLACE INTO {table} (match_id, data) VALUES (?, ?)",
              (match_id, json.dumps(data)))
    conn.commit()
    conn.close()

def get_match_timeline(match_id):
    url = f'https://{REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline'
    headers = {'X-Riot-Token': API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_match_details(match_id):
    url = f'https://{REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}'
    headers = {'X-Riot-Token': API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_match_timeline_cached(match_id):
    cached = cache_get("timeline", match_id)
    if cached:
        return cached
    data = get_match_timeline(match_id)
    cache_set("timeline", match_id, data)
    return data

def get_match_details_cached(match_id):
    cached = cache_get("match_details", match_id)
    if cached:
        return cached
    data = get_match_details(match_id)
    cache_set("match_details", match_id, data)
    return data

def get_participant_id_from_timeline(timeline, summoner_puuid):
    for i, p in enumerate(timeline['metadata']['participants']):
        if p == summoner_puuid:
            return i + 1
    return None

def analyze_minions(timeline, summoner_puuid):
    target_time = 600000  # 10 min in ms
    participant_id = get_participant_id_from_timeline(timeline, summoner_puuid)
    chosen_frame = None
    for frame in timeline['info']['frames']:
        if frame['timestamp'] >= target_time:
            chosen_frame = frame
            break
    if chosen_frame is None:
        chosen_frame = timeline['info']['frames'][-1]
    p_frame = chosen_frame['participantFrames'].get(str(participant_id), {})
    return p_frame.get('minionsKilled', 0)

def analyze_kill_participation(match_details, summoner_puuid):
    summoner_stats = None
    team_id = None
    for p in match_details['info']['participants']:
        if p['puuid'] == summoner_puuid:
            summoner_stats = p
            team_id = p['teamId']
            break
    if not summoner_stats:
        return 0
    kills = summoner_stats.get('kills', 0)
    assists = summoner_stats.get('assists', 0)
    team_kills = sum(p.get('kills', 0) for p in match_details['info']['participants'] if p['teamId'] == team_id)
    if team_kills == 0:
        return 0
    return (kills + assists) / team_kills * 100

def analyze_first_structure(timeline, match_details, summoner_puuid):
    summoner_team_id = None
    for p in match_details['info']['participants']:
        if p['puuid'] == summoner_puuid:
            summoner_team_id = p['teamId']
            break
    if summoner_team_id is None:
        return None

    first_ts = None
    for frame in timeline['info']['frames']:
        for event in frame.get('events', []):
            if event['type'] == 'BUILDING_KILL':
                killer_id = event.get('killerId')
                if killer_id is None:
                    continue
                # find killer's team
                killer_team_id = None
                for participant in match_details['info']['participants']:
                    if participant['participantId'] == killer_id:
                        killer_team_id = participant['teamId']
                        break
                if killer_team_id == summoner_team_id:
                    t = event.get('timestamp')
                    if t is not None:
                        if first_ts is None or t < first_ts:
                            first_ts = t
    return first_ts

def analyze_assists(match_details, summoner_puuid):
    for p in match_details['info']['participants']:
        if p['puuid'] == summoner_puuid:
            return p.get('assists', 0)
    return 0

def analyze_scuttle_crabs(match_details, summoner_puuid):
    # Use participant challenges for scuttle crab kills.
    for p in match_details['info']['participants']:
        if p['puuid'] == summoner_puuid:
            challenges = p.get('challenges', {})
            return challenges.get('scuttleCrabKills', 0)
    return 0

def analyze_ability_uses(match_details, summoner_puuid):
    for p in match_details['info']['participants']:
        if p['puuid'] == summoner_puuid:
            challenges = p.get('challenges', {})
            return challenges.get('abilityUses', 0)
    return 0

def analyze_total_damage(match_details, summoner_puuid):
    for p in match_details['info']['participants']:
        if p['puuid'] == summoner_puuid:
            return p.get('totalDamageDealtToChampions', 0)
    return 0

def get_champion(match_details, summoner_puuid):
    for p in match_details['info']['participants']:
        if p['puuid'] == summoner_puuid:
            return p.get('championName', 'Unknown')
    return 'Unknown'

def get_game_mode(match_details):
    queue_id = match_details['info'].get('queueId', 0)
    mapping = {
        400: "Normal Draft",
        430: "Normal Blind",
        420: "Ranked Solo",
        440: "Ranked Flex",
        450: "ARAM",
        700: "Clash"
    }
    return mapping.get(queue_id, match_details['info'].get('gameMode', 'Unknown'))



def store_analysis_result(summoner_name, match_id, game_datetime, game_duration,
                          champion, game_mode,
                          minions_at_10, kill_part, first_struct,
                          assists, scuttles, ability_uses, total_damage):
    """
    Store the final per-match stats in the 'analysis' table.
    If the row already exists for (summoner_name, match_id), it is replaced.
    """
    conn = sqlite3.connect(CACHE_DB)
    c = conn.cursor()
    c.execute('''
        REPLACE INTO analysis (
            summoner_name, match_id, game_datetime, game_duration, champion, gameMode,
            minions_at_10, kill_participation, first_structure_ts,
            assists, scuttle_crabs, abilityUses, total_damage_dealt
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        summoner_name,
        match_id,
        game_datetime,
        game_duration,
        champion,
        game_mode,
        minions_at_10,
        kill_part,
        first_struct if first_struct else 0,
        assists,
        scuttles,
        ability_uses,
        total_damage
    ))
    conn.commit()
    conn.close()

def get_analysis_data_for_summoner(summoner_name):
    """
    Returns a Pandas DataFrame of the 'analysis' table rows for the given summoner_name.
    """
    conn = sqlite3.connect(CACHE_DB)
    df = pd.read_sql_query(
        "SELECT * FROM analysis WHERE summoner_name = ?",
        conn,
        params=(summoner_name,)
    )
    conn.close()
    return df

# -- Helper functions for final display formatting --

def format_game_duration(seconds):
    """Convert total game time in seconds to mm:ss format."""
    if not seconds or seconds < 0:
        return "0:00"
    mm = seconds // 60
    ss = seconds % 60
    return f"{mm}:{ss:02d}"

def format_first_structure_ts(ms):
    """Convert first-structure timestamp from ms to ss:ms format (e.g. 708.801 -> 708:801)."""
    if ms is None or ms <= 0:
        return "N/A"
    total_ms = int(ms)
    s = total_ms // 1000
    remain_ms = total_ms % 1000
    return f"{s}:{remain_ms:03d}"

def format_kill_participation(value):
    """Round to two decimals and append '%'."""
    return f"{value:.2f}%"

def get_all_summoners_from_db():
    conn = sqlite3.connect("riot_cache.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT summoner_name FROM analysis")
    results = cursor.fetchall()
    conn.close()
    return sorted(set(row[0] for row in results))

def main():
    init_db()

    summoners = load_custom_summoners()

    print("Select summoner to analyze:")
    summoner_keys = list(summoners.keys())
    for idx, key in enumerate(summoner_keys, 1):
        print(f" {idx}: {summoners[key]['name']}")
    print(f" {len(summoner_keys) + 1}: Enter summoner by Riot ID (gameName and tagLine)")

    choice = input("Enter summoner number: ").strip()

    if choice == str(len(summoner_keys) + 1):
        game_name = input("Enter summoner gameName: ").strip()
        tag_line = input("Enter summoner tagLine: ").strip()
        try:
            summoner_data = get_summoner_by_riot_id(game_name, tag_line)
            puuid = summoner_data["puuid"]
            summoner_name = summoner_data["gameName"]
            save_custom_summoner(summoner_name, puuid)
        except Exception as e:
            print("Error retrieving summoner data:", e)
            return
    else:
        try:
            idx = int(choice) - 1
            selected = summoners[summoner_keys[idx]]
            puuid = selected["puuid"]
            summoner_name = selected["name"]
        except (IndexError, ValueError):
            print("Invalid choice.")
            return

    # Determine how many recent matches to analyze
    count = int(input("How many recent games to analyze?: "))

    # Retrieve match IDs
    url = f'https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}'
    headers = {'X-Riot-Token': API_KEY}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    match_ids = resp.json()

    for mid in match_ids:
        print(f"Analyzing match {mid} ...")
        # Retrieve from cache or API
        timeline = get_match_timeline_cached(mid)
        match_details = get_match_details_cached(mid)

        # Extract data
        minions_10 = analyze_minions(timeline, puuid)
        kill_part = analyze_kill_participation(match_details, puuid)
        first_struct = analyze_first_structure(timeline, match_details, puuid)
        assists = analyze_assists(match_details, puuid)
        scuttles = analyze_scuttle_crabs(match_details, puuid)
        ability_uses = analyze_ability_uses(match_details, puuid)
        total_damage = analyze_total_damage(match_details, puuid)
        champion = get_champion(match_details, puuid)
        game_mode = get_game_mode(match_details)
        # Extract game duration from match details (assumed to be in seconds)
        game_duration = match_details['info'].get('gameDuration', 0)

        # Convert timestamp to human-readable date
        game_dt = match_details['info'].get('gameStartTimestamp', 0)
        game_dt_readable = datetime.fromtimestamp(game_dt / 1000).strftime("%Y-%m-%d %H:%M:%S")

        store_analysis_result(
            summoner_name,
            mid,
            game_dt_readable,
            game_duration,
            champion,
            game_mode,
            minions_10,
            kill_part,
            first_struct if first_struct else 0,
            assists,
            scuttles,
            ability_uses,
            total_damage
        )

    # Retrieve and show analysis results
    df = get_analysis_data_for_summoner(summoner_name)

    # -- Final formatting before printing --
    if not df.empty:
        # Format game_duration as mm:ss
        df['game_duration'] = df['game_duration'].apply(format_game_duration)
        # Format first_structure_ts as ss:ms
        df['first_structure_ts'] = df['first_structure_ts'].apply(format_first_structure_ts)
        # Format kill_participation to two decimals plus '%'
        df['kill_participation'] = df['kill_participation'].apply(format_kill_participation)

        # Rename columns for better readability
        df.rename(columns={
            'summoner_name': 'Summoner',
            'match_id': 'Match ID',
            'game_datetime': 'Date & Time',
            'game_duration': 'Duration',
            'champion': 'Champion',
            'gameMode': 'Mode',
            'minions_at_10': 'Minions @10',
            'kill_participation': 'KP%',
            'first_structure_ts': '1st Tower',
            'assists': 'Assists',
            'scuttle_crabs': 'Crabs',
            'abilityUses': 'Abilities',
            'total_damage_dealt': 'Damage'
        }, inplace=True)

    print("\nAnalysis results from 'analysis' table:")
    print(df.to_string(index=False))

if __name__ == "__main__":
    main()
