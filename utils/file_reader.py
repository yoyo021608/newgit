#读取不同格式的文件内容。
import os
import pdfplumber  # 对 PDF 中文支持更好
from docx import Document as DocxDocument


def read_file(file_path: str) -> str:
    ext = file_path.split(".")[-1].lower()

    if ext == "txt" or ext == "md":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    elif ext == "pdf":
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        return text

    elif ext == "docx":
        doc = DocxDocument(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text

    else:
        return ""