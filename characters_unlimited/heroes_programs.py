"""Reviewed Heroes scholastic grants, separate from Rifts class skill pools."""

from copy import deepcopy
from collections import Counter

from .education import project_education
from .proficiency import project_proficiency, synergy_contributions
from .heroes_powers import power_skill_contributions


def validate_program_selections(selections, pack):
    if not isinstance(selections, list) or len(selections) > 100:
        raise ValueError('Select at most 100 program entries')
    programs = {item['id']:item for item in pack['programs']}
    skills = {item['id'] for item in pack['skills']}
    for selection in selections:
        if (not isinstance(selection, dict) or not {'slot','program'} <= set(selection) <= {'slot','program','choices'}
                or type(selection['slot']) is not int or not 0 <= selection['slot'] < 100
                or not isinstance(selection['program'], str) or selection['program'] not in programs):
            raise ValueError('Select an available program and a whole-number education slot')
        if 'choices' in selection:
            groups = {group['id'] for group in programs[selection['program']].get('choice_groups',[])}
            choices = selection['choices']
            if (not groups or not isinstance(choices,dict) or not set(choices)<=groups
                    or any(not isinstance(items,list) or len(items)>100
                           or any(not isinstance(item,str) or item not in skills for item in items)
                           for items in choices.values())):
                raise ValueError('Select known skills in an available program choice group')
    return deepcopy(selections)


def validate_secondary_selections(selections, pack):
    if 'secondary' not in pack:
        raise ValueError('Review and apply current program rules before selecting Secondary skills')
    identifiers = {skill['id'] for skill in pack['skills']}
    if (not isinstance(selections,list) or len(selections)>100
            or any(not isinstance(item,str) or item not in identifiers for item in selections)):
        raise ValueError('Select at most 100 available Secondary skill entries')
    return list(selections)


def program_choice_view(selection, program, warnings, *, certified=True):
    groups = []
    for definition in program.get('choice_groups',[]):
        choices = selection.get('choices',{}).get(definition['id'],[])
        unresolved = set(choices).intersection(definition.get('unresolved_skill_ids',[]))
        eligible = (set(choices).intersection(definition['skill_ids'])-unresolved) if certified else set()
        credited = sum(definition.get('selection_costs',{}).get(identifier,1) for identifier in eligible)
        remaining = definition['count']-credited
        label = f"{program['name']} slot {selection['slot']+1} — {definition['name']}"
        if remaining:
            if 'selection_costs' in definition:
                message = (f'{remaining} weighted selections remaining' if remaining>0 else
                           f'exceeds the allowance by {-remaining} selections')
                warnings.append(f'{label}: {message}. Entered choices retained.')
            else:
                warnings.append(f'{label}: {remaining} distinct eligible choices remaining. Entered choices retained.')
        if len(set(choices))<len(choices):
            warnings.append(f'{label}: repeated choices retained; duplicates do not fill another distinct choice.')
        if set(choices)-set(definition['skill_ids']):
            warnings.append(f'{label}: outside-group choices retained with no group education bonus.')
        if unresolved:
            warnings.append(f'{label}: duplicate fixed-grant choice credit is pending interpretation. Fixed grants remain intact; the extra entitlement is not certified.')
        groups.append({**deepcopy(definition),'selections':deepcopy(choices),'entered':len(choices),
                       'credited':credited,'remaining':remaining,'credit_certified':certified})
    return groups


def project_programs(character, pack, education_pack, power_pack=None):
    education = project_education(character.get('education'), education_pack)
    outcome = education['outcome']
    slots = outcome['program_slots'] if outcome else []
    selections = validate_program_selections(character.get('hero_program_selections', []), pack)
    warnings = []
    bonuses = {identifier:0 for identifier in pack['universal_skill_ids']}
    physical_grants = set(bonuses)
    secondary_rules = pack.get('secondary')
    secondary_choices = (validate_secondary_selections(character.get('hero_secondary_selections',[]),pack)
                         if secondary_rules else [])
    for identifier in secondary_choices:
        bonuses.setdefault(identifier,0)
        physical_grants.add(identifier)
    seen_programs, seen_slots = set(), set()
    program_choices = []
    for selection in selections:
        program = next(item for item in pack['programs'] if item['id'] == selection['program'])
        slot = slots[selection['slot']] if selection['slot'] < len(slots) else None
        repeated = selection['program'] in seen_programs
        if repeated:
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
            physical_grants.add(identifier)
        groups = program_choice_view(selection,program,warnings,
                                     certified=not (repeated and program.get('repeat_entitlement_pending',False)))
        program_choices.append({'program':program['id'],'slot':selection['slot'],'groups':groups,'repeat':repeated})
        if repeated and groups:
            warnings.append(f"{program['name']} repeat entitlement is not implemented. Retained first-program group choices receive no new group education bonus and do not certify the repeat's remaining-category choices.")
        for group in groups:
            if not group['credit_certified']:
                warnings.append(f"{program['name']} repeat credit is uncertified. Choices retained without new grants until the remaining-category entitlement is reviewed.")
                continue
            physical_grants.update(set(group['selections']).intersection(group['skill_ids'])
                                   - set(group.get('unresolved_skill_ids', [])))
            for identifier in group['selections']:
                choice_bonus = bonus if not repeated and identifier in group['skill_ids'] else 0
                bonuses[identifier] = max(bonuses.get(identifier,0),choice_bonus)
    if outcome is None:
        warnings.append('Choose education before assigning scholastic programs.')
    elif outcome['id'] == 'street-schooled':
        warnings.append('Street Schooled literacy and its skill trade remain unresolved; Basic Mathematics and Computer Operation require literacy. Choices are retained for player adjudication.')
    iq = character['attributes']['IQ']['value']
    intelligence = pack['intelligence']['bonuses'].get(str(min(iq, 30)), 0)
    if iq > 30:
        warnings.append('I.Q. above 30 uses the reviewed +16% chart limit; further skill bonuses remain pending.')
    secondary_costs = {skill['id']:secondary_rules['selection_costs'].get(skill['id'],1)
                       for skill in pack['skills']} if secondary_rules else {}
    secondary_used = sum(secondary_costs[identifier] for identifier in secondary_choices)
    allowance = outcome['secondary_count'] if outcome else 0
    if secondary_rules:
        names = {skill['id']:skill['name'] for skill in pack['skills']}
        for identifier,count in Counter(secondary_choices).items():
            if identifier in secondary_rules.get('conditional_guidance', {}):
                warnings.append(secondary_rules['conditional_guidance'][identifier])
            if count>1:
                warnings.append(f"Repeated Secondary {names[identifier]} retained and counted; its effects occur once.")
            if identifier not in secondary_rules['eligible_skill_ids']:
                warnings.append(f"{names[identifier]} is outside the eligible Secondary categories. Choice retained without an education bonus.")
        if secondary_used>allowance:
            warnings.append(f'Secondary selections exceed the education allowance by {secondary_used-allowance}. Choices retained.')
    for definition in pack['skills']:
        if definition['id'] in physical_grants:
            for required in definition.get('requires_skill_ids', []):
                if required not in physical_grants:
                    name = next(row['name'] for row in pack['skills'] if row['id'] == required)
                    warnings.append(f"{definition['name']} requires {name}. Selection retained on the honor system; the prerequisite is not granted.")
    skills = []
    for definition in pack['skills']:
        if definition['id'] not in bonuses:
            continue
        if definition.get('kind') == 'physical' and 'base' not in definition:
            continue
        contributions = {'base':definition['base'], 'education':bonuses[definition['id']], 'intelligence':intelligence,
                         **synergy_contributions(definition,set(bonuses)),
                         **power_skill_contributions(character,definition,power_pack)}
        for bonus in definition.get('attribute_bonuses', []):
            value = character['attributes'][bonus['attribute']]['value']
            if 'cap' in bonus:
                value = min(value,bonus['cap'])
            contributions[bonus['name']] = max(0, value-bonus['threshold']) // bonus['step'] * bonus['amount']
        projected_definition = deepcopy(definition)
        projected_definition['additional_checks'] = [check for check in definition.get('additional_checks', [])
                                                    if check.get('requires_skill') is None or check['requires_skill'] in bonuses]
        skills.append({**deepcopy(definition), **project_proficiency(projected_definition, contributions),
                       'secondary_selected':definition['id'] in secondary_choices})
    return {'catalog':deepcopy(pack['programs']), 'selections':selections, 'slots':deepcopy(slots),
            'physical_selections':[{'skill_id':row['id']} for row in pack['skills']
                                   if row.get('kind') == 'physical' and row['id'] in physical_grants],
            'skill_catalog':deepcopy(pack['skills']),
            'skills':skills, 'warnings':warnings, 'guidance':deepcopy(pack['guidance']),
            'rules':{'id':pack['id'], 'version':pack['version']}, 'source':deepcopy(pack['source']),
            'program_choices':program_choices,
            'secondary':{'supported':secondary_rules is not None, 'catalog':deepcopy(pack['skills']) if secondary_rules else [],
                         'selections':secondary_choices,'allowance':allowance,'used':secondary_used,'remaining':allowance-secondary_used,
                         'selection_costs':secondary_costs,
                         'guidance':deepcopy(secondary_rules['guidance']) if secondary_rules else [],
                         'eligible_skill_ids':deepcopy(secondary_rules['eligible_skill_ids']) if secondary_rules else [],
                         'source':deepcopy(secondary_rules['source']) if secondary_rules else None}}
