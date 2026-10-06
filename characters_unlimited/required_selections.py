"""Resolve retained required choices once for every grant projection."""

from typing import Any
from .skill_choices import specialty_key
from .required_definitions import required_catalog, required_selection_group
from .selection_groups import project_group


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


def selected_required_definitions(character, pack):
    rules = required_catalog(pack)
    if rules is None:
        return [], {}, []
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
    return definitions, remaining, warnings
