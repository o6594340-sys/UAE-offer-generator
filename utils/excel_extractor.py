from io import BytesIO


def extract_text_from_excel(file_bytes: bytes) -> str:
    from openpyxl import load_workbook

    wb = load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    parts = []

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = []
        for row in ws.iter_rows(values_only=True):
            cells = [str(c).strip() if c is not None else '' for c in row]
            if any(c for c in cells):
                rows.append('\t'.join(cells))
        if rows:
            parts.append(f"=== Sheet: {sheet_name} ===\n" + '\n'.join(rows))

    wb.close()
    return '\n\n'.join(parts)
