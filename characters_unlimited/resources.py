"""Recorded starting resources and their pinned contributions."""

from copy import deepcopy
import json

from .attribute_modifiers import attribute_value
from .physical import project_physical


MAX_INTEGER = 9_007_199_254_740_991


def _integer(value):
    return type(value) is int and abs(value) <= MAX_INTEGER


def _canonical(value):
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError, RecursionError) as error:
        raise ValueError('Invalid resource source evidence') from error


def _rules(pack):
    rules = pack.get('resources')
    if rules is None:
        return None
    if (not isinstance(rules, dict) or set(rules) != {'definitions', 'guidance'} or
            not isinstance(rules['definitions'], list) or not 0 < len(rules['definitions']) <= 100 or
            not isinstance(rules['guidance'], list) or len(rules['guidance']) > 100 or
            any(not isinstance(note, str) for note in rules['guidance'])):
        raise ValueError('Invalid pinned resource rules')
    identifiers = set()
    for definition in rules['definitions']:
        if (not isinstance(definition, dict) or set(definition) != {'id', 'name', 'contributions'} or
                not isinstance(definition['id'], str) or not definition['id'] or
                definition['id'] in identifiers or not isinstance(definition['name'], str) or
                not isinstance(definition['contributions'], list) or
                not 0 < len(definition['contributions']) <= 100):
            raise ValueError('Invalid pinned resource definition')
        identifiers.add(definition['id'])
        contribution_ids = set()
        for contribution in definition['contributions']:
            if (not isinstance(contribution, dict) or
                    set(contribution) not in ({'id', 'formula', 'source'}, {'id', 'attribute', 'source'}) or
                    not isinstance(contribution['id'], str) or not contribution['id'] or
                    contribution['id'] in contribution_ids or not isinstance(contribution['source'], dict)):
                raise ValueError('Invalid pinned resource contribution')
            contribution_ids.add(contribution['id'])
            if 'formula' in contribution:
                _formula(contribution['formula'])
            elif not isinstance(contribution['attribute'], str) or not contribution['attribute']:
                raise ValueError('Invalid resource attribute contribution')
    return rules


def _formula(formula):
    if not isinstance(formula, dict) or set(formula) != {'count', 'sides', 'bonus'}:
        raise ValueError('Invalid pinned resource dice formula')
    count, sides, bonus = formula['count'], formula['sides'], formula['bonus']
    if (type(count) is not int or not 0 <= count <= 1000 or
            type(sides) is not int or sides < 0 or (count and not 1 <= sides <= 1000) or
            not _integer(bonus)):
        raise ValueError('Invalid pinned resource dice formula')
    return count, sides, bonus


def _snapshot_names(rules):
    return {item['attribute'] for definition in rules['definitions']
            for item in definition['contributions'] if 'attribute' in item}


def acquire_resources(character, pack, die):
    """Draw each starting resource die once and capture effective attributes."""
    rules = _rules(pack)
    if rules is None:
        raise ValueError('Resource generation requires pinned resource rules')
    if 'resources' in character or 'resource_attribute_snapshot' in character:
        raise ValueError('Starting resources have already been generated')
    snapshot = {}
    for name in sorted(_snapshot_names(rules)):
        record = deepcopy(character['attributes'][name])
        if not _integer(record.get('value')) or attribute_value(record) != record['value']:
            raise ValueError('Resource attribute value is invalid')
        snapshot[name] = record
    resources = {}
    for definition in rules['definitions']:
        contributions = []
        for item in definition['contributions']:
            if 'formula' in item:
                count, sides, bonus = _formula(item['formula'])
                rolls = []
                for _ in range(count):
                    face = die(sides)
                    if type(face) is not int or not 1 <= face <= sides:
                        raise ValueError('Dice source returned an invalid resource value')
                    rolls.append(face)
                value = sum(rolls) + bonus
            else:
                value, rolls = snapshot[item['attribute']]['value'], []
            if not _integer(value):
                raise ValueError('Resource contribution exceeds the supported range')
            contributions.append({'id': item['id'], 'value': value,
                                  'rolls': rolls, 'source': deepcopy(item['source'])})
        resources[definition['id']] = {'contributions': contributions,
                                       'adjustment': 0, 'fixed': None}
    return {'resources': resources, 'resource_attribute_snapshot': snapshot}


def validate_resources(character, pack):
    """Validate saved resource records against the exact pinned contribution rules."""
    has_resources = 'resources' in character
    has_snapshot = 'resource_attribute_snapshot' in character
    if not has_resources and not has_snapshot:
        return
    if has_resources != has_snapshot:
        raise ValueError('Resource records require their attribute snapshot')
    rules = _rules(pack)
    if rules is None:
        raise ValueError('Resource records require pinned resource rules')
    resources = character['resources']
    snapshot = character['resource_attribute_snapshot']
    definitions = {item['id']: item for item in rules['definitions']}
    if (not isinstance(resources, dict) or set(resources) != definitions.keys() or
            not isinstance(snapshot, dict) or set(snapshot) != _snapshot_names(rules)):
        raise ValueError('Resource records do not match pinned definitions')
    for name, record in snapshot.items():
        if not isinstance(record, dict) or not _integer(record.get('value')):
            raise ValueError('Invalid resource attribute snapshot')
        try:
            calculated = attribute_value(record)
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError('Invalid resource attribute snapshot') from error
        if calculated != record['value']:
            raise ValueError('Resource attribute snapshot value does not match its record')
    for identifier, definition in definitions.items():
        record = resources[identifier]
        if (not isinstance(record, dict) or set(record) != {'contributions', 'adjustment', 'fixed'} or
                not _integer(record['adjustment']) or
                (record['fixed'] is not None and not _integer(record['fixed'])) or
                not isinstance(record['contributions'], list) or
                len(record['contributions']) != len(definition['contributions'])):
            raise ValueError('Invalid resource record')
        expected = {item['id']: item for item in definition['contributions']}
        seen = set()
        for contribution in record['contributions']:
            if (not isinstance(contribution, dict) or
                    set(contribution) != {'id', 'value', 'rolls', 'source'} or
                    not isinstance(contribution['id'], str) or
                    contribution['id'] not in expected or contribution['id'] in seen or
                    not _integer(contribution['value']) or
                    not isinstance(contribution['rolls'], list) or
                    len(contribution['rolls']) > 1000 or
                    _canonical(contribution['source']) != _canonical(expected[contribution['id']]['source'])):
                raise ValueError('Invalid resource contribution')
            seen.add(contribution['id'])
            rule = expected[contribution['id']]
            if 'formula' in rule:
                count, sides, bonus = _formula(rule['formula'])
                faces = contribution['rolls']
                if (len(faces) != count or
                        any(type(face) is not int or not 1 <= face <= sides for face in faces) or
                        contribution['value'] != sum(faces) + bonus):
                    raise ValueError('Resource dice do not match pinned rules')
            elif (contribution['rolls'] or
                  contribution['value'] != snapshot[rule['attribute']]['value']):
                raise ValueError('Resource attribute contribution does not match its snapshot')


def project_resources(character, pack):
    """Show generated totals and active Physical S.D.C. bonuses without rolling."""
    validate_resources(character, pack)
    rules = _rules(pack)
    if rules is None:
        return {'supported': False, 'generated': False, 'resources': {}, 'guidance': []}
    generated = 'resources' in character
    physical = project_physical(character, pack)['resources'] if 'skills' in pack else []
    projected = {}
    for definition in rules['definitions']:
        identifier = definition['id']
        record = character['resources'][identifier] if generated else None
        amounts = {item['id']: item['value'] for item in record['contributions']} if record else {}
        rolls = {item['id']: deepcopy(item['rolls']) for item in record['contributions']} if record else {}
        sources = [deepcopy(item['source']) for item in record['contributions']] if record else []
        advancement = character.get('advancement')
        if identifier == 'HP' and advancement and advancement['active']:
            amounts['Level 2'] = advancement['hp_roll']
            rolls['Level 2'] = [advancement['hp_roll']]
            sources.append(deepcopy(advancement['source']))
            for event in character.get('later_advancements', []):
                if event['level'] <= character['level']:
                    label = 'Level ' + str(event['level'])
                    amounts[label] = event['hp_roll']
                    rolls[label] = [event['hp_roll']]
                    sources.append(deepcopy(event['source']))
        if identifier == 'SDC':
            for item in physical:
                if item['resource'] != 'SDC':
                    continue
                label = 'Physical: ' + item['name']
                amounts[label] = item['value']
                rolls[label] = deepcopy(item['rolls'])
                if item['source'] not in sources:
                    sources.append(deepcopy(item['source']))
        adjustment = record['adjustment'] if record else 0
        fixed = record['fixed'] if record else None
        calculated = sum(amounts.values()) + adjustment if generated else None
        projected[identifier] = {'name': definition['name'],
                                 'value': fixed if fixed is not None else calculated,
                                 'calculated_value': calculated,
                                 'contributions': amounts, 'rolls': rolls,
                                 'sources': sources, 'adjustment': adjustment,
                                 'fixed': fixed}
    return {'supported': True, 'generated': generated, 'resources': projected,
            'guidance': list(rules['guidance'])}


def update_resource(character, pack, resource, mode, value=None):
    """Apply a manual fixed value, adjustment, or reset to calculated value."""
    validate_resources(character, pack)
    rules = _rules(pack)
    known = {item['id'] for item in rules['definitions']} if rules else set()
    if 'resources' not in character or resource not in known:
        raise ValueError('Generate resources and select a known resource')
    if mode not in ('fixed', 'adjustment', 'calculated'):
        raise ValueError('Select fixed, adjustment, or calculated')
    if mode != 'calculated' and not _integer(value):
        raise ValueError('Resource values must be supported whole numbers')
    resources = deepcopy(character['resources'])
    record = resources[resource]
    record['fixed'] = value if mode == 'fixed' else None
    record['adjustment'] = value if mode == 'adjustment' else 0
    return {'resources': resources}
