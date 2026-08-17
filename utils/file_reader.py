import os
import PyPDF2
from docx import Document as DocxDocument


def read_file(file_path: str) -> str:
    ext = file_path.split(".")[-1].lower()

    if ext == "txt" or ext == "md":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    elif ext == "pdf":
        reader = PyPDF2.PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    elif ext == "docx":
        doc = DocxDocument(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text

    else:
        return ""