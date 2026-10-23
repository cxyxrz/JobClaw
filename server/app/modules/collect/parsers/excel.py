"""Excel 解析器：用 openpyxl 读取所有单元格并拼接为文本。"""

import io

from openpyxl import load_workbook

from ..errors import ParseError
from .base import BaseParser, ParseResult


class ExcelParser(BaseParser):
    source_type = "excel"

    async def parse(self, payload: bytes | str, **kwargs) -> ParseResult:
        if isinstance(payload, str):
            # 如果是文件路径，读取字节；此处统一按字节处理
            raise ParseError("Excel 解析器需要二进制内容，请上传 .xlsx 文件")
        try:
            wb = load_workbook(io.BytesIO(payload), read_only=True, data_only=True)
        except Exception as exc:  # noqa: BLE001
            raise ParseError(f"Excel 读取失败: {exc}") from exc

        lines: list[str] = []
        for ws in wb.worksheets:
            lines.append(f"## Sheet: {ws.title}")
            for row in ws.iter_rows(values_only=True):
                cells = [str(c) for c in row if c is not None]
                if cells:
                    lines.append("\t".join(cells))
        text = "\n".join(lines)
        wb.close()

        if not text.strip():
            raise ParseError("Excel 内容为空")

        return ParseResult(text=text, source_type=self.source_type)
