import sqlite3
import json
import pandas as pd

CACHE_DB = "riot_cache.db"

def get_timeline_table():
    """
    Returns a DataFrame with a few selected columns from the 'timeline' table.
    Adjust or expand the extracted fields as needed.
    """
    conn = sqlite3.connect(CACHE_DB)
    c = conn.cursor()
    c.execute("SELECT match_id, data FROM timeline")
    rows = c.fetchall()
    conn.close()

    data_list = []
    for match_id, data_str in rows:
        data_json = json.loads(data_str)

        # Extract some sample fields from the JSON
        metadata_match_id = data_json.get("metadata", {}).get("matchId", None)
        frames = data_json.get("info", {}).get("frames", [])
        frames_count = len(frames)

        data_list.append({
            "db_match_id": match_id,
            "metadata.matchId": metadata_match_id,
            "frames_count": frames_count
        })

    df = pd.DataFrame(data_list)
    return df

def get_match_details_table():
    """
    Returns a DataFrame with a few selected columns from the 'match_details' table.
    Adjust or expand the extracted fields as needed.
    """
    conn = sqlite3.connect(CACHE_DB)
    c = conn.cursor()
    c.execute("SELECT match_id, data FROM match_details")
    rows = c.fetchall()
    conn.close()

    data_list = []
    for match_id, data_str in rows:
        data_json = json.loads(data_str)

        # Extract some sample fields from the JSON
        metadata_match_id = data_json.get("metadata", {}).get("matchId", None)
        info = data_json.get("info", {})
        game_id = info.get("gameId", None)
        queue_id = info.get("queueId", None)
        game_duration = info.get("gameDuration", None)

        data_list.append({
            "db_match_id": match_id,
            "metadata.matchId": metadata_match_id,
            "gameId": game_id,
            "queueId": queue_id,
            "gameDuration": game_duration
        })

    df = pd.DataFrame(data_list)
    return df

def show_all_data():
    """
    Example function that retrieves data from both tables and prints them out.
    """
    df_timeline = get_timeline_table()
    df_details = get_match_details_table()

    print("Timeline Table:")
    print(df_timeline.to_string(index=False))
    print("\nMatch Details Table:")
    print(df_details.to_string(index=False))

if __name__ == "__main__":
    # Just run the display function
    show_all_data()
