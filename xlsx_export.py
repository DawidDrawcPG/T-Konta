"""Lekki generator XLSX dla układu tradycyjnych kont T.

Moduł korzysta wyłącznie z biblioteki standardowej Pythona, dzięki czemu
lokalna aplikacja nie wymaga instalowania pakietów biurowych.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import re
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape, unescape


def _column_name(number: int) -> str:
    result = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _cell_ref(row: int, column: int) -> str:
    return f"{_column_name(column)}{row}"


def _text_cell(row: int, column: int, value: str, style: int = 0) -> str:
    ref = _cell_ref(row, column)
    safe = escape(str(value))
    return f'<c r="{ref}" s="{style}" t="inlineStr"><is><t>{safe}</t></is></c>'


def _number_cell(row: int, column: int, value: float, style: int) -> str:
    ref = _cell_ref(row, column)
    return f'<c r="{ref}" s="{style}"><v>{float(value):.2f}</v></c>'


def _blank_cell(row: int, column: int, style: int) -> str:
    return f'<c r="{_cell_ref(row, column)}" s="{style}"/>'


def _operation_marker(entry: dict, side: str) -> str:
    """Zapis jak w ręcznym koncie T: 9a) po Wn i (9a po Ma."""
    number = str(entry.get("numer_operacji", "")).strip()
    return f"{number})" if side == "W" else f"({number}"


def _account_title(account: dict) -> str:
    """Widoczny nagłówek konta: numer oraz nazwa, jak w zeszycie ćwiczeń."""
    number = str(account.get("numer", "")).strip()
    name = str(account.get("nazwa", "")).strip()
    return " ".join(part for part in (number, name) if part)


def _account_title_cells(accounts: list[dict]) -> list[tuple[dict, str]]:
    """Zwraca komórki nagłówków w tym samym układzie, co generator arkusza."""
    cells: list[tuple[dict, str]] = []
    current_row = 2
    for group_start in range(0, len(accounts), 3):
        group = accounts[group_start : group_start + 3]
        group_depth = max(
            4,
            *(max(
                len([entry for entry in account.get("zapisy", []) if entry.get("strona") == "W"]),
                len([entry for entry in account.get("zapisy", []) if entry.get("strona") == "M"]),
            ) for account in group),
        )
        for position, account in enumerate(group):
            cells.append((account, _cell_ref(current_row, 2 + position * 5)))
        current_row += group_depth + 2
    return cells


def _visible_account_numbers(archive: ZipFile, accounts: list[dict]) -> dict[int, str]:
    """Odczytuje ręcznie poprawiony numer z widocznego nagłówka arkusza XLSX."""
    try:
        root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    except (KeyError, ET.ParseError):
        return {}

    namespace = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    values: dict[str, str] = {}
    for cell in root.findall(".//x:c", namespace):
        reference = cell.get("r")
        text_node = cell.find(".//x:t", namespace)
        if reference and text_node is not None and text_node.text is not None:
            values[reference] = text_node.text.strip()

    overrides: dict[int, str] = {}
    for account, reference in _account_title_cells(accounts):
        visible_title = values.get(reference, "")
        name = str(account.get("nazwa", "")).strip()
        match = re.fullmatch(rf"(.+?)\s+{re.escape(name)}", visible_title) if name else None
        if match:
            number = match.group(1).strip()
            if number:
                overrides[id(account)] = number
    return overrides


def _entry_tone(account: dict, side: str) -> str:
    """Kolor oznacza skutek zapisu dla typu konta, nie samą stronę Wn/Ma."""
    typ = account.get("typ")
    if typ == "Wynik finansowy":
        return "neutralny"
    normalna = {"Aktywne": "W", "Kosztowe": "W", "Pasywne": "M", "Przychodowe": "M"}.get(typ)
    if typ == "Aktywno-pasywne":
        # Wybrana w ćwiczeniu strona typowa rozstrzyga kolor danego konta.
        normalna = account.get("strona_salda_poczatkowego", "W")
    return "zwiekszenie" if side == normalna else "zmniejszenie"


def _entry_styles(account: dict, side: str) -> tuple[int, int]:
    """Zwraca style markera i kwoty dla lewej lub prawej strony konta T."""
    tone = _entry_tone(account, side)
    if side == "W":
        return {"zwiekszenie": (2, 3), "zmniejszenie": (4, 5), "neutralny": (10, 11)}[tone]
    return {"zwiekszenie": (7, 6), "zmniejszenie": (9, 8), "neutralny": (13, 12)}[tone]


def _closing_styles(marker_style: int, amount_style: int, side: str) -> tuple[int, int]:
    """Wariant stylu z podwójną linią: formalne zamknięcie konta T."""
    if side == "W":
        return {2: (14, 15), 4: (16, 17), 10: (18, 19)}[marker_style]
    return {7: (20, 21), 9: (22, 23), 13: (24, 25)}[marker_style]


def _sheet_xml(accounts: list[dict]) -> str:
    """Buduje prosty układ 1:1 z arkuszem zad15: numer | Wn | Ma | numer."""
    rows: dict[int, list[str]] = {}
    merges: list[str] = []
    header_rows: set[int] = set()
    max_column = 14
    current_row = 2

    for group_start in range(0, len(accounts), 3):
        group = accounts[group_start : group_start + 3]
        group_depth = max(
            4,
            *(max(
                len([e for e in account.get("zapisy", []) if e.get("strona") == "W"]),
                len([e for e in account.get("zapisy", []) if e.get("strona") == "M"]),
            ) for account in group),
        )

        for position, account in enumerate(group):
            header_rows.add(current_row)
            start_column = 1 + position * 5
            left_note, debit_col, credit_col, right_note = (
                start_column,
                start_column + 1,
                start_column + 2,
                start_column + 3,
            )
            title = _account_title(account)
            rows.setdefault(current_row, []).append(_text_cell(current_row, debit_col, title, 1))
            rows[current_row].append(_blank_cell(current_row, credit_col, 1))
            merges.append(f"{_cell_ref(current_row, debit_col)}:{_cell_ref(current_row, credit_col)}")

            debit_entries = [e for e in account.get("zapisy", []) if e.get("strona") == "W"]
            credit_entries = [e for e in account.get("zapisy", []) if e.get("strona") == "M"]
            for index in range(group_depth):
                row = current_row + 1 + index
                linia_zamkniecia = bool(account.get("zamkniete")) and index == group_depth - 1
                if index < len(debit_entries):
                    entry = debit_entries[index]
                    marker_style, amount_style = _entry_styles(account, "W")
                    if linia_zamkniecia:
                        marker_style, amount_style = _closing_styles(marker_style, amount_style, "W")
                    rows.setdefault(row, []).extend([
                        _text_cell(row, left_note, _operation_marker(entry, "W"), marker_style),
                        _number_cell(row, debit_col, float(entry.get("kwota", 0)), amount_style),
                    ])
                elif linia_zamkniecia:
                    marker_style, amount_style = _closing_styles(*_entry_styles(account, "W"), "W")
                    rows.setdefault(row, []).extend([_blank_cell(row, left_note, marker_style), _blank_cell(row, debit_col, amount_style)])
                else:
                    rows.setdefault(row, []).append(_blank_cell(row, debit_col, 6))

                if index < len(credit_entries):
                    entry = credit_entries[index]
                    marker_style, amount_style = _entry_styles(account, "M")
                    if linia_zamkniecia:
                        marker_style, amount_style = _closing_styles(marker_style, amount_style, "M")
                    rows.setdefault(row, []).extend([
                        _number_cell(row, credit_col, float(entry.get("kwota", 0)), amount_style),
                        _text_cell(row, right_note, _operation_marker(entry, "M"), marker_style),
                    ])
                elif linia_zamkniecia:
                    marker_style, amount_style = _closing_styles(*_entry_styles(account, "M"), "M")
                    rows.setdefault(row, []).extend([_blank_cell(row, credit_col, amount_style), _blank_cell(row, right_note, marker_style)])
        current_row += group_depth + 2

    if not accounts:
        rows[2] = [_text_cell(2, 1, "Brak kont do wyeksportowania.", 0)]

    max_row = max(rows)
    row_xml = []
    for row_number in sorted(rows):
        height = 24 if row_number in header_rows else 23.25
        cells = "".join(sorted(rows[row_number], key=lambda cell: cell.split('r="', 1)[1].split('"', 1)[0]))
        row_xml.append(f'<row r="{row_number}" ht="{height}" customHeight="1">{cells}</row>')

    reference_widths = [
        6.140625, 22.5703125, 16.5703125, 5.28515625, 5,
        6.140625, 22.5703125, 16.5703125, 5.28515625, 5,
        6.140625, 22.5703125, 16.5703125, 5.28515625,
    ]
    columns = [
        f'<col min="{col}" max="{col}" width="{width}" customWidth="1"/>'
        for col, width in enumerate(reference_widths, start=1)
    ]

    merge_xml = ""
    if merges:
        merge_xml = f'<mergeCells count="{len(merges)}">' + "".join(f'<mergeCell ref="{ref}"/>' for ref in merges) + "</mergeCells>"

    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
 <dimension ref="A1:{_cell_ref(max_row, max_column)}"/>
 <sheetViews><sheetView showGridLines="1" zoomScale="52" zoomScaleNormal="100" workbookViewId="0"><selection activeCell="A1" sqref="A1"/></sheetView></sheetViews>
 <sheetFormatPr defaultRowHeight="23.25"/>
 <cols>{''.join(columns)}</cols>
 <sheetData>{''.join(row_xml)}</sheetData>
 {merge_xml}
</worksheet>'''


def _styles_xml() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
 <fonts count="3">
  <font><sz val="16"/><name val="Arial"/><family val="2"/><charset val="238"/></font>
  <font><sz val="16"/><color rgb="FFC23B45"/><name val="Arial"/><family val="2"/><charset val="238"/></font>
  <font><sz val="16"/><color rgb="FF16875B"/><name val="Arial"/><family val="2"/><charset val="238"/></font>
 </fonts>
 <fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>
 <borders count="5">
  <border><left/><right/><top/><bottom/><diagonal/></border>
  <border><left/><right/><top/><bottom style="thin"><color indexed="64"/></bottom><diagonal/></border>
  <border><left/><right style="thin"><color indexed="64"/></right><top/><bottom/><diagonal/></border>
  <border><left/><right/><top/><bottom style="double"><color indexed="64"/></bottom><diagonal/></border>
  <border><left/><right style="thin"><color indexed="64"/></right><top/><bottom style="double"><color indexed="64"/></bottom><diagonal/></border>
 </borders>
 <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
 <cellXfs count="26">
  <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyFont="1"/>
  <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center"/></xf>
  <xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1" applyAlignment="1"><alignment horizontal="right"/></xf>
  <xf numFmtId="3" fontId="2" fillId="0" borderId="2" xfId="0" applyNumberFormat="1" applyFont="1" applyBorder="1"/>
  <xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1" applyAlignment="1"><alignment horizontal="right"/></xf>
  <xf numFmtId="3" fontId="1" fillId="0" borderId="2" xfId="0" applyNumberFormat="1" applyFont="1" applyBorder="1"/>
  <xf numFmtId="3" fontId="2" fillId="0" borderId="0" xfId="0" applyNumberFormat="1" applyFont="1" applyAlignment="1"><alignment horizontal="left"/></xf>
  <xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1" applyAlignment="1"><alignment horizontal="left"/></xf>
  <xf numFmtId="3" fontId="1" fillId="0" borderId="0" xfId="0" applyNumberFormat="1" applyFont="1" applyAlignment="1"><alignment horizontal="left"/></xf>
  <xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1" applyAlignment="1"><alignment horizontal="left"/></xf>
  <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyFont="1" applyAlignment="1"><alignment horizontal="right"/></xf>
  <xf numFmtId="3" fontId="0" fillId="0" borderId="2" xfId="0" applyNumberFormat="1" applyFont="1" applyBorder="1"/>
  <xf numFmtId="3" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1" applyFont="1" applyAlignment="1"><alignment horizontal="left"/></xf>
  <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyFont="1" applyAlignment="1"><alignment horizontal="left"/></xf>
  <xf numFmtId="0" fontId="2" fillId="0" borderId="3" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1"><alignment horizontal="right"/></xf>
  <xf numFmtId="3" fontId="2" fillId="0" borderId="4" xfId="0" applyNumberFormat="1" applyFont="1" applyBorder="1"/>
  <xf numFmtId="0" fontId="1" fillId="0" borderId="3" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1"><alignment horizontal="right"/></xf>
  <xf numFmtId="3" fontId="1" fillId="0" borderId="4" xfId="0" applyNumberFormat="1" applyFont="1" applyBorder="1"/>
  <xf numFmtId="0" fontId="0" fillId="0" borderId="3" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1"><alignment horizontal="right"/></xf>
  <xf numFmtId="3" fontId="0" fillId="0" borderId="4" xfId="0" applyNumberFormat="1" applyFont="1" applyBorder="1"/>
  <xf numFmtId="0" fontId="2" fillId="0" borderId="3" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1"><alignment horizontal="left"/></xf>
  <xf numFmtId="3" fontId="2" fillId="0" borderId="3" xfId="0" applyNumberFormat="1" applyFont="1" applyBorder="1" applyAlignment="1"><alignment horizontal="left"/></xf>
  <xf numFmtId="0" fontId="1" fillId="0" borderId="3" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1"><alignment horizontal="left"/></xf>
  <xf numFmtId="3" fontId="1" fillId="0" borderId="3" xfId="0" applyNumberFormat="1" applyFont="1" applyBorder="1" applyAlignment="1"><alignment horizontal="left"/></xf>
  <xf numFmtId="0" fontId="0" fillId="0" borderId="3" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1"><alignment horizontal="left"/></xf>
  <xf numFmtId="3" fontId="0" fillId="0" borderId="3" xfId="0" applyNumberFormat="1" applyFont="1" applyBorder="1" applyAlignment="1"><alignment horizontal="left"/></xf>
 </cellXfs>
 <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
 <dxfs count="0"/>
 <tableStyles count="0" defaultTableStyle="TableStyleMedium2" defaultPivotStyle="PivotStyleLight16"/>
</styleSheet>'''


def build_xlsx(accounts: list[dict]) -> bytes:
    """Zwraca gotowy plik XLSX jako bajty."""
    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="xml" ContentType="application/xml"/>
 <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
 <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
 <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
 <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
 <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>'''
    root_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
 <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
 <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''
    workbook = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
 <bookViews><workbookView xWindow="0" yWindow="0" windowWidth="24000" windowHeight="14000"/></bookViews>
 <sheets><sheet name="Konta T" sheetId="1" r:id="rId1"/></sheets>
 <calcPr calcId="191029" fullCalcOnLoad="1"/>
</workbook>'''
    workbook_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
 <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>'''
    app = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><Application>Kontownik</Application></Properties>'''
    core = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:creator>Kontownik</dc:creator><dc:title>Konta T</dc:title><dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created></cp:coreProperties>'''

    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("docProps/app.xml", app)
        archive.writestr("docProps/core.xml", core)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/styles.xml", _styles_xml())
        archive.writestr("xl/worksheets/sheet1.xml", _sheet_xml(accounts))
        state = escape(json.dumps({"format": "kontownik-t-v2", "konta": accounts}, ensure_ascii=False))
        archive.writestr("customXml/item1.xml", f'<?xml version="1.0" encoding="UTF-8"?><kontownikState><state>{state}</state></kontownikState>')
    return output.getvalue()


def read_xlsx_state(file_bytes: bytes) -> dict:
    """Odtwarza ćwiczenie z pliku wcześniej wyeksportowanego przez Kontownik."""
    try:
        with ZipFile(BytesIO(file_bytes)) as archive:
            raw = archive.read("customXml/item1.xml").decode("utf-8")
    except Exception as exc:
        raise ValueError("Wybierz plik XLSX wyeksportowany wcześniej z Kontownika.") from exc
    match = re.search(r"<state>(.*)</state>", raw, flags=re.DOTALL)
    if not match:
        raise ValueError("Plik XLSX nie zawiera danych ćwiczenia Kontownika.")
    try:
        state = json.loads(unescape(match.group(1)))
    except json.JSONDecodeError as exc:
        raise ValueError("Dane ćwiczenia w pliku XLSX są uszkodzone.") from exc
    if state.get("format") != "kontownik-t-v2":
        raise ValueError("To nie jest plik ćwiczenia wyeksportowany z aktualnego Kontownika.")
    try:
        with ZipFile(BytesIO(file_bytes)) as archive:
            visible_numbers = _visible_account_numbers(archive, state.get("konta", []))
    except Exception:
        visible_numbers = {}
    for account in state.get("konta", []):
        if id(account) in visible_numbers:
            account["numer"] = visible_numbers[id(account)]
    return state
