import os

from dotenv import load_dotenv
from espn_api.football import League

load_dotenv()

def get_league():
    league_id = int(os.getenv("ESPN_LEAGUE_ID"))
    year = int(os.getenv("ESPN_YEAR"))
    espn_s2 = os.getenv("ESPN_S2")
    swid = os.getenv("ESPN_SWID")

    if not all([league_id, year, espn_s2, swid]):
        raise ValueError(
            "Missing ESPN configuration. "
            "Check ESPN_LEAGUE_ID, ESPN_YEAR, ESPN_S2, and ESPN_SWID."
        )

    return League(
        league_id=league_id,
        year=year,
        espn_s2=espn_s2,
        swid=swid,
    )
    
def normalize_team_name(name):
    return " ".join(name.lower().split())