"""Reviewed Heroes scholastic grants, separate from Rifts class skill pools."""

from copy import deepcopy
from collections import Counter

from .education import project_education
from .proficiency import project_proficiency


def validate_program_selections(selections, pack):
    if not isinstance(selections, list) or len(selections) > 100:
        raise ValueError('Select at most 100 program entries')
    programs = {item['id'] for item in pack['programs']}
    for selection in selections:
        if (not isinstance(selection, dict) or set(selection) != {'slot', 'program'}
                or type(selection['slot']) is not int or not 0 <= selection['slot'] < 100
                or not isinstance(selection['program'], str) or selection['program'] not in programs):
            raise ValueError('Select an available program and a whole-number education slot')
    return deepcopy(selections)


def validate_secondary_selections(selections, pack):
    if 'secondary' not in pack:
        raise ValueError('Review and apply current program rules before selecting Secondary skills')
    identifiers = {skill['id'] for skill in pack['skills']}
    if (not isinstance(selections,list) or len(selections)>100
            or any(not isinstance(item,str) or item not in identifiers for item in selections)):
        raise ValueError('Select at most 100 available Secondary skill entries')
    return list(selections)


def project_programs(character, pack, education_pack):
    education = project_education(character.get('education'), education_pack)
    outcome = education['outcome']
    slots = outcome['program_slots'] if outcome else []
    selections = validate_program_selections(character.get('hero_program_selections', []), pack)
    warnings = []
    bonuses = {identifier:0 for identifier in pack['universal_skill_ids']}
    secondary_rules = pack.get('secondary')
    secondary_choices = (validate_secondary_selections(character.get('hero_secondary_selections',[]),pack)
                         if secondary_rules else [])
    for identifier in secondary_choices:
        bonuses.setdefault(identifier,0)
    seen_programs, seen_slots = set(), set()
    for selection in selections:
        program = next(item for item in pack['programs'] if item['id'] == selection['program'])
        slot = slots[selection['slot']] if selection['slot'] < len(slots) else None
        if selection['program'] in seen_programs:
            warnings.append(f"Repeated {program['name']} program retained. Its four remaining-category choices are not yet implemented; grants occur once with the highest eligible bonus, without adding bonuses together.")
        seen_programs.add(selection['program'])
        eligible_slots = program['eligible_slots'].get(outcome['id'], []) if outcome else []
        valid = slot is not None and selection['slot'] in eligible_slots and selection['slot'] not in seen_slots
        seen_slots.add(selection['slot'])
        if not valid:
            warnings.append(f"{program['name']} is outside an eligible education slot. Choice retained with no scholastic bonus.")
        bonus = slot['bonus'] if valid and slot is not None and slot['bonus'] is not None else 0
        for identifier in program['skill_ids']:
            bonuses[identifier] = max(bonuses.get(identifier, 0), bonus)
    if outcome is None:
        warnings.append('Choose education before assigning scholastic programs.')
    elif outcome['id'] == 'street-schooled':
        warnings.append('Street Schooled literacy and its skill trade remain unresolved; Basic Mathematics and Computer Operation require literacy. Choices are retained for player adjudication.')
    iq = character['attributes']['IQ']['value']
    intelligence = pack['intelligence']['bonuses'].get(str(min(iq, 30)), 0)
    if iq > 30:
        warnings.append('I.Q. above 30 uses the reviewed +16% chart limit; further skill bonuses remain pending.')
    secondary_used = sum(secondary_rules['selection_costs'].get(identifier,1) for identifier in secondary_choices) if secondary_rules else 0
    allowance = outcome['secondary_count'] if outcome else 0
    if secondary_rules:
        names = {skill['id']:skill['name'] for skill in pack['skills']}
        for identifier,count in Counter(secondary_choices).items():
            if count>1:
                warnings.append(f"Repeated Secondary {names[identifier]} retained and counted; its proficiency occurs once.")
            if identifier not in secondary_rules['eligible_skill_ids']:
                warnings.append(f"{names[identifier]} is outside the eligible Secondary categories. Choice retained without an education bonus.")
        if secondary_used>allowance:
            warnings.append(f'Secondary selections exceed the education allowance by {secondary_used-allowance}. Choices retained.')
    skills = []
    for definition in pack['skills']:
        if definition['id'] not in bonuses:
            continue
        contributions = {'base':definition['base'], 'education':bonuses[definition['id']], 'intelligence':intelligence}
        skills.append({**deepcopy(definition), **project_proficiency(definition, contributions),
                       'secondary_selected':definition['id'] in secondary_choices})
    return {'catalog':deepcopy(pack['programs']), 'selections':selections, 'slots':deepcopy(slots),
            'skills':skills, 'warnings':warnings, 'guidance':deepcopy(pack['guidance']),
            'rules':{'id':pack['id'], 'version':pack['version']}, 'source':deepcopy(pack['source']),
            'secondary':{'supported':secondary_rules is not None, 'catalog':deepcopy(pack['skills']) if secondary_rules else [],
                         'selections':secondary_choices,'allowance':allowance,'used':secondary_used,'remaining':allowance-secondary_used,
                         'guidance':deepcopy(secondary_rules['guidance']) if secondary_rules else [],
                         'eligible_skill_ids':deepcopy(secondary_rules['eligible_skill_ids']) if secondary_rules else [],
                         'source':deepcopy(secondary_rules['source']) if secondary_rules else None}}
