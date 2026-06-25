"""
文件文本提取 — 支持 txt / docx / pdf
"""
import io
from typing import Optional


def extract_text(filename: str, content: bytes) -> Optional[str]:
    """根据文件扩展名提取文本内容"""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "txt":
        return _extract_txt(content)
    elif ext == "docx":
        return _extract_docx(content)
    elif ext == "pdf":
        return _extract_pdf(content)
    else:
        return None


def _extract_txt(content: bytes) -> str:
    """纯文本（尝试 UTF-8 / GBK）"""
    for enc in ["utf-8", "gbk", "gb2312", "latin-1"]:
        try:
            return content.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return content.decode("utf-8", errors="replace")


def _extract_docx(content: bytes) -> str:
    """Word 文档"""
    from docx import Document
    doc = Document(io.BytesIO(content))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def _extract_pdf(content: bytes) -> str:
    """PDF 文档"""
    from PyPDF2 import PdfReader
    reader = PdfReader(io.BytesIO(content))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n".join(pages)
