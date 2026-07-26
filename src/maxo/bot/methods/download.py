from dataclasses import dataclass

from unihttp.http import HTTPResponse
from unihttp.http.stream import AsyncChunkStream
from unihttp.markers import Path
from unihttp.method import StreamMethod


@dataclass
class Download(StreamMethod):
    """Скачивание вложения по произвольному URL (не по шаблону API)."""

    url: Path[str]

    __url__ = "{url}"
    __method__ = "GET"

    def on_error(self, response: HTTPResponse[AsyncChunkStream]) -> None:
        response.raise_for_status()
