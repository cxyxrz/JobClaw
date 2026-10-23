"""解析器注册与工厂。"""

from .base import BaseParser
from .excel import ExcelParser
from .html import HtmlParser
from .image import ImageParser
from .text import TextParser

PARSERS: dict[str, BaseParser] = {
    "text": TextParser(),
    "html": HtmlParser(),
    "excel": ExcelParser(),
    "image": ImageParser(),
}


def get_parser(source_type: str) -> BaseParser:
    if source_type not in PARSERS:
        from ..errors import ParseError

        raise ParseError(f"不支持的来源类型: {source_type}")
    return PARSERS[source_type]
