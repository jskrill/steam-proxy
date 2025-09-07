import time
import requests
import cachetools.func
from fastapi import FastAPI, HTTPException

STEAM_API_ROOT = "https://api.steampowered.com"

app = FastAPI()

@cachetools.func.ttl_cache(maxsize=128, ttl=300, timer=time.monotonic, typed=False)
def _get_owned_games(key: str, steamid: str, include_appinfo: int = 0, include_played_free_games: int = 0, skip_unvetted_apps: int = 0, format: str = "json"):
    resp = requests.get(f"{STEAM_API_ROOT}/IPlayerService/GetOwnedGames/v0001/", params={
        "key": key,
        "steamid": steamid,
        "include_appinfo": include_appinfo,
        "include_played_free_games": include_played_free_games,
        "skip_unvetted_apps": skip_unvetted_apps,
        "format": format,
    })
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"Error from SteamAPI: {resp.content}")
    data = resp.json()
    return data


@app.get("/IPlayerService/GetOwnedGames/v0001/")
async def get_owned_games(
    key: str,
    steamid: str,
    include_appinfo: int = 0,
    include_played_free_games: int = 0,
    skip_unvetted_apps: int = 0,
    format: str = "json",
    page: int = 1,
    limit: int = 100,
):
    data = _get_owned_games(key=key, steamid=steamid, include_appinfo=include_appinfo, include_played_free_games=include_played_free_games, skip_unvetted_apps=skip_unvetted_apps, format=format)
    total_game_count = data["response"].get("game_count", 0)
    games = data["response"].get("games", [])[(page-1)*limit:page*limit]
    return {
        "pagination": {
            "total_games_count": total_game_count,
            "page": page,
            "total_pages": (((total_game_count - 1) // limit) + 1),
            "limit": limit,
        },
        "results": games,
    }

if __name__ == "__main__":
    app()
