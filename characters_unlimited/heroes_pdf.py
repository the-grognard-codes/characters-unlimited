"""A ruled, editable Heroes Unlimited sheet for the reviewed character projection."""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import black, white
from reportlab.pdfgen.canvas import Canvas

from .pdf_export import append_continuation, fill_values, install_editing_font, wrap_lines


def export_heroes_sheet(character, core, education, programs, power_budget=None, powers=None, resources=None):
    stream = BytesIO()
    canvas = Canvas(stream, pagesize=(612, 792))
    canvas.setTitle('Heroes Unlimited character sheet')
    values = {}
    overflow = []

    def heading(text, x, y, width):
        canvas.setFont('Times-Bold', 11)
        canvas.drawCentredString(x + width/2, y, text)
        canvas.line(x, y-4, x+width, y-4)

    def field(name, x, y, width, height=12, value='', multiline=False):
        canvas.acroForm.textfield(name=name, value='', x=x, y=y, width=width, height=height,
            fontName='Helvetica', fontSize=8, borderWidth=0, textColor=black, fillColor=white,
            forceBorder=False, fieldFlags='multiline' if multiline else '')
        canvas.line(x, y, x+width, y)
        if value != '':
            values[name] = str(value)

    def labelled(label, name, x, y, width, value=''):
        canvas.setFont('Times-Bold', 9)
        canvas.drawString(x, y+3, label)
        offset = canvas.stringWidth(label, 'Times-Bold', 9) + 4
        field(name, x+offset, y, width-offset, value=value)

    def page_header(number):
        canvas.setFont('Times-Bold', 18)
        canvas.drawCentredString(306, 754, 'HEROES UNLIMITED')
        canvas.setFont('Times-Roman', 10)
        canvas.drawCentredString(306, 738, 'REVISED SECOND EDITION CHARACTER SHEET')
        canvas.setFont('Times-Roman', 7)
        canvas.drawString(40, 27, 'Characters Unlimited · Personal character sheet')
        canvas.drawRightString(572, 27, f'Page {number}')

    page_header(1)
    heading('Saving Throws', 40, 716, 140)
    for index, (label, key) in enumerate([('Magic', 'SAVE_MAGIC'), ('Psionics', 'SAVE_PSIONICS'),
            ('Poison', 'SAVE_POISON'), ('Insanity', 'SAVE_INSANITY'), ('Coma / death', 'SAVE_COMA')]):
        save_id = {'SAVE_PSIONICS':'psionics','SAVE_INSANITY':'insanity'}.get(key)
        save = (powers or {}).get('saving_bonuses',{}).get(save_id,{})
        value = f"{save['value']:+d}" if save.get('value') is not None else ''
        if value and save.get('target') is not None:
            value += f"; target {save['target']}"
        labelled(label, key, 40, 691-index*20, 140, value)
    heading('Combat Skill', 198, 716, 150)
    labelled('Training', 'COMBAT_SKILL', 198, 691, 150)
    for index, (label, key) in enumerate([('Attacks', 'ATTACKS'), ('Initiative', 'INITIATIVE'),
            ('Strike', 'STRIKE'), ('Parry', 'PARRY'), ('Dodge', 'DODGE'), ('Damage bonus', 'DAMAGE')]):
        labelled(label, key, 198, 667-index*20, 150)
    heading('Identity', 366, 716, 206)
    race = next(row['name'] for row in core['races'] if row['id'] == character['race'])
    category = next(row['name'] for row in core['classes'] if row['id'] == character['character_class'])
    outcome = education['outcome']
    for index, (label, key, value) in enumerate([
            ('Name', 'NAME', character['name']), ('Origin', 'RACE', race),
            ('Power category', 'CATEGORY', category), ('Level', 'LEVEL', character['level']),
            ('Education', 'EDUCATION', outcome['name'] if outcome else ''),
            ('Alignment', 'ALIGNMENT', ''), ('Occupation', 'OCCUPATION', '')]):
        labelled(label, key, 366, 691-index*20, 206, value)
    heading('Attributes', 40, 550, 308)
    for index, key in enumerate(('IQ', 'ME', 'MA', 'PS', 'PP', 'PE', 'PB', 'SPD')):
        labelled(key, key, 40+(index%4)*79, 526-(index//4)*23, 70, character['attributes'][key]['value'])
    resource_values = (resources or {}).get('resources', {})
    for label, name, y in [('Hit Points', 'HP', 526), ('Physical S.D.C.', 'SDC', 503), ('P.P.E.', 'PPE', 485)]:
        value = resource_values.get(name, {}).get('value')
        labelled(label, name, 366, y, 206, '' if value is None else value)
    heading('Education & Scholastic Programs', 40, 474, 532)
    names = {row['id']:row['name'] for row in programs['catalog']}
    program_names = '; '.join(f"Slot {row['slot']+1}: {names[row['program']]}" for row in programs['selections'])
    program_lines = wrap_lines(program_names, 530)
    for index, line in enumerate(program_lines[:2]):
        field('PROGRAMS' if index == 0 else 'PROGRAMS.1', 40, 453-index*11, 532, 10, line)
    if not program_lines:
        field('PROGRAMS', 40, 445, 532, 22)
    if len(program_lines) > 2:
        overflow.extend(['Scholastic programs (continued)', *program_lines[2:]])
    secondary = programs['secondary']
    labelled('Secondary choices used / allowed', 'SECONDARY_ALLOWANCE', 40, 423, 532,
             f"{secondary['used']} / {secondary['allowance']}" if outcome else '')
    heading('Powers & Special Abilities', 40, 390, 532)
    power_lines = []
    if power_budget and power_budget['selection']:
        power_lines = [power_budget['outcome']['name']]
        power_lines.extend(f"{row['name']}: {row['count']}" for row in power_budget['budgets'])
        power_lines.extend(power_budget['guidance'])
        power_lines.append(f"{power_budget['source']['book']}, printed p. 161 / PDF p. 162; {power_budget['rules']['id']} {power_budget['rules']['version']}")
        for selection in power_budget['history']:
            power_lines.append(f"Recorded outcome: {selection['id']}; {selection['method']}; percentile {selection.get('roll', 'none')}; D4 faces {selection['rolls']}")
    if powers:
        if powers['trust_intimidate'] is not None:
            power_lines.append(f"Effective M.A. trust/intimidate: {powers['trust_intimidate']}% (attribute chart, printed p.15 / PDF p.16)")
        if powers.get('charm_impress') is not None:
            source = powers['charm_source']
            power_lines.append(f"Effective P.B. charm/impress: {powers['charm_impress']}% ({source['book']}, printed p.{source['printed_page']} / PDF p.{source['pdf_page']})")
        for power in powers['powers']:
            power_lines.append(f"{power['name']}: recorded target {power['target']}; dice {power['rolls']}; Minor")
            power_lines.extend(power['guidance'])
            power_lines.append(f"{power['source']['book']}, printed p.{power['source']['printed_page']} / PDF p.{power['source']['pdf_page']}")
        for receipt in powers['receipts']:
            if not receipt['active']:
                power_lines.append(f"Retained inactive power: {receipt['name']}; target {receipt['target']}; dice {receipt['rolls']}")
                power_lines.append(f"{receipt['source']['book']}, printed p.{receipt['source']['printed_page']} / PDF p.{receipt['source']['pdf_page']}")
        if powers['powers']:
            power_lines.append(f"Minor selections: {powers['minor']['used']} used / {powers['minor']['allowance']} allowed")
        for save in powers.get('saving_bonuses',{}).values():
            bonus = f"{save['value']:+d}" if save['value'] is not None else 'unreviewed'
            target = f"; roll target {save['target']}" if save['target'] is not None else '; target depends on the triggering rule'
            parts = '; '.join(f'{label} {amount:+d}' for label,amount in save['contributions'].items())
            power_lines.append(f"{save['name']}: {bonus}{target}; {parts}")
            power_lines.extend(f"{source['book']}, printed p.{source['printed_page']} / PDF p.{source['pdf_page']}" for source in save['sources'])
        power_lines.extend(powers.get('saving_notes',[]))
        power_lines.extend(powers['warnings'])
    wrapped_powers = [line for text in power_lines for line in wrap_lines(text, 530)]
    field('POWERS', 40, 242, 532, 137, value='\n'.join(wrapped_powers[:10]), multiline=True)
    if len(wrapped_powers) > 10:
        overflow.extend(['Power outcome and starting allowance (continued)', *wrapped_powers[10:]])
    heading('Weapons & Combat Effects', 40, 212, 310)
    field('WEAPONS', 40, 58, 310, 143, multiline=True)
    heading('Armor & Protection', 368, 212, 204)
    field('ARMOR', 368, 58, 204, 143, multiline=True)
    canvas.showPage()

    page_header(2)
    for secondary_column, x in ((False, 40), (True, 314)):
        heading('Secondary Skills' if secondary_column else 'Skills & Program Grants', x, 716, 258)
        canvas.setFont('Times-Roman', 8)
        canvas.drawString(x, 697, 'Skill')
        canvas.drawString(x+194, 697, '+%/Lv')
        canvas.drawString(x+234, 697, '%')
        rows = [row for row in programs['skills'] if bool(row['secondary_selected']) == secondary_column]
        slot = 0
        for row in rows:
            checks = [('', row['name'], row['percentage'], row['per_level']),
                *[(f'.check{index}', row['name']+': '+check['name'], check['percentage'], check['per_level'])
                  for index, check in enumerate(row.get('additional_checks', []))]]
            for suffix, label, percentage, rate in checks:
                if slot >= 20:
                    overflow.extend(wrap_lines(f'{label}: {percentage}% (+{rate}% per level)', 530))
                    continue
                y = 677-slot*16
                key = 'skills.'+row['id']+suffix
                field(key+'.name', x, y, 188, value=label)
                field(key+'.rate', x+194, y, 27, value=rate)
                field(key+'.percentage', x+228, y, 30, value=percentage)
                slot += 1
        for index in range(slot, 20):
            y = 677-index*16
            key = f'blank-skills.{secondary_column}.{index}'
            field(key+'.name', x, y, 188)
            field(key+'.rate', x+194, y, 27)
            field(key+'.percentage', x+228, y, 30)
    heading('Equipment & Money', 40, 343, 532)
    field('EQUIPMENT', 40, 224, 532, 108, multiline=True)
    heading('Character Notes & Rule References', 40, 199, 532)
    lines = wrap_lines(character['notes'], 530)
    lines += wrap_lines('Rules: '+character['rules']['id']+' '+character['rules']['version']+'; '+
        '; '.join(f'{key} {version}' for key, version in character.get('additional_rule_packs', {}).items()), 530)
    lines += wrap_lines('Education: '+education['source']['book']+', pp. '+
                        ', '.join(map(str, education['source']['pages'])), 530)
    lines += wrap_lines('Skills: '+programs['source']['book']+', pp. '+
                        ', '.join(map(str, programs['source']['pages'])), 530)
    if outcome:
        for slot in outcome['program_slots']:
            bonus = '' if slot['bonus'] is None else f"; +{slot['bonus']}%"
            lines.extend(wrap_lines('Program allowance: '+slot['name']+'; '+slot['restriction']+bonus, 530))
    skill_names = {row['id']:row['name'] for row in programs['skill_catalog']}
    for selection in programs['selections']:
        for group, choices in selection.get('choices', {}).items():
            lines.extend(wrap_lines(f"Recorded choice: {names[selection['program']]} slot {selection['slot']+1} / {group}: "+
                         ', '.join(skill_names[identifier] for identifier in choices), 530))
    if secondary['selections']:
        lines.extend(wrap_lines('Recorded Secondary choices: '+
                     ', '.join(skill_names[identifier] for identifier in secondary['selections']), 530))
    lines += wrap_lines('Additional power, combat, resource and equipment automation remains pending. Ungenerated or unreviewed fields remain blank and editable.', 530)
    for skill in programs.get('physical', {}).get('selected', []):
        terms = []
        for group in ('attributes', 'resources'):
            for name, result in skill['effects'][group].items():
                terms.append(name+' +'+str(result['value'])+
                             (f" (dice {result['rolls']})" if result['rolls'] else ''))
        lines += wrap_lines('Physical: '+skill['name']+'; '+', '.join(terms), 530)
        source = skill['source']
        lines += wrap_lines(source['book']+', printed pp. '+', '.join(map(str,source['pages']))+
                            ' / PDF pp. '+', '.join(map(str,source['pdf_pages'])), 530)
        for note in skill.get('guidance', []):
            lines += wrap_lines(skill['name']+': '+note, 530)
    if resources and resources['generated']:
        lines += wrap_lines('Starting resources retain recorded contributions; later attribute changes do not reroll them.', 530)
        for result in resources['resources'].values():
            terms = []
            for name, value in result['contributions'].items():
                faces = result['rolls'][name]
                terms.append(name+': '+str(value)+(f' (dice {faces})' if faces else ''))
            lines += wrap_lines(result['name']+': '+str(result['value'])+'; '+'; '.join(terms), 530)
            for source in result['sources']:
                lines += wrap_lines(source['book']+', printed pp. '+', '.join(map(str,source['pages']))+
                                    ' / PDF pp. '+', '.join(map(str,source['pdf_pages'])), 530)
        for note in resources['guidance']:
            lines += wrap_lines(note, 530)
    for message in dict.fromkeys([*programs['warnings'], *programs['guidance']]):
        lines.extend(wrap_lines(message, 530))
    for skill in programs['skills']:
        for message in skill.get('guidance', []):
            lines.extend(wrap_lines(skill['name']+': '+message, 530))
    for index, line in enumerate(lines[:12]):
        field(f'NOTES.{index}', 40, 177-index*10, 532, 10, line)
    overflow.extend(lines[12:])
    canvas.showPage()
    canvas.save()
    writer = PdfWriter()
    writer.clone_document_from_reader(PdfReader(stream))
    fill_values(writer, values)
    append_continuation(writer, overflow, 'HEROES UNLIMITED CHARACTER SHEET - CONTINUATION')
    install_editing_font(writer)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()
