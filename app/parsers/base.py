"""
文档解析器基类和数据模型。

定义了所有文档解析器的统一接口和文档数据结构。
每个解析器负责将特定格式的文件转换为 Document 对象列表。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Document:
    """
    解析后的文档数据对象。

    属性:
        text: 提取出的文本内容。
        metadata: 附加元数据（如来源文件名、页码、文件类型等）。
    """

    text: str
    metadata: dict = field(default_factory=dict)

    @property
    def char_count(self) -> int:
        """返回文本的字符数。"""
        return len(self.text)


class BaseParser(ABC):
    """
    所有文档解析器的抽象基类。

    子类必须实现 parse() 方法，并声明 SUPPORTED_EXTENSIONS。
    """

    SUPPORTED_EXTENSIONS: list[str] = []  # 子类需覆盖，如 [".pdf", ".txt"]

    @abstractmethod
    def parse(self, file_path: str | Path) -> list[Document]:
        """
        解析文件，提取文本内容。

        参数:
            file_path: 待解析文件的路径。

        返回:
            Document 对象列表，每个对象包含一段文本和对应元数据。
        """

    @classmethod
    def can_parse(cls, file_path: str | Path) -> bool:
        """判断此解析器是否支持给定的文件类型。"""
        ext = Path(file_path).suffix.lower()
        return ext in cls.SUPPORTED_EXTENSIONS
