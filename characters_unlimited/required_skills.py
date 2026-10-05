"""Declarative O.C.C. percentile grants and required choice groups."""

from typing import Any
from .skill_choices import learned_selection_ids, specialty_key
from .proficiency import synergy_contributions, project_proficiency
from .advancement import learning_age
from .required_definitions import required_catalog, required_selection_group
from .selection_groups import project_group
from .skill_effects import pack_skill_effects, matching_skill_effects
from .skill_attribute_bonuses import attribute_contributions
from .skill_training import training_rules, required_training_definition, recorded_training_level


def required_choice_identity(group, value):
    return value if group['kind'] == 'select' else specialty_key(value)


def validate_required_choices(choices, pack):
    rules = required_catalog(pack)
    if rules is None:
        raise ValueError('Preview a skill-rule update before selecting these required choices')
    if not isinstance(choices, dict) or set(choices) - {group['id'] for group in rules['groups']}:
        raise ValueError('Provide the required skill choices')
    result: dict[str, Any] = {}
    for group in rules['groups']:
        multiple = group['kind'] == 'text-list' or group['count'] > 1
        value = choices.get(group['id'], [] if multiple else '')
        values = value if multiple else [value]
        if (not isinstance(values,list) or len(values) > 1000 or any(not isinstance(item,str) for item in values)):
            raise ValueError('Required skill choices must be text or a text list for this group')
        values = [item.strip() for item in values]
        if group['kind'] == 'select' and any(item and item not in {option['id'] for option in group['options']} for item in values):
            raise ValueError('Select an available required skill choice')
        result[group['id']] = values if multiple else values[0]
    return result


def project_required_skills(character, pack, intelligence, *, skill_grants=None):
    aliases = training_rules(pack)
    skill_effects = pack_skill_effects(pack)
    rules = required_catalog(pack)
    if rules is None:
        return {'grants': [], 'remaining': {}, 'warnings': [], 'catalog': None}
    choices = validate_required_choices(character.get('required_skill_choices', {}), pack)
    warnings = []
    definitions = [(definition, choices.get(definition.get('specialty_from'), '')) for definition in rules['grants']]
    if any(not isinstance(specialty,str) for _,specialty in definitions):
        raise ValueError('A fixed grant specialty must refer to a single text choice')
    remaining = {}
    for group in rules['groups']:
        raw = choices[group['id']]
        values = raw if isinstance(raw,list) else [raw]
        excluded: set[str] = set()
        for identifier in group.get('different_from', []):
            target = choices[identifier]
            excluded.update(required_choice_identity(group, item)
                            for item in (target if isinstance(target,list) else [target]) if item)
        unique = set()
        for value in values:
            key = required_choice_identity(group, value)
            if not key:
                if value or group['kind'] == 'text-list':
                    warnings.append(f"{group['name']}: name every choice.")
                continue
            if key in excluded:
                warnings.append(f"{group['name']}: must differ from the other named choices; retained without filling another slot.")
                continue
            if key in unique:
                warnings.append(f"{group['name']}: duplicate choices are retained without another slot or bonus.")
                continue
            unique.add(key)
            if group['kind'] == 'select':
                definitions.append((next(item for item in group['options'] if item['id'] == value), ''))
            elif 'skill' in group:
                definitions.append((group['skill'], value))
        remaining[group['id']] = (project_group(required_selection_group(group), list(unique))['remaining']
            if group['kind'] == 'select' else group['count'] - len(unique))
        if remaining[group['id']] < 0:
            warnings.append(f"{group['name']}: {-remaining[group['id']]} selection(s) over the allowance.")
    definitions = [(required_training_definition(definition, pack, aliases), specialty)
                   for definition, specialty in definitions]
    available = {definition['id'] for definition, _ in definitions}
    available.update(learned_selection_ids(character.get('skill_selections', []), pack))
    available.update(skill_grants or {})
    grants = []
    seen = set()
    for definition, specialty in definitions:
        identity = (definition['id'], specialty_key(specialty))
        if identity in seen:
            warnings.append(f"{definition['name']}: duplicate O.C.C. grant retained without another proficiency bonus.")
            continue
        seen.add(identity)
        contributions = {'base': definition['base'], 'class': definition['class_bonus'], 'intelligence': intelligence}
        training = (skill_grants or {}).get(definition['id']) if not specialty else None
        if training:
            contributions['class'] = max(definition['class_bonus'], training['ordinary_bonus'])
            if training['origins']:
                contributions['Skill grant training'] = max(0, training['bonus'] - contributions['class'])
        learned = (recorded_training_level(character, definition['id'], aliases, default=1)
                   if aliases is not None and not specialty else None)
        if training and aliases is not None:
            learned = training['learned_level']
        if character['level'] > 1:
            age = character['level'] - learned + 1 if learned is not None else learning_age(character, 'skill', definition['id'], specialty)
            contributions['advancement'] = (age - 1) * definition['per_level']
        if 'class_ability' in definition:
            contributions['class_ability'] = definition['class_ability']
        contributions.update(synergy_contributions(definition, available))
        contributions.update(attribute_contributions(definition, character['attributes']))
        grants.append({**definition, 'specialty': specialty, **({'learned_level': learned} if learned is not None and 'catalog_skill_id' in definition else {}), **({'grant_origins': training['origins']} if training and training['origins'] else {}), **project_proficiency(definition, contributions, effect_contributions=matching_skill_effects(definition['id'], skill_effects), exact=aliases is not None or any(row.get('granted_skills') for row in pack['skills'])), 'quality': 'trained'})
    return {'grants': grants, 'remaining': remaining, 'warnings': warnings, 'catalog': rules}
