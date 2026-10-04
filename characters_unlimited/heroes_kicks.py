"""Retained Heroes learned kick choices and their active damage contexts."""
import json
from copy import deepcopy


def validate_kick_selections(selections, pack):
    known = {row['id'] for row in pack['kicks']}
    if (not isinstance(selections, list)
            or any(not isinstance(value, str) or value not in known for value in selections)
            or len(selections) != len(set(selections))):
        raise ValueError('Choose distinct recognized Heroes kicks')
    return deepcopy(selections)


def validate_hero_kicks(character, pack):
    records = character.get('hero_kick_choices')
    if records is None and pack is None:
        return
    if character['game'] != 'heroes-unlimited' or pack is None or not isinstance(records, dict):
        raise ValueError('Heroes kick choices require their exact Heroes rule pin')
    for style, record in records.items():
        if style not in pack['styles'] or style not in character.get('physical_acquisitions', {}):
            raise ValueError('Kick choices must reference a retained training acquisition')
        if not isinstance(record, dict) or set(record) != {'selections', 'source'} or json.dumps(record['source'],sort_keys=True,allow_nan=False) != json.dumps(pack['source'],sort_keys=True,allow_nan=False):
            raise ValueError('Kick choices must retain their exact reviewed source')
        validate_kick_selections(record['selections'], pack)


def kick_damage(definition, bonus, power):
    if definition['dice'] is None:
        return 'No damage'
    if bonus is None:
        return None
    expression = ('2 x ' if power else '') + definition['dice']
    if definition['flat']:
        expression += f" + {definition['flat']}"
    if bonus:
        expression += f' + {bonus}'
    return expression + ' S.D.C.'


def project_hero_kicks(character, pack, active, damage_bonus):
    if pack is None:
        return {'supported': False}, []
    rule = pack['styles'].get(active)
    age = character['level'] - character.get('learning_levels', {}).get(active, character['level']) + 1
    eligible = rule is not None and age >= rule['level']
    selections = character.get('hero_kick_choices', {}).get(active, {}).get('selections', [])
    accepted = character.get('additional_rule_packs', {}).get(pack['id']) == pack['version']
    allowed = rule['choices'] if rule else []
    automatic = list(rule['automatic']) if eligible else []
    if eligible:
        automatic.extend(value for level, values in rule.get('later_automatic', {}).items()
                         if age >= int(level) for value in values)
    view = {
        'supported': True, 'accepted': accepted, 'training_id': active, 'age': age,
        'count': rule['count'] if eligible else 0,
        'remaining': (rule['count'] if eligible else 0) - len(selections),
        'selections': deepcopy(selections), 'catalog': deepcopy(pack['kicks']),
        'eligible': eligible, 'allowed': deepcopy(allowed), 'automatic': automatic,
        'warnings': [], 'source': deepcopy(pack['source']),
        'receipts': [{'training_id': style, 'selections': deepcopy(record['selections']),
                      'active': style == active, 'source': deepcopy(record['source'])}
                     for style, record in character.get('hero_kick_choices', {}).items()],
    }
    if selections and not eligible:
        view['warnings'].append('Selected kicks precede their training entitlement and remain inactive. Choices retained.')
    if view['remaining'] < 0:
        view['warnings'].append('Selected kicks exceed the training allowance. Choices retained.')
    if any(value not in allowed for value in selections):
        view['warnings'].append('Some retained choices are outside this training style kick entitlement and remain inactive.')
    granted = automatic + [value for value in selections if value in allowed] if eligible and accepted else []
    attacks = []
    for definition in pack['kicks']:
        if definition['id'] not in granted:
            continue
        for power in [False, True] if definition['power'] else [False]:
            row = deepcopy(definition)
            row['id'] = ('power-' if power else '') + row['id']
            row['name'] = ('Power ' if power else '') + row['name']
            row['power'] = power
            row['actions'] = 2 if power else row['actions']
            row['source'] = deepcopy(pack['source'])
            row['damage'] = kick_damage(definition, damage_bonus, power)
            attacks.append(row)
    return view, attacks
