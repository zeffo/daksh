from __future__ import annotations
from pydantic import BaseModel
from html import unescape
from typing import Any


class Thumbnail(BaseModel):
    url: str


class BaseTrack(BaseModel):
    id: str
    title: str
    description: str | None
    uploader: str | None
    thumbnails: list[Thumbnail]

    def get_thumbnail(self):
        return self.thumbnails[-1]
    


class Track(BaseTrack):
    url: str
    duration: float

class Playlist(BaseTrack):
    entries: list[Track]
    uploader: str

    def __init__(self, **data: Any):
        for track in data.get("entries", []):
            track["uploader"] = track.get("channel", "Unknown Uploader")
        super().__init__(**data)


class APIId(BaseModel):
    kind: str
    videoId: str


class APISnippet(BaseModel):
    def __init__(self, **data: str) -> None:
        for key, value in data.items():
            data[key] = unescape(value)
        super().__init__(**data)

    title: str
    description: str | None
    thumbnails: dict[str, Thumbnail]
    channelTitle: str


class APIItem(BaseModel):
    id: APIId
    snippet: APISnippet

    def partial(self):
        snip = self.snippet
        return BaseTrack(
            id=self.id.videoId,
            title=snip.title,
            description=snip.description,
            uploader=snip.channelTitle,
            thumbnails=list(snip.thumbnails.values()),
        )


class APIResult(BaseModel):
    items: list[APIItem]
