"""解析器基类：将原始输入统一转为纯文本。"""

from abc import ABC, abstractmethod


class ParseResult:
    def __init__(self, text: str, source_type: str, meta: dict | None = None):
        self.text = text
        self.source_type = source_type
        self.meta = meta or {}


class BaseParser(ABC):
    source_type: str = "text"

    @abstractmethod
    async def parse(self, payload: bytes | str, **kwargs) -> ParseResult:
        """将输入解析为纯文本。"""
