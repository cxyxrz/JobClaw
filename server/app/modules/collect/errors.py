"""采集模块领域异常。"""


class CollectError(Exception):
    """采集流程基类异常。"""


class ParseError(CollectError):
    """解析阶段失败（文本提取/OCR 等）。"""


class ExtractError(CollectError):
    """字段抽取阶段失败。"""


class ValidateError(CollectError):
    """校验阶段失败（关键字段缺失等）。"""


class PersistError(CollectError):
    """入库阶段失败。"""
