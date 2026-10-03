"""Editable Rifts sheets, preserving the supplied sheet's visual artwork."""

from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (ArrayObject, BooleanObject, DictionaryObject, NameObject,
                           NumberObject, TextStringObject, DecodedStreamObject)
from reportlab.lib.colors import black, white
from reportlab.pdfbase.pdfmetrics import stringWidth, registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas


TEMPLATE = Path(__file__).parent / 'templates' / 'rifts.pdf'
UNICODE_FONT = TTFont('RPGUnicode', str(Path(__file__).parent / 'fonts' / 'DroidSansFallback.ttf'))
registerFont(UNICODE_FONT)


def install_editing_font(writer):
    """Use BMP Unicode CIDs mapped to the bundled TrueType glyphs for editing."""
    def indirect(mapping):
        return writer._add_object(DictionaryObject({NameObject(key): value for key, value in mapping.items()}))

    font_data = DecodedStreamObject()
    font_data.set_data((Path(__file__).parent / 'fonts' / 'DroidSansFallback.ttf').read_bytes())
    descriptor = indirect({'/Type': NameObject('/FontDescriptor'), '/FontName': NameObject('/RPGUnicode'),
        '/Flags': NumberObject(4), '/FontBBox': ArrayObject([NumberObject(round(n)) for n in UNICODE_FONT.face.bbox]),
        '/ItalicAngle': NumberObject(0), '/Ascent': NumberObject(766), '/Descent': NumberObject(-239),
        '/CapHeight': NumberObject(715), '/StemV': NumberObject(87),
        '/FontFile2': writer._add_object(font_data.flate_encode())})
    glyph_map = DecodedStreamObject()
    glyph_map.set_data(b''.join(UNICODE_FONT.face.charToGlyph.get(code, 0).to_bytes(2, 'big')
                               for code in range(65536)))
    widths = ArrayObject()
    for code, width in sorted(UNICODE_FONT.face.charWidths.items()):
        if code <= 65535:
            widths.extend([NumberObject(code), ArrayObject([NumberObject(round(width))])])
    descendant = indirect({'/Type': NameObject('/Font'), '/Subtype': NameObject('/CIDFontType2'),
        '/BaseFont': NameObject('/RPGUnicode'), '/CIDSystemInfo': DictionaryObject({
            NameObject('/Registry'): TextStringObject('Adobe'), NameObject('/Ordering'): TextStringObject('Identity'),
            NameObject('/Supplement'): NumberObject(0)}), '/FontDescriptor': descriptor,
        '/CIDToGIDMap': writer._add_object(glyph_map.flate_encode()), '/W': widths})
    font = indirect({'/Type': NameObject('/Font'), '/Subtype': NameObject('/Type0'),
        '/BaseFont': NameObject('/RPGUnicode'), '/Encoding': NameObject('/Identity-H'),
        '/DescendantFonts': ArrayObject([descendant])})
    form = writer.root_object['/AcroForm']
    form['/DR']['/Font'][NameObject('/RPGUnicode')] = font
    for page in writer.pages:
        for reference in page.get('/Annots', []):
            widget = reference.get_object()
            if widget.get('/FT') == '/Tx':
                widget[NameObject('/DA')] = TextStringObject('/RPGUnicode 0 Tf 0 g')
                widget[NameObject('/DR')] = form['/DR']


def unicode_appearance(writer, widget, value):
    """Embed a portable font in the appearance; retain the original editable value.

    Rare characters outside the bundled font are shown as explicit Unicode codes
    rather than silent missing glyphs. Their original text remains in /V.
    """
    width = float(widget['/Rect'][2]) - float(widget['/Rect'][0])
    height = float(widget['/Rect'][3]) - float(widget['/Rect'][1])
    visible = ''.join(char if ord(char) in UNICODE_FONT.face.charToGlyph else f'[U+{ord(char):04X}]'
                      for char in value)
    size = min(8, max(1, height - 2))
    measured = stringWidth(visible, 'RPGUnicode', size)
    if measured > width - 2:
        size *= max(1, width - 2) / measured
    stream = BytesIO()
    canvas = Canvas(stream, pagesize=(width, height))
    canvas.setFont('RPGUnicode', size)
    canvas.drawString(1, max(1, (height - size) / 2), visible)
    canvas.showPage()
    canvas.save()
    page = PdfReader(stream).pages[0]
    appearance = DecodedStreamObject()
    contents = page.get_contents()
    assert contents is not None
    appearance.set_data(contents.get_data())
    appearance.update({NameObject('/Type'): NameObject('/XObject'),
                       NameObject('/Subtype'): NameObject('/Form'),
                       NameObject('/BBox'): ArrayObject([NumberObject(0), NumberObject(0),
                                                         page.mediabox[2], page.mediabox[3]]),
                       NameObject('/Resources'): page['/Resources'].clone(writer)})
    widget[NameObject('/V')] = TextStringObject(value)
    # PDF appearance streams must be indirect objects. pypdf exposes no public
    # registration method for a newly authored stream (dependency is pinned).
    widget[NameObject('/AP')] = DictionaryObject({NameObject('/N'): writer._add_object(appearance)})


def independent_fields(writer):
    """The reference shares parents across unrelated cells; separate each widget."""
    fields = ArrayObject()
    for page_number, page in enumerate(writer.pages, 1):
        for index, reference in enumerate(page.get('/Annots', [])):
            widget = reference.get_object()
            if widget.get('/Subtype') != '/Widget':
                continue
            parent = widget.get('/Parent')
            if parent:
                ancestor = parent.get_object()
                for key in ('/FT', '/DA', '/Ff', '/Q', '/MaxLen'):
                    if key not in widget and key in ancestor:
                        widget[NameObject(key)] = ancestor[key]
                widget[NameObject('/T')] = TextStringObject(f'page{page_number}.cell{index}')
                widget.pop('/Parent', None)
            widget.pop('/Kids', None)
            if widget.get('/FT') == '/Tx':
                # Siblings also share appearance streams in the reference. Regenerate
                # each filled cell independently, with readable black text.
                widget.pop('/AP', None)
                widget.pop('/DR', None)
                widget.pop('/MaxLen', None)
                widget[NameObject('/DA')] = TextStringObject('/Helv 0 Tf 0 g')
                widget[NameObject('/Ff')] = NumberObject(0)
            fields.append(reference)
    form = writer.root_object['/AcroForm']
    # The reference's Differences-only font omits its base encoding. Without
    # WinAnsi, regenerated ASCII appearances use incorrect glyph widths.
    form['/DR']['/Font']['/Helv'][NameObject('/Encoding')] = NameObject('/WinAnsiEncoding')
    form[NameObject('/Fields')] = fields
    form[NameObject('/NeedAppearances')] = BooleanObject(False)


def wrap_lines(text, width, size=8):
    lines = []
    for paragraph in text.split('\n'):
        line = ''
        for word in paragraph.split():
            if line and stringWidth(line + ' ' + word, 'Helvetica', size) > width:
                lines.append(line)
                line = ''
            # Split long unbroken words instead of clipping them at the field edge.
            while stringWidth(word, 'Helvetica', size) > width:
                split = 1
                while split < len(word) and stringWidth(word[:split + 1], 'Helvetica', size) <= width:
                    split += 1
                lines.append(word[:split])
                word = word[split:]
            line = (line + ' ' + word).strip()
        lines.append(line)
    return lines


def skill_cells(page, left):
    cells = [ref.get_object() for ref in page.get('/Annots', [])
             if ref.get_object().get('/Subtype') == '/Widget']
    return sorted([cell for cell in cells if abs(float(cell['/Rect'][0]) - left) < 2
                   and 360 < float(cell['/Rect'][1]) < 535],
                  key=lambda cell: float(cell['/Rect'][1]), reverse=True)


def fill_skills(page, rows, left, values):
    names, rates, percentages = (skill_cells(page, left + offset) for offset in (0, 136, 153))
    if not len(names) == len(rates) == len(percentages) == 20:
        raise ValueError('The Rifts sheet skill rectangles changed; review its field mapping')
    overflow = []
    slot = 0
    for row in rows:
        label = row['name'] + (' - ' + row['specialty'] if row.get('specialty') else '')
        for name, percentage, rate in [(label, row['percentage'], row['per_level']),
                                 *[(label + ': ' + check['name'], check['percentage'], check.get('per_level', row['per_level']))
                                   for check in row.get('additional_checks', [])]]:
            if slot < len(names) and stringWidth(name, 'Helvetica', 7) <= 132:
                values[names[slot]['/T']] = name
                values[rates[slot]['/T']] = str(rate)
                values[percentages[slot]['/T']] = str(percentage)
                slot += 1
            else:
                overflow.extend(wrap_lines(f'{name}: {percentage}% (+{rate}% per level)', 530))
    return overflow


def fill_saving_bonuses(page, bonuses, values):
    # The reference's saving cells have shared or generic names; use their
    # original geometry after normalization instead of those ambiguous names.
    cells = [('magic',134.6,720), ('magic',134.6,711.1), ('psionics',134.5,701.1),
             ('poison',134.8,691.1), ('poison',159.4,690.8), ('drugs',134.8,681),
             ('insanity',134.8,671), ('possession',140.5,660.5),
             ('horror_factor',140.7,651), ('coma_death',140.5,641)]
    for identifier, x, y in cells:
        result = bonuses.get(identifier)
        if not result or result['value'] is None:
            continue
        matches = [ref.get_object() for ref in page.get('/Annots', [])
                   if abs(float(ref.get_object()['/Rect'][0])-x) < .2
                   and abs(float(ref.get_object()['/Rect'][1])-y) < .2]
        if len(matches) != 1:
            raise ValueError('The Rifts saving rectangles changed; review the sheet mapping')
        values[matches[0]['/T']] = f'{result["value"]:+d}'


def append_continuation(writer, lines):
    if not lines:
        return
    if len(lines) > 12000:
        raise ValueError('PDF exceeds 200 continuation pages; split the character notes before exporting')
    stream = BytesIO()
    canvas = Canvas(stream, pagesize=(612, 792))
    for start in range(0, len(lines), 60):
        page = start // 60 + 3
        canvas.setFont('Times-Bold', 14)
        canvas.drawCentredString(306, 756, 'RIFTS CHARACTER SHEET - CONTINUATION')
        canvas.setFont('Times-Roman', 9)
        canvas.drawString(40, 736, 'Skills and character notes')
        for index, line in enumerate(lines[start:start + 60]):
            y = 716 - index * 11
            canvas.line(40, y - 1, 572, y - 1)
            canvas.acroForm.textfield(name=f'continuation.{start + index}', value='',
                                      x=40, y=y, width=532, height=10, fontName='Helvetica',
                                      fontSize=8, borderWidth=0, textColor=black,
                                      fillColor=white, forceBorder=False)
        canvas.drawRightString(572, 34, f'Page {page}')
        canvas.showPage()
    canvas.save()
    writer.append(PdfReader(stream))
    values = {f'continuation.{index}': line for index, line in enumerate(lines)}
    fill_values(writer, values)


def fill_values(writer, values):
    ascii_values = {key: (value, '/Helv', 0) for key, value in values.items() if value.isascii()}
    writer.update_page_form_field_values(None, ascii_values, auto_regenerate=False)
    for page in writer.pages:
        for reference in page.get('/Annots', []):
            widget = reference.get_object()
            value = values.get(widget.get('/T'))
            if value is not None and not value.isascii():
                unicode_appearance(writer, widget, value)


def export_rifts_sheet(character, core, skills, combat):
    writer = PdfWriter()
    writer.clone_document_from_reader(PdfReader(TEMPLATE))
    independent_fields(writer)
    race = next(item['name'] for item in core['races'] if item['id'] == character['race'])
    occupation = next(item['name'] for item in core['classes'] if item['id'] == character['character_class'])
    values = {'NAME': character['name'], 'RACE': race, 'OCC': occupation,
              'EXPERIENCE LEVEL': str(character['level'])}
    values.update({name: str(value['value']) for name, value in character['attributes'].items()})
    saving_bonuses = combat.get('saving_bonuses', {})
    fill_saving_bonuses(writer.pages[0], saving_bonuses, values)
    labels = {'attacks': 'OF ATTACKS', 'initiative': 'INNITIATIVE', 'damage': 'DAMAGE',
              'strike': 'STRIKE', 'parry': 'PARR Y', 'dodge': 'DODGE',
              'roll_with_impact': 'ROLL', 'pull_punch': 'RESTR PUNCH'}
    for stat, field in labels.items():
        result = combat['totals'].get(stat, {}).get('value')
        if result is not None:
            values[field] = str(result)
    if combat.get('catalog'):
        hand = next(item for item in combat['catalog']['hand_to_hand']
                    if item['id'] == combat['choices']['hand_to_hand'])
        values['COMBAT SKILL'] = hand['name'].removeprefix('Hand to Hand: ')
    for attack in combat.get('unarmed', []):
        attack_field = {'punch': 'PUNCH', 'kick': 'KICK', 'power-punch': 'POWER PUNCH'}.get(attack['id'])
        if attack_field and 'Pending' not in attack['damage']:
            values[attack_field] = attack['damage'].removesuffix(' S.D.C.').replace(' × ', 'x')
    rows = [row for row in skills['grants'] if row['id'] != 'native-language' or row.get('specialty')]
    rows.extend(row for row in skills['selected'] if row['pool'] != 'secondary')
    overflow = fill_skills(writer.pages[0], rows, 220, values)
    secondary = [row for row in skills['selected'] if row['pool'] == 'secondary']
    overflow.extend(fill_skills(writer.pages[0], secondary, 404, values))
    sheet_notes = character['notes']
    if saving_bonuses:
        sheet_notes += '\nSaving fields show attribute bonuses.'
        additional = [f'{saving_bonuses[key]["name"]}: {saving_bonuses[key]["value"]:+d}'
                      for key in ('disease', 'illusions') if saving_bonuses[key]['value'] is not None]
        sheet_notes += '\n' + '; '.join(additional)
        # Keep source exceptions and fatigue context with the editable values,
        # including on continuation pages when the player's notes fill the sheet.
        sheet_notes += '\n' + '\n'.join(combat.get('saving_notes', [])[1:])
    notes = wrap_lines(sheet_notes.strip(), 172)
    for index, line in enumerate(notes[:7], 1):
        values[f'NOTES {index}'] = line
    if len(notes) > 7:
        overflow.extend(['Character notes (continued)', *wrap_lines('\n'.join(notes[7:]), 530)])
    for weapon in combat.get('melee', []):
        strike, parry = (weapon[stat]['value'] for stat in ('strike', 'parry'))
        overflow.append(f'{weapon["name"]}: strike {strike if strike is not None else ""}; parry {parry if parry is not None else ""}')
    for weapon in combat.get('shooting', []):
        if weapon['trained']:
            contexts = [f'{context}: {weapon[context]["value"] if weapon[context]["value"] is not None else ""}'
                        for context in ('single', 'aimed', 'burst', 'wild')]
            overflow.append(weapon['name'] + ' - ' + '; '.join(contexts))
    # Auto-size the appearance to the original field rectangles; keep canonical values.
    fill_values(writer, values)
    append_continuation(writer, overflow)
    install_editing_font(writer)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()
