"""Reviewed power acquisitions, retained dice and source-bound effects."""

import json
from copy import deepcopy
from uuid import UUID, uuid4

from .attribute_modifiers import attribute_value
from .heroes_power_budget import project_budget


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def validate_powers(record, pack):
    if not isinstance(record, dict) or set(record) != {'acquisitions','active','history'}:
        raise ValueError('Invalid Heroes power record')
    acquisitions = record['acquisitions']
    if not isinstance(acquisitions, list) or len(acquisitions) > 1000:
        raise ValueError('Invalid power acquisitions')
    definitions = {row['id']:row for row in pack['powers']}
    identifiers, powers = set(), set()
    for acquisition in acquisitions:
        if not isinstance(acquisition, dict) or set(acquisition) != {'id','power','rolls','source'}:
            raise ValueError('Invalid power acquisition')
        identifier = acquisition['id']
        try:
            if not isinstance(identifier, str) or str(UUID(identifier)) != identifier:
                raise ValueError('Invalid power acquisition identity')
        except (ValueError, AttributeError):
            raise ValueError('Invalid power acquisition identity') from None
        power = acquisition['power']
        if not isinstance(power, str) or power not in definitions or identifier in identifiers or power in powers:
            raise ValueError('Power acquisition identities and powers must be unique and reviewed')
        identifiers.add(identifier); powers.add(power)
        definition = definitions[power]
        dice = acquisition['rolls']
        formula = definition['attribute_floor']
        if not isinstance(dice, list) or len(dice) != formula['count'] or any(type(face) is not int or not 1 <= face <= formula['sides'] for face in dice):
            raise ValueError('Power acquisition dice must match the reviewed formula')
        if encoded(acquisition['source']) != encoded(definition['source']):
            raise ValueError('Power acquisition source must match its pinned rules')
    history = record['history']
    if not isinstance(history, list) or not 1 <= len(history) <= 1000:
        raise ValueError('Power selection history must contain between 1 and 1000 entries')
    for active in [record['active'], *history]:
        if not isinstance(active, list) or len(active) > len(identifiers) or any(not isinstance(item,str) or item not in identifiers for item in active) or len(set(active)) != len(active):
            raise ValueError('Active powers must use distinct retained acquisition identities')
    if record['active'] != history[-1]:
        raise ValueError('Active powers must match the latest retained history')
    first_appearances = list(dict.fromkeys(identifier for frame in history for identifier in frame))
    if first_appearances != [row['id'] for row in acquisitions]:
        raise ValueError('Every retained power acquisition must appear in selection history in acquisition order')


def floor_modifier(acquisition, definition):
    formula = definition['attribute_floor']
    return {'id':'power-floor:'+acquisition['id'], 'value':formula['constant']+sum(acquisition['rolls']),
            'rolls':deepcopy(acquisition['rolls']), 'source':deepcopy(definition['source'])}


def power_modifiers(record, pack, *, active_only=True):
    definitions = {row['id']:row for row in pack['powers']}
    return [(definitions[row['power']]['attribute_floor']['attribute'], floor_modifier(row, definitions[row['power']]))
            for row in record['acquisitions'] if not active_only or row['id'] in record['active']]


def select_powers(character, selections, pack, die):
    definitions = {row['id']:row for row in pack['powers']}
    if not isinstance(selections,list) or len(selections) > 100 or any(not isinstance(item,str) or item not in definitions for item in selections) or len(set(selections)) != len(selections):
        raise ValueError('Choose distinct reviewed super abilities')
    record = deepcopy(character.get('hero_powers', {'acquisitions':[], 'active':[], 'history':[]}))
    retained = {row['power']:row for row in record['acquisitions']}
    active = []
    for power in selections:
        if power not in retained:
            definition = definitions[power]
            formula = definition['attribute_floor']
            acquisition = {'id':str(uuid4()), 'power':power, 'rolls':[die(formula['sides']) for _ in range(formula['count'])],
                           'source':deepcopy(definition['source'])}
            record['acquisitions'].append(acquisition); retained[power] = acquisition
        active.append(retained[power]['id'])
    record['active'] = active; record['history'].append(deepcopy(active))
    validate_powers(record, pack)
    attributes = deepcopy(character['attributes'])
    for value in attributes.values():
        if 'modifiers' in value:
            value['modifiers'] = [row for row in value['modifiers'] if not row['id'].startswith('power-floor:')]
    for name, modifier in power_modifiers(record, pack):
        attributes[name].setdefault('modifiers', []).append(modifier)
    for value in attributes.values():
        value['value'] = attribute_value(value)
    return {'hero_powers':record, 'attributes':attributes}


def validate_power_attributes(character, pack):
    record = character.get('hero_powers')
    if record:
        validate_powers(record, pack)
    allowed = {modifier['id']:(name,modifier) for name,modifier in power_modifiers(record,pack,active_only=False)} if record else {}
    current = {modifier['id']:(name,modifier) for name,modifier in power_modifiers(record,pack)} if record else {}
    frames = [character['attributes'], *(row['attributes'] for row in character.get('roll_history', []))]
    for index, attributes in enumerate(frames):
        found = {}
        for name, value in attributes.items():
            for modifier in value.get('modifiers', []):
                if modifier['id'].startswith('power-floor:'):
                    if modifier['id'] in found or encoded((name,modifier)) != encoded(allowed.get(modifier['id'])):
                        raise ValueError('Power attribute contribution must match its retained acquisition')
                    found[modifier['id']] = (name,modifier)
        if index == 0 and encoded(found) != encoded(current):
            raise ValueError('Current power attribute contributions must match active powers')


def power_skill_contributions(character, definition, pack):
    if pack is None or not character.get('hero_powers'):
        return {}
    record = character['hero_powers']
    definitions = {row['id']:row for row in pack['powers']}
    contributions = {}
    for acquisition in record['acquisitions']:
        if acquisition['id'] not in record['active']:
            continue
        power = definitions[acquisition['power']]
        bonus = power['skill_bonus']
        if definition['id'] in bonus['skill_ids'] or set(definition.get('power_bonus_tags',[])).intersection(bonus['tags']):
            contributions[power['name']] = bonus['amount']
    return contributions


def project_powers(character, pack, budget_pack):
    record = character.get('hero_powers')
    if record is not None:
        validate_powers(record, pack)
    active = record['active'] if record else []
    receipts = []
    definitions = {row['id']:row for row in pack['powers']}
    for acquisition in record['acquisitions'] if record else []:
        definition = definitions[acquisition['power']]
        receipts.append({**deepcopy(definition), 'acquisition_id':acquisition['id'], 'rolls':deepcopy(acquisition['rolls']),
                         'target':floor_modifier(acquisition,definition)['value'], 'active':acquisition['id'] in active})
    powers = [row for row in receipts if row['active']]
    budget = project_budget(character.get('power_budget'), budget_pack)
    allowance = sum(row['count'] for row in budget['budgets'] if row['name'] == 'Minor super abilities')
    used = len(powers)
    warnings = []
    if used > allowance:
        warnings.append(f'Minor power selections exceed the recorded starting allowance by {used-allowance}. Selections retained.')
    value = character['attributes']['MA']['value']
    trust = pack['mental_affinity_chart'].get(str(min(value,30)))
    return {'catalog':deepcopy(pack['powers']), 'selections':[row['id'] for row in powers], 'powers':powers, 'receipts':receipts,
            'minor':{'used':used, 'allowance':allowance, 'remaining':allowance-used}, 'trust_intimidate':trust,
            'warnings':warnings, 'history':[{'selections':[next(row['power'] for row in record['acquisitions'] if row['id']==identifier) for identifier in frame]} for frame in record['history']] if record else [],
            'trust_source':deepcopy(pack['mental_affinity_source']),
            'source':deepcopy(pack['source']), 'guidance':deepcopy(pack['guidance']),
            'rules':{'id':pack['id'], 'version':pack['version']}}
