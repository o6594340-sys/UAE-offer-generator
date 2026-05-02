from io import BytesIO


def extract_text_from_pdf(file_bytes: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(file_bytes))
    pages = []
    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ''
        text = text.strip()
        if text:
            pages.append(f"[Page {i}]\n{text}")
    return "\n\n".join(pages)
