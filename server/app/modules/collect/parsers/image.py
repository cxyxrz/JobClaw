"""图片解析器：优先使用 PaddleOCR，未安装时给出明确提示。"""

from ..errors import ParseError
from .base import BaseParser, ParseResult


class ImageParser(BaseParser):
    source_type = "image"

    async def parse(self, payload: bytes | str, **kwargs) -> ParseResult:
        if isinstance(payload, str):
            raise ParseError("图片解析器需要二进制内容，请上传图片文件")

        try:
            from paddleocr import PaddleOCR  # type: ignore
        except ImportError as exc:
            raise ParseError(
                "图片 OCR 未启用：请安装 paddleocr 与 paddlepaddle "
                "（pip install paddleocr paddlepaddle）"
            ) from exc

        try:
            import io

            from PIL import Image

            img = Image.open(io.BytesIO(payload))
            ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
            result = ocr.ocr(img, cls=True)
            texts = []
            for page in result or []:
                for line in page or []:
                    if line and len(line) >= 2:
                        texts.append(line[1][0])
            text = "\n".join(texts)
        except Exception as exc:  # noqa: BLE001
            raise ParseError(f"图片 OCR 失败: {exc}") from exc

        if not text.strip():
            raise ParseError("图片中未识别到文字")

        return ParseResult(text=text, source_type=self.source_type)
