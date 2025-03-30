import os
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("RIOT_API_KEY")
REGION = 'europe'
CACHE_DB = "riot_cache.db"
CUSTOM_SUMMONERS_FILE = "custom_summoners.json"

def load_custom_summoners():
    if not os.path.exists(CUSTOM_SUMMONERS_FILE):
        return {}
    with open(CUSTOM_SUMMONERS_FILE, 'r') as f:
        return json.load(f)

def save_custom_summoner(name, puuid):
    custom = load_custom_summoners()
    if name not in custom:
        custom[name] = {"name": name, "puuid": puuid}
        with open(CUSTOM_SUMMONERS_FILE, 'w') as f:
            json.dump(custom, f, indent=2)


API_KEY = ''
REGION = 'europe'
CACHE_DB = "riot_cache.db"