"""图片文件解析器，通过 OCR 识别图片中的文字内容。"""

import logging
from pathlib import Path

from PIL import Image

from .base import BaseParser, Document

logger = logging.getLogger(__name__)


class ImageParser(BaseParser):
    """
    图片文件解析器 (.png, .jpg, .jpeg, .bmp, .tiff, .webp)。

    使用 RapidOCR 从图片中提取文字内容。
    """

    SUPPORTED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"]

    def __init__(self):
        self._ocr_engine = None

    def _get_ocr_engine(self):
        """懒加载 OCR 引擎。"""
        if self._ocr_engine is None:
            from rapidocr_onnxruntime import RapidOCR
            self._ocr_engine = RapidOCR()
        return self._ocr_engine

    def parse(self, file_path: str | Path) -> list[Document]:
        """
        解析图片文件，通过 OCR 识别图片中的文字。

        返回:
            包含识别文字的 Document 列表。若图片无可识别文字则返回空列表。
        """
        file_path = Path(file_path)
        documents = []

        img = Image.open(str(file_path))
        file_name = file_path.name

        # 确保图片为 RGB 或灰度模式（兼容 CMYK 等格式）
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        engine = self._get_ocr_engine()
        result, _ = engine(img)

        if result:
            text = "\n".join(line[1] for line in result if line[1])
            if text.strip():
                logger.info(
                    "图片 OCR 完成: %s (%dx%d), 识别 %d 字符",
                    file_name, img.width, img.height, len(text),
                )
                documents.append(
                    Document(
                        text=text,
                        metadata={
                            "source": file_name,
                            "file_type": "image",
                            "image_format": img.format,
                            "image_size": f"{img.width}x{img.height}",
                        },
                    )
                )
        else:
            logger.info("图片 OCR 未识别到文字: %s", file_name)

        return documents
