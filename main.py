import time
import requests
import cachetools.func
from pydantic import BaseModel
from typing import Generic, TypeVar
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import APIKeyHeader
from typing_extensions import Annotated

STEAM_API_ROOT = "https://api.steampowered.com"

app = FastAPI(
    title="Steam API Wrapper",
    summary="A FastAPI wrapper for the Steam API",
)

api_key_scheme = APIKeyHeader(name="x-Api-Key")

PageItem = TypeVar('PageItem')

class PaginationMeta(BaseModel):
    total_count: int
    limit: int
    page: int
    total_pages: int

class PaginatedResponse(BaseModel, Generic[PageItem]):
    pagination: PaginationMeta
    results: list[PageItem]

class GameResponse(BaseModel):
    appid: int
    playtime_forever: int
    playtime_windows_forever: int
    playtime_mac_forever: int
    playtime_linux_forever: int
    playtime_deck_forever: int
    rtime_last_played: int
    playtime_disconnected: int
    name: str | None = None
    img_icon_url: str | None = None
    has_community_visible_stats: bool | None = None

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


@app.get("/IPlayerService/GetOwnedGames/v0001/", tags=["IPlayerService"], summary="GetOwnedGames", description="Returns a list of games owned by the player.", response_description="A list of games owned by the player.")
async def get_owned_games(
    steamid: str,
    api_key: Annotated[str, Depends(api_key_scheme)],
    include_appinfo: int = 0,
    include_played_free_games: int = 0,
    skip_unvetted_apps: int = 0,
    format: str = "json",
    page: int = 1,
    limit: int = 100,
) -> PaginatedResponse[GameResponse]:
    data = _get_owned_games(key=api_key, steamid=steamid, include_appinfo=include_appinfo, include_played_free_games=include_played_free_games, skip_unvetted_apps=skip_unvetted_apps, format=format)
    total_game_count = data["response"].get("game_count", 0)
    games = data["response"].get("games", [])[(page-1)*limit:page*limit]
    return {
        "pagination": {
            "total_count": total_game_count,
            "limit": limit,
            "page": page,
            "total_pages": (((total_game_count - 1) // limit) + 1),
        },
        "results": games,
    }

if __name__ == "__main__":
    app()
