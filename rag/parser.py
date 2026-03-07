import os
from pypdf import PdfReader
from docx import Document


def parse_pdf(path):

    reader = PdfReader(path)
    pages = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""

        pages.append({
            "page": i + 1,
            "text": text
        })

    return pages


def parse_docx(path):

    doc = Document(path)

    text = "\n".join([p.text for p in doc.paragraphs])

    return [{
        "page": 1,
        "text": text
    }]


def parse_txt(path):

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    return [{
        "page": 1,
        "text": text
    }]


def parse_document(path):

    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        return parse_pdf(path)

    if ext == ".docx":
        return parse_docx(path)

    if ext == ".txt":
        return parse_txt(path)

    raise ValueError("Unsupported file format")