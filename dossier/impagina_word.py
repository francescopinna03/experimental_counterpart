"""Uniforma l'impaginazione del DOCX prodotto da Pandoc, preservando le equazioni."""
from pathlib import Path
from docx import Document
from docx.shared import Mm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT

path = Path(__file__).resolve().parent.parent / 'Protocollo_identificazione_dinamica.docx'
doc = Document(path)
math_props = doc.settings.element.find(qn('m:mathPr'))
if math_props is not None:
    math_font = math_props.find(qn('m:mathFont'))
    if math_font is not None:
        math_font.set(qn('m:val'), 'Latin Modern Math')
for section in doc.sections:
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.top_margin = Mm(23)
    section.bottom_margin = Mm(22)
    section.left_margin = Mm(23)
    section.right_margin = Mm(23)
    section.footer_distance = Mm(10)
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if not p.text and not p._p.xpath('.//w:fldSimple'):
        field = OxmlElement('w:fldSimple')
        field.set(qn('w:instr'), 'PAGE')
        p._p.append(field)

for style in doc.styles:
    if style.style_id in ('Normal', 'BodyText', 'FirstParagraph'):
        style.font.name = 'DejaVu Serif'
        style.font.size = Pt(11)
        style.paragraph_format.space_after = Pt(5)
        style.paragraph_format.line_spacing = 1.06
        style.paragraph_format.widow_control = True
    if style.style_id.startswith('Heading') or style.style_id in ('Title', 'Subtitle'):
        style.font.color.rgb = RGBColor(0, 0, 0)
        rpr = style.element.get_or_add_rPr()
        for color in rpr.findall(qn('w:color')):
            for attr in ('themeColor', 'themeTint', 'themeShade'):
                color.attrib.pop(qn('w:' + attr), None)
        style.paragraph_format.keep_with_next = True
    if style.style_id == 'Title':
        style.font.size = Pt(21)
        style.font.bold = True

widths_mm = [
    [96, 34, 34], [39, 125], [82, 41, 41], [65, 33, 33, 33],
    [27, 26, 29, 18, 21, 19, 24], [26, 46, 46, 46], [124, 40],
    [124, 40], [50, 57, 57], [37, 127], [78, 56, 30], [114, 50],
]
assert len(doc.tables) == len(widths_mm), (len(doc.tables), len(widths_mm))
for table, widths in zip(doc.tables, widths_mm):
    table.autofit = False
    for column, width in zip(table.columns, widths):
        column.width = Mm(width)
    props = table._tbl.tblPr
    old = props.find(qn('w:tblBorders'))
    if old is not None:
        props.remove(old)
    borders = OxmlElement('w:tblBorders')
    for side in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        edge = OxmlElement('w:' + side)
        for name, value in [('val', 'single'), ('sz', '4'), ('color', 'D9D9D9')]:
            edge.set(qn('w:' + name), value)
        borders.append(edge)
    props.append(borders)
    for i, row in enumerate(table.rows):
        trpr = row._tr.get_or_add_trPr()
        if trpr.find(qn('w:cantSplit')) is None:
            trpr.append(OxmlElement('w:cantSplit'))
        if i == 0:
            if trpr.find(qn('w:tblHeader')) is None:
                trpr.append(OxmlElement('w:tblHeader'))
        for cell, width in zip(row.cells, widths):
            cell.width = Mm(width)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tcpr = cell._tc.get_or_add_tcPr()
            margins = OxmlElement('w:tcMar')
            for side in ('top', 'left', 'bottom', 'right'):
                item = OxmlElement('w:' + side)
                item.set(qn('w:w'), '70')
                item.set(qn('w:type'), 'dxa')
                margins.append(item)
            old = tcpr.find(qn('w:tcMar'))
            if old is not None:
                tcpr.remove(old)
            tcpr.append(margins)
            if i == 0:
                for old in tcpr.findall(qn('w:shd')):
                    tcpr.remove(old)
                shade = OxmlElement('w:shd')
                shade.set(qn('w:fill'), 'E7EEF1')
                tcpr.append(shade)
            for p in cell.paragraphs:
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.line_spacing = 1.0
                p.paragraph_format.keep_with_next = (
                    i == 0 or (len(table.rows) <= 6 and i < len(table.rows)-1)
                )
                for run in p.runs:
                    run.font.size = Pt(9 if len(table.columns) == 7 else 10)
                    if i == 0:
                        run.bold = True
                        run.font.color.rgb = RGBColor(0, 0, 0)
doc.save(path)
print(f'DOCX impaginato: {path.name}, {len(doc.tables)} tabelle')
