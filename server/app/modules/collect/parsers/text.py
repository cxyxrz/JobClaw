"""文本直读解析器。"""

from .base import BaseParser, ParseResult


class TextParser(BaseParser):
    source_type = "text"

    async def parse(self, payload: bytes | str, **kwargs) -> ParseResult:
        if isinstance(payload, bytes):
            text = payload.decode("utf-8", errors="ignore")
        else:
            text = payload
        return ParseResult(text=text.strip(), source_type=self.source_type)
