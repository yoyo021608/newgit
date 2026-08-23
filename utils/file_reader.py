#读取不同格式的文件内容。
import os
import PyPDF2  #解析 PDF 文件，提取文字
from docx import Document as DocxDocument


def read_file(file_path: str) -> str:
    ext = file_path.split(".")[-1].lower()

    if ext == "txt" or ext == "md":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    elif ext == "pdf":
        reader = PyPDF2.PdfReader(file_path)  #创建pdf读取器
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""  #提取当前页文字
        return text

    elif ext == "docx":
        doc = DocxDocument(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text

    else:
        return ""