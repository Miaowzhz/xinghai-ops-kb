# backend/app/utils/parsers.py
from pathlib import Path
from pypdf import PdfReader
from docx import Document as DocxDocument


def parse_file(file_path: str, file_type: str) -> str:
    """把上传文件解析成纯文本。解析不到内容时返回空串，由流水线判空走失败分支。"""
    path = Path(file_path)
    if file_type == "pdf":
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if file_type == "docx":
        doc = DocxDocument(str(path))
        return "\n".join(p.text for p in doc.paragraphs)
    # md / txt 直接按文本读
    return path.read_text(encoding="utf-8", errors="ignore")