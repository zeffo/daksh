from __future__ import annotations
import asyncio
from yt_dlp import YoutubeDL
from logging import getLogger
from typing import TYPE_CHECKING, Any, cast
from re import compile
import json
from .models import APIResult, Track, Playlist


if TYPE_CHECKING:
    from httpx import AsyncClient

logger = getLogger("daksh")
VIDEO = compile(
    r"^(?:https?:\/\/)?(?:www\.)?(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))((\w|-){11})(?:\S+)?$"
)
PLAYLIST = compile(r"^.*(youtu.be\/|list=)([^#\&\?]*).*")


class YTDL(YoutubeDL):
    def __init__(self):
        params = {
            "format": "bestaudio",
            "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
            "restrictfilenames": True,
            "noplaylist": False,
            "nocheckcertificate": True,
            "ignoreerrors": True,
            "logtostderr": False,
            "quiet": True,
            "no_warnings": True,
            "default_search": "auto",
            "source_address": "0.0.0.0",
            "extract_flat": True,
            "skip_download": True,
            "logger": logger,
        }
        super().__init__(params=params)  # type: ignore

    @classmethod
    async def get_data(cls, uri: str):
        def to_thread() -> dict[Any, Any]:
            with cls() as ytdl:
                data = ytdl.extract_info(uri, download=False)  # type: ignore
                data = cast(dict[Any, Any], data)
            return data

        return await asyncio.to_thread(to_thread)

    @classmethod
    async def get(cls, query: str, *, api_key: str, client: "AsyncClient"):
        if match := VIDEO.match(query):
            data = await cls.get_data(match.group(1))
            ret = [Track(**data)]
        elif PLAYLIST.match(query):
            data = await cls.get_data(query)
            with open("data.json", "w") as f:
                json.dump(data, f, indent=4)
            ret = Playlist(**data)
        else:
            ret = await cls.from_api(query, api_key=api_key, client=client) or []
        return ret

    @classmethod
    async def from_api(cls, query: str, *, api_key: str, client: "AsyncClient"):
        endpoint = f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=10&q={query}&type=video&key={api_key}"
        resp = await client.get(endpoint)
        if resp.status_code != 200:
            return None
        json = resp.json()
        if not json.get("items"):
            return None
        return APIResult(**json)
