"""Plain text and Markdown file parser."""

from pathlib import Path

from .base import BaseParser, Document


class TextParser(BaseParser):
    """Parser for plain text and Markdown files."""

    SUPPORTED_EXTENSIONS = [".txt", ".md", ".csv", ".json", ".xml", ".html", ".log"]

    def parse(self, file_path: str | Path) -> list[Document]:
        file_path = Path(file_path)
        documents = []

        # Try common encodings
        text = None
        for encoding in ["utf-8", "gbk", "gb2312", "latin-1"]:
            try:
                text = file_path.read_text(encoding=encoding)
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if text and text.strip():
            documents.append(
                Document(
                    text=text.strip(),
                    metadata={
                        "source": file_path.name,
                        "file_type": "text",
                        "extension": file_path.suffix.lower(),
                    },
                )
            )

        return documents
