"""Reviewed Heroes scholastic grants, separate from Rifts class skill pools."""

from copy import deepcopy

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


def project_programs(character, pack, education_pack):
    education = project_education(character.get('education'), education_pack)
    outcome = education['outcome']
    slots = outcome['program_slots'] if outcome else []
    selections = validate_program_selections(character.get('hero_program_selections', []), pack)
    warnings = []
    bonuses = {identifier:0 for identifier in pack['universal_skill_ids']}
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
    skills = []
    for definition in pack['skills']:
        if definition['id'] not in bonuses:
            continue
        contributions = {'base':definition['base'], 'education':bonuses[definition['id']], 'intelligence':intelligence}
        skills.append({**deepcopy(definition), **project_proficiency(definition, contributions)})
    return {'catalog':deepcopy(pack['programs']), 'selections':selections, 'slots':deepcopy(slots),
            'skills':skills, 'warnings':warnings, 'guidance':deepcopy(pack['guidance']),
            'rules':{'id':pack['id'], 'version':pack['version']}, 'source':deepcopy(pack['source'])}
