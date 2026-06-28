"""
PDF 文档解析器，基于 PyMuPDF (fitz)。

支持三种文本提取方式：
1. 直接文本提取：从 PDF 页面中提取已嵌入的文本内容
2. 扫描页 OCR：对于扫描件/图片 PDF（文本极少），自动渲染整页为图像后 OCR
3. 页面内嵌图片 OCR：对含有图片的页面，提取嵌入图片并 OCR 识别文字，
   确保图片中的信息不丢失

OCR 使用 RapidOCR（基于 ONNXRuntime），无需安装 Tesseract 系统依赖。
"""

import io
import logging
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

from .base import BaseParser, Document

logger = logging.getLogger(__name__)

# 内嵌图片 OCR 的最小尺寸（像素），过滤装饰性小图标
_MIN_IMAGE_SIZE = 50


class PDFParser(BaseParser):
    """
    PDF 文件解析器。

    逐页提取文本，并智能处理图片内容：
    - 扫描页（文本极少）：渲染整页为图像后 OCR
    - 含图片页面：提取嵌入图片并 OCR，将识别文字追加到文本中
    """

    SUPPORTED_EXTENSIONS = [".pdf"]

    def __init__(self, use_ocr: bool = True, ocr_threshold: int = 50):
        """
        参数:
            use_ocr: 是否启用 OCR 识别，默认 True。
            ocr_threshold: 文本字符数低于此阈值的页面会被视为扫描页，默认 50。
        """
        self.use_ocr = use_ocr
        self.ocr_threshold = ocr_threshold
        self._ocr_engine = None  # 延迟加载 OCR 引擎

    def _get_ocr_engine(self):
        """懒加载 RapidOCR 引擎，避免在不需要 OCR 时产生导入开销。"""
        if self._ocr_engine is None:
            from rapidocr_onnxruntime import RapidOCR
            self._ocr_engine = RapidOCR()
        return self._ocr_engine

    def _render_and_ocr_page(self, doc: fitz.Document, page_num: int) -> str:
        """
        对单个 PDF 页面进行整页 OCR（适用于扫描页）。

        将页面渲染为 300 DPI 的 PNG 图像后送入 OCR 引擎识别。

        返回:
            识别出的文本内容（多行以换行符连接）。
        """
        page = doc[page_num]
        # 300 DPI 渲染以获得更好的 OCR 精度
        pix = page.get_pixmap(dpi=300)
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))

        engine = self._get_ocr_engine()
        result, _ = engine(img)

        if not result:
            return ""
        # result 格式: [[坐标框, 文本, 置信度], ...]
        return "\n".join(line[1] for line in result if line[1])

    def _extract_and_ocr_images(self, page: fitz.Page) -> str:
        """
        从 PDF 页面中提取嵌入图片并逐一 OCR 识别。

        仅处理尺寸足够大的图片（过滤装饰性小图标），
        将每张图片的 OCR 结果用换行连接。

        返回:
            所有图片 OCR 识别出的文本内容。
        """
        image_list = page.get_images(full=True)
        if not image_list:
            return ""

        engine = self._get_ocr_engine()
        ocr_texts = []

        for img_info in image_list:
            xref = img_info[0]
            try:
                # 从 PDF 对象中提取图片数据
                base_image = page.parent.extract_image(xref)
                if not base_image:
                    continue

                img_bytes = base_image["image"]
                img_width = base_image.get("width", 0)
                img_height = base_image.get("height", 0)

                # 过滤太小的图片（装饰性图标等）
                if img_width < _MIN_IMAGE_SIZE or img_height < _MIN_IMAGE_SIZE:
                    continue

                # 用 PIL 打开图片并送 OCR
                img = Image.open(io.BytesIO(img_bytes))
                # 确保是 RGB 模式（某些格式如 CMYK 需要转换）
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")

                result, _ = engine(img)
                if result:
                    page_ocr_text = "\n".join(
                        line[1] for line in result if line[1]
                    )
                    if page_ocr_text.strip():
                        ocr_texts.append(page_ocr_text.strip())
                        logger.debug(
                            "图片 OCR (xref=%d): %d 字符",
                            xref, len(page_ocr_text),
                        )
            except Exception as e:
                logger.debug("提取/OCR 图片失败 (xref=%d): %s", xref, e)
                continue

        return "\n\n".join(ocr_texts)

    def parse(self, file_path: str | Path) -> list[Document]:
        """
        解析 PDF 文件，每页生成一个 Document 对象。

        处理逻辑：
        1. 提取页面文本
        2. 若文本过少（扫描页）→ 整页 OCR
        3. 若文本正常但页面含图片 → 提取图片 OCR，追加新内容
        """
        file_path = Path(file_path)
        documents = []

        pdf_doc = fitz.open(str(file_path))
        file_name = file_path.name

        try:
            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                text = page.get_text("text").strip()
                ocr_used = False

                if self.use_ocr:
                    if len(text) < self.ocr_threshold:
                        # 文本过少 → 扫描页，整页 OCR
                        ocr_text = self._render_and_ocr_page(pdf_doc, page_num)
                        if ocr_text:
                            text = ocr_text
                            ocr_used = True
                            logger.info(
                                "PDF 第 %d 页为扫描页，已整页 OCR: %d 字符",
                                page_num + 1, len(ocr_text),
                            )
                    else:
                        # 文本正常 → 提取页面内嵌图片并 OCR
                        img_text = self._extract_and_ocr_images(page)
                        if img_text:
                            # 仅追加与现有文本不重复的内容
                            text += "\n\n" + img_text
                            ocr_used = True
                            logger.info(
                                "PDF 第 %d 页提取到 %d 张图片，OCR: %d 字符",
                                page_num + 1,
                                len(page.get_images(full=True)),
                                len(img_text),
                            )

                if text:
                    documents.append(
                        Document(
                            text=text,
                            metadata={
                                "source": file_name,
                                "page": page_num + 1,
                                "file_type": "pdf",
                                "total_pages": len(pdf_doc),
                                "ocr_applied": ocr_used,
                            },
                        )
                    )
        finally:
            pdf_doc.close()

        return documents
