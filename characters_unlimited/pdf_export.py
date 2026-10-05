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
from .advancement import learning_key


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
    baseline = max(1, (height - size) / 2)
    if widget.get('/T') == 'CRITICAL STRIKE':
        canvas.drawRightString(width - 1, baseline, visible)
    else:
        canvas.drawString(1, baseline, visible)
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
            rect = widget.get('/Rect', [])
            if (page_number == 1 and len(rect) == 4
                    and abs(float(rect[0])-533.018) < .2 and abs(float(rect[1])-322.582) < .2):
                # The reference mistakenly defines the numeric Prowl penalty as a checkbox.
                widget[NameObject('/FT')] = NameObject('/Tx')
                widget[NameObject('/Ff')] = NumberObject(0)
                widget.pop('/AS', None)
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
        for name, percentage, rate in [(label, row.get('percentage'), row.get('per_level')),
                                 *[(label + ': ' + check['name'], check['percentage'], check.get('per_level', row['per_level']))
                                   for check in row.get('additional_checks', [])]]:
            if slot < len(names) and stringWidth(name, 'Helvetica', 7) <= 132:
                values[names[slot]['/T']] = name
                values[rates[slot]['/T']] = '' if rate is None else str(rate)
                values[percentages[slot]['/T']] = '' if percentage is None else str(percentage)
                slot += 1
            else:
                overflow.extend(wrap_lines(name+' (Physical bonuses)' if percentage is None else f'{name}: {percentage}% (+{rate}% per level)', 530))
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


def fill_combat_conditions(page, conditions, values):
    cells = [('critical',218.509,635.949,'CRITICAL STRIKE'),
             ('knockout',226.44,646.4,'COMBAT KNOCK OUT'),
             ('death_blow',210.48,626.96,'DEATH')]
    for identifier, x, y, name in cells:
        result = conditions.get(identifier)
        if not result:
            continue
        matches = [ref.get_object() for ref in page.get('/Annots', [])
                   if abs(float(ref.get_object()['/Rect'][0])-x) < .2
                   and abs(float(ref.get_object()['/Rect'][1])-y) < .2]
        if len(matches) != 1:
            raise ValueError('The Rifts combat rectangles changed; review the sheet mapping')
        matches[0][NameObject('/T')] = TextStringObject(name)
        low, high = result['natural_min'], result['natural_max']
        if identifier == 'critical':
            # The reference prints the range's final 20 outside this widget.
            # Keep that artwork and right-align the editable prefix beside it.
            if high != 20:
                raise ValueError('Review the printed Critical suffix for this natural range')
            matches[0][NameObject('/Q')] = NumberObject(2)
            matches[0][NameObject('/TU')] = TextStringObject('Natural roll prefix; the sheet prints the final 20')
            values[name] = f'Natural {low}–' if low != high else 'Natural'
        else:
            values[name] = f'Natural {low}' + (f'–{high}' if low != high else '')


def append_continuation(writer, lines, title='RIFTS CHARACTER SHEET - CONTINUATION'):
    if not lines:
        return
    if len(lines) > 12000:
        raise ValueError('PDF exceeds 200 continuation pages; split the character notes before exporting')
    stream = BytesIO()
    canvas = Canvas(stream, pagesize=(612, 792))
    for start in range(0, len(lines), 60):
        page = start // 60 + 3
        canvas.setFont('Times-Bold', 14)
        canvas.drawCentredString(306, 756, title)
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
            if value is not None and (not value.isascii() or widget.get('/T') == 'CRITICAL STRIKE'):
                unicode_appearance(writer, widget, value)


def fill_equipment(page, equipment, values):
    """Map current possessions to verified weapon, armor and personal gear rectangles."""
    def cell(x, y, value):
        matches = [ref.get_object() for ref in page.get('/Annots',[])
                   if ref.get_object().get('/FT') == '/Tx'
                   and abs(float(ref.get_object()['/Rect'][0])-x)<.2
                   and abs(float(ref.get_object()['/Rect'][1])-y)<.2]
        if len(matches)!=1:
            raise ValueError('The Rifts equipment rectangle changed; review its field mapping')
        values[matches[0]['/T']] = str(value)
    weapons = [item for item in equipment['items'] if item['category']=='weapon']
    rectangles = [((37.92,345.458),(121.637,345.578),(148.146,345.578),(179.455,345.578),(61.20,336.85)),
                  ((37.451,328.658),(121.168,328.778),(147.677,328.778),(178.986,328.778),(60.731,320.05)),
                  ((37.451,311.64),(121.168,311.759),(147.677,311.759),(178.986,311.76),(60.731,303.032))]
    for item, cells in zip(weapons,rectangles):
        melee = item.get('weapon_kind') == 'melee'
        active = next((attack for attack in equipment['melee_attacks']
                       if attack['possession_id'] == item['id']), None)
        damage = active['damage'] if active else item['damage']
        if 'Pending' in damage:
            damage = ''
        for position, value in zip(cells,[item['name'],'Melee' if melee else str(item['range_feet'])+' ft',
                                       '' if melee else str(item['shots'])+'/'+str(item['capacity']),damage,
                                       ('' if melee else 'Standard E-Clip; ')+str(item['quantity'])+' item(s), '+item['location']]):
            cell(*position,value)
    personal_gear = [item for item in equipment['items'] if item['category'] in ('gear', 'ammunition')]
    gear_rows = [202.44,193.44,185.52,177,168,159.48,150.96,143.04,134.52,125.52,
                 117,108.96,100.44,91.44,83.04,75,66.48,57.48,48.96,40.44]
    for item, y in zip(personal_gear,gear_rows):
        cell(36.48,y,item['name']+' x'+str(item['quantity'])+'; '+item['location']+
             ('; '+str(item['shots'])+'/'+str(item['capacity'])+' shots' if item['category']=='ammunition' else ''))
    armor = equipment['armor']
    if len(armor)==1 and armor[0]['quantity']==1:
        item = armor[0]
        values.update({'ARMOR':item.get('sheet_name',item['name']),'COST':str(item['cost_credits']),
                       'WEIGHT 1':str(item['weight_lbs'])+' lb',
                       'undefined_7':str(item['locations']['main_body']),
                       'undefined_8':str(item['locations']['main_body'])})
        if item.get('prowl_penalty') is not None:
            cell(533.018,322.582,item['prowl_penalty'])


def resource_source_citation(source):
    parts = [source['book']]
    for label, plural, singular in [('printed pp.', 'pages', 'printed_page'),
                                    ('PDF pp.', 'pdf_pages', 'pdf_page')]:
        pages = source.get(plural, [source[singular]] if source.get(singular) is not None else [])
        if pages:
            parts.append(label + ' ' + ', '.join(map(str, pages)))
    if source.get('section'):
        parts.append(source['section'])
    return ', '.join(parts)


def export_rifts_sheet(character, core, skills, combat):
    writer = PdfWriter()
    writer.clone_document_from_reader(PdfReader(TEMPLATE))
    independent_fields(writer)
    race = next(item['name'] for item in core['races'] if item['id'] == character['race'])
    occupation = next(item['name'] for item in core['classes'] if item['id'] == character['character_class'])
    values = {'NAME': character['name'], 'RACE': race, 'OCC': occupation,
              'EXPERIENCE LEVEL': str(character['level'])}
    values.update({name: str(value['value']) for name, value in character['attributes'].items()})
    resources = skills.get('resources',{}).get('resources',{})
    if resources.get('HP',{}).get('value') is not None:
        values['HIT POINTS'] = str(resources['HP']['value'])
    if resources.get('SDC',{}).get('value') is not None:
        cells = [ref.get_object() for ref in writer.pages[0].get('/Annots',[])
                 if abs(float(ref.get_object()['/Rect'][0])-512.64)<.2
                 and abs(float(ref.get_object()['/Rect'][1])-682.64)<.2]
        if len(cells)!=1:
            raise ValueError('The Rifts physical S.D.C. rectangle changed; review its field mapping')
        values[cells[0]['/T']] = str(resources['SDC']['value'])
    saving_bonuses = combat.get('saving_bonuses', {})
    fill_saving_bonuses(writer.pages[0], saving_bonuses, values)
    fill_combat_conditions(writer.pages[0], combat.get('conditions', {}), values)
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
        attack_field = {'punch': 'PUNCH', 'kick': 'KICK', 'power-punch': 'POWER PUNCH',
                        'leap-kick':'LEAP KICK','body-flip':'BODY FLIP THROW'}.get(attack['id'])
        if attack_field and 'Pending' not in attack['damage']:
            values[attack_field] = attack['damage'].removesuffix(' S.D.C.').replace(' × ', 'x')
    rows = [row for row in skills['grants'] if row['id'] != 'native-language' or row.get('specialty')]
    rows.extend(row for row in skills['selected'] if row['pool'] != 'secondary')
    overflow = fill_skills(writer.pages[0], rows, 220, values)
    secondary = [row for row in skills['selected'] if row['pool'] == 'secondary']
    overflow.extend(fill_skills(writer.pages[0], secondary, 404, values))
    sheet_notes = character['notes']
    if 'experience' in character:
        sheet_notes += '\nExperience: ' + str(character['experience']) + ' XP.'
    if character.get('advancement'):
        record = character['advancement']
        sheet_notes += ('\nLevel-two advancement HP die: ' + str(record['hp_roll']) +
                        (' (active).' if record['active'] else ' (undone; retained for replay).'))
        for event in character.get('later_advancements', []):
            sheet_notes += ('\nLevel-' + str(event['level']) + ' advancement HP die: ' + str(event['hp_roll']) +
                            (' (active).' if event['level'] <= character['level'] else ' (undone; retained for replay).'))
        for skill in [*skills['grants'], *skills['selected']]:
            learned = character.get('learning_levels', {}).get(learning_key('skill', skill['id'], skill.get('specialty', '')))
            if learned is not None:
                sheet_notes += '\n' + skill['name'] + (' - ' + skill['specialty'] if skill.get('specialty') else '') + ': learned at level ' + str(learned) + '.'
    for attack in combat.get('unarmed', []):
        if attack['id'] not in ('punch', 'kick', 'power-punch'):
            sheet_notes += '\n' + attack['name'] + ': ' + (attack['damage'] or 'No damage') + '; ' + str(attack['actions']) + ' action(s). Ultimate Edition pp. 345, 348.'
    if combat.get('notes'):
        sheet_notes += '\nCombat conditions (Ultimate Edition pp. 341, 344–348, 361):\n' + '\n'.join(combat['notes'])
    equipment = skills.get('equipment')
    if equipment is not None:
        fill_equipment(writer.pages[0],equipment,values)
        weight_label = 'Carried weight' if equipment['carried_weight_complete'] else 'Known carried weight'
        sheet_notes += '\nCurrent credits: '+str(equipment['inventory']['credits'])+'. '+weight_label+': '+str(equipment['carried_weight_lbs'])+' lb.'
        if not equipment['carried_weight_complete']:
            sheet_notes += '\n'+str(equipment['unknown_carried_weight_quantity'])+' carried item(s) have unspecified weight; the weight total is incomplete.'
        for identifier, record in equipment['starting_funds']['funds'].items():
            definition = next(item for item in equipment['starting_funds']['definitions'] if item['id']==identifier)
            sheet_notes += ('\n'+definition['name']+': '+str(record['value'])+' credits = ('+
                            ' + '.join(map(str,record['rolls']))+') x'+str(definition['multiplier'])+'. '+record['source']['book']+
                            ', p. '+', '.join(map(str,record['source']['pages']))+'.')
        if equipment['starting_funds']['generated']:
            item_definition = next(item for item in equipment['starting_funds']['definitions'] if item['id']=='saleable_goods')
            sheet_notes += '\n'+item_definition['name']+' remains recorded item value; it is not added to current credits automatically.'
        if equipment['starting_choices']['generated']:
            starting = equipment['starting_choices']
            names = {item['id']: item['name'] for item in equipment['catalog']}
            sheet_notes += '\nOriginal free starting equipment choices: '+ '; '.join(
                names[grant['item_id']]+' x'+str(grant['quantity']) for grant in starting['grants'])+'.'
            sheet_notes += ' '+starting['source']['book']+', p. '+', '.join(map(str,starting['source']['pages']))+'.'
            sheet_notes += ' '+' '.join(starting['guidance'])
        names = {item['id']: item['name'] for item in equipment['catalog']}
        for group in equipment['starting_groups']['groups']:
            if group['generated']:
                receipt = group['receipt']
                sheet_notes += '\nOriginal '+group['name'].lower()+': '+names[receipt['selection']]+' x'+str(group['quantity'])+'.'
                sheet_notes += ' '+receipt['source']['book']+', p. '+', '.join(map(str,receipt['source']['pages']))+'.'
                sheet_notes += ' '+' '.join(group['guidance'])
        if equipment['starting_gear']['generated']:
            gear = equipment['starting_gear']
            names = {item['id']: item['name'] for item in equipment['catalog']}
            sheet_notes += '\nOriginal personal starting gear grant: '+ '; '.join(
                names[grant['item_id']]+' x'+str(grant['quantity']) for grant in gear['grants'])+'.'
            sheet_notes += ' '+gear['source']['book']+', p. '+', '.join(map(str,gear['source']['pages']))+'. Current possessions may be edited or removed; the original grant is retained.'
            sheet_notes += ' '+' '.join(gear['guidance'])
        for item in equipment['items']:
            sheet_notes += ('\n'+item['name']+' x'+str(item['quantity'])+'; '+item['location']+
                            ('; equipped' if item['equipped'] else '; unequipped')+
                              '; '+('weight unspecified' if item['weight_lbs'] is None else str(item['weight_lbs'])+' lb each')+'. '+item['source']['book']+
                            ', p. '+', '.join(map(str,item['source']['pages']))+'.')
            if item['category']=='weapon':
                if item.get('weapon_kind') == 'melee':
                    sheet_notes += ' Base damage '+item['damage']+'; melee weapon. Equipped totals follow below.'
                else:
                    sheet_notes += (' '+item['damage']+'; range '+str(item['range_feet'])+' ft / '+str(item['range_meters'])+
                                    ' m; shots per item '+str(item['shots'])+'/'+str(item['capacity'])+'.')
            elif item['category'] == 'ammunition':
                sheet_notes += ' '+str(item['shots'])+'/'+str(item['capacity'])+' shots per clip with reviewed compatible weapons: '+', '.join(item['compatible_weapons'])+'.'
            elif item['category'] == 'armor':
                sheet_notes += ' '+', '.join(name.replace('_',' ')+' '+str(value)+' M.D.C.' for name,value in item['locations'].items())+'.'
                sheet_notes += ' Movement skill penalty '+str(item['movement_penalty'])+'%; not a universal speed penalty.'
                if item.get('environmental') is not None:
                    sheet_notes += ' '+('Environmental' if item['environmental'] else 'Non-environmental')+' armor.'
                sheet_notes += ' '+' '.join(item.get('protection_notes', []))
        for attack in equipment['attacks']:
            sheet_notes += '\n'+attack['name']+': '+ '; '.join(
                context+' strike '+(str(attack[context]['value']) if attack[context]['value'] is not None else 'pending')+
                ' ('+', '.join(name.replace('_',' ')+' '+str(value) for name,value in attack[context]['contributions'].items())+
                '); '+str(attack[context]['actions'])+' action(s)' for context in ('single','aimed'))+'.'
        for attack in equipment['melee_attacks']:
            sheet_notes += '\n'+attack['name']+': '+ '; '.join(
                context+' '+(str(attack[context]['value']) if attack[context]['value'] is not None else 'pending')+
                ' ('+', '.join(name.replace('_',' ')+' '+str(value) for name,value in attack[context]['contributions'].items())+')'
                for context in ('strike','parry'))+'; damage '+attack['damage']+'. '+attack['guidance']
            sheet_notes += ' Damage bonus: '+', '.join(name.replace('_',' ')+' '+str(value)
                for name,value in attack['damage_bonus']['contributions'].items())+'. '+ '; '.join(
                source['book']+', pp. '+', '.join(map(str,source['pages']))
                for source in attack['damage_bonus']['sources'])+'.'
        sheet_notes += '\n'+' '.join([*equipment['warnings'],*equipment['guidance']])
    for identifier,result in resources.items():
        if result['value'] is None:
            continue
        terms = [f'{name}: {value}'+(' (dice '+', '.join(map(str,result['rolls'][name]))+')' if result['rolls'][name] else '')
                 for name,value in result['contributions'].items()]
        if result['fixed'] is not None:
            terms.append('Fixed total: '+str(result['fixed']))
        elif result['adjustment']:
            terms.append('Player adjustment: '+str(result['adjustment']))
        references = list(dict.fromkeys(resource_source_citation(source) for source in result['sources']))
        sheet_notes += '\n'+result['name']+': '+'; '.join([*terms,*references])+'.'
    if combat.get('class_bonuses'):
        perception = combat['class_bonuses']['perception']
        perception_references = '; '.join(source['book']+', pp. '+', '.join(map(str,source['pages'])) for source in perception['sources'])
        sheet_notes += '\nPerception O.C.C. bonus: +'+str(perception['value'])+' ('+perception_references+'). Other Perception contributions remain separate.'
    for skill in skills.get('selected',[]):
        if skill.get('selection_cost',1) > 1:
            cost_source = skill['selection_cost_source']
            sheet_notes += f"\n{skill['name']}: uses {skill['selection_cost']} {skill['pool']} selections. "+cost_source['book']+', pp. '+', '.join(map(str,cost_source['pages']))+'.'
    for skill in skills.get('physical',{}).get('selected',[]):
        effects = []
        for group,bonuses in skill['effects'].items():
            for name,effect in bonuses.items():
                value = effect['value'] if isinstance(effect,dict) else effect
                label = ('S.D.C. bonus' if resources.get('SDC',{}).get('value') is not None else 'S.D.C. bonus (starting total pending)') if group=='resources' and name=='SDC' else name.replace('_',' ')
                rolls = effect.get('rolls',[]) if isinstance(effect,dict) else []
                effects.append(f'{label} +{value}'+(' (dice '+', '.join(map(str,rolls))+')' if rolls else ''))
        sheet_notes += '\n'+skill['name']+': '+'; '.join(effects)+'. '+skill['source']['book']+', p. '+', '.join(map(str,skill['source']['pages']))+'.'
        if skill.get('notes'):
            sheet_notes += ' ' + ' '.join(skill['notes'])
        for activity in skill.get('activities', []):
            sheet_notes += '\n' + activity['name'] + ': ' + activity['guidance']
    if saving_bonuses:
        sheet_notes += '\nSaving fields show reviewed bonuses.'
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
        if 'thrown' in weapon:
            thrown = weapon['thrown']['value']
            overflow.append(f'{weapon["name"]}: thrown strike {thrown if thrown is not None else ""}')
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
