from flask import Flask, render_template, request
from main import (
    get_summoner_by_riot_id, get_analysis_data_for_summoner,
    init_db, get_match_timeline_cached, get_match_details_cached,
    analyze_minions, analyze_kill_participation, analyze_first_structure,
    analyze_assists, analyze_scuttle_crabs, analyze_ability_uses,
    analyze_total_damage, get_champion, get_game_mode,
    store_analysis_result
)
from datetime import datetime
from config import API_KEY, load_custom_summoners, save_custom_summoner
import pandas as pd
import requests
import sqlite3

app = Flask(__name__)

def get_all_summoners_from_db():
    conn = sqlite3.connect("riot_cache.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT summoner_name FROM analysis")
    results = cursor.fetchall()
    conn.close()

    return sorted(set(row[0] for row in results))

@app.route('/', methods=['GET', 'POST'])
def index():
    result_table = None
    error = None
    dropdown_summoners = load_custom_summoners()

    if request.method == 'POST':
        count = int(request.form.get('count', 3))
        manual_mode = request.form.get('manual_mode') == 'on'

        try:
            init_db()

            if manual_mode:
                game_name = request.form.get('game_name', '').strip()
                tag_line = request.form.get('tag_line', '').strip()
                if not game_name or not tag_line:
                    raise ValueError("Missing Riot ID (gameName and tagLine).")
                summoner_data = get_summoner_by_riot_id(game_name, tag_line)
                puuid = summoner_data["puuid"]
                summoner_name = summoner_data["gameName"]
                save_custom_summoner(summoner_name, puuid)
                dropdown_summoners[summoner_name] = {"name": summoner_name, "puuid": puuid}
            else:
                puuid = request.form.get('puuid')
                summoner_name = request.form.get('summoner_name')

                if not puuid or not summoner_name:
                    raise ValueError("Invalid summoner selected.")

                if not puuid:
                    # Try to fetch puuid using Riot ID if it's missing (from DB summoners)
                    raise ValueError(f"No puuid available for {summoner_name}. Please analyze manually first.")

            # Get match list
            url = f'https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}'
            headers = {'X-Riot-Token': API_KEY}
            match_ids = requests.get(url, headers=headers).json()

            for mid in match_ids:
                timeline = get_match_timeline_cached(mid)
                match_details = get_match_details_cached(mid)

                minions_10 = analyze_minions(timeline, puuid)
                kill_part = analyze_kill_participation(match_details, puuid)
                first_struct = analyze_first_structure(timeline, match_details, puuid)
                assists = analyze_assists(match_details, puuid)
                scuttles = analyze_scuttle_crabs(match_details, puuid)
                ability_uses = analyze_ability_uses(match_details, puuid)
                total_damage = analyze_total_damage(match_details, puuid)
                champion = get_champion(match_details, puuid)
                game_mode = get_game_mode(match_details)
                game_duration = match_details['info'].get('gameDuration', 0)
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

            df = get_analysis_data_for_summoner(summoner_name)
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

            result_table = df.to_html(classes="table table-bordered", index=False, border=0, justify="center")

        except Exception as e:
            error = str(e)

    # After form POST or normal GET, load extra names from DB
    try:
        db_names = get_all_summoners_from_db()
        for name in db_names:
            if name not in dropdown_summoners:
                dropdown_summoners[name] = {"name": name, "puuid": None}
    except Exception:
        pass

    return render_template("index.html", summoners=dropdown_summoners, result=result_table, error=error)

if __name__ == '__main__':
    app.run(debug=True)
