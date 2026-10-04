"""Independent, source-bound starting equipment groups and original receipts."""

from copy import deepcopy
import json
from uuid import UUID

MAX_QUANTITY = 1000
MAX_SAFE_INTEGER = 9_007_199_254_740_991


def _canonical(value):
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError, RecursionError) as error:
        raise ValueError('Invalid starting equipment group evidence') from error


def _possession_id(value):
    if not isinstance(value, str):
        return False
    try:
        return str(UUID(value)) == value
    except (ValueError, AttributeError):
        return False


def _rules(character, pack):
    if pack.get('id') != 'rifts-equipment' or pack.get('game') != 'rifts':
        raise ValueError('Unsupported starting equipment group pack')
    rules = pack.get('starting_groups')
    if rules is None:
        return {}
    if (not isinstance(rules, dict) or set(rules) != {'character_class', 'groups'}
            or not isinstance(rules['character_class'], str)
            or not isinstance(rules['groups'], dict) or not 0 < len(rules['groups']) <= MAX_QUANTITY):
        raise ValueError('Invalid starting equipment group rules')
    if character.get('game') != 'rifts' or character.get('character_class') != rules['character_class']:
        return {}
    catalog = {item['id']: item for item in pack['items']}
    for identifier, group in rules['groups'].items():
        if (not isinstance(identifier, str) or not identifier or len(identifier) > 100
                or not isinstance(group, dict)
                or set(group) != {'name', 'category', 'options', 'quantity', 'location', 'source', 'guidance'}
                or not isinstance(group['name'], str) or not group['name']
                or group['category'] not in ('armor', 'weapon', 'gear', 'ammunition')
                or not isinstance(group['options'], list) or not 0 < len(group['options']) <= MAX_QUANTITY
                or any(not isinstance(item, str) or item not in catalog for item in group['options'])
                or len(set(group['options'])) != len(group['options'])
                or any(catalog[item]['category'] != group['category'] for item in group['options'])
                or type(group['quantity']) is not int or not 1 <= group['quantity'] <= MAX_QUANTITY
                or group['location'] not in ('carried', 'stored')
                or not isinstance(group['source'], dict)
                or not isinstance(group['guidance'], list) or len(group['guidance']) > 100
                or any(not isinstance(note, str) for note in group['guidance'])):
            raise ValueError('Invalid starting equipment group definition')
        _canonical(group['source'])
    return rules['groups']


def _other_receipt_ids(character):
    identifiers = set()
    for field in ('starting_gear', 'starting_choices'):
        receipt = character.get(field)
        if receipt is not None:
            if not isinstance(receipt, dict) or not isinstance(receipt.get('grants'), list):
                raise ValueError('Invalid existing starting equipment receipt')
            for grant in receipt['grants']:
                if not isinstance(grant, dict) or not _possession_id(grant.get('possession_id')):
                    raise ValueError('Invalid existing starting equipment identity')
                identifiers.add(grant['possession_id'])
    return identifiers


def validate_starting_groups(character, pack):
    """Bind every original grant to its exact selected class rules."""
    if 'starting_equipment_groups' not in character:
        return
    groups = _rules(character, pack)
    receipts = character['starting_equipment_groups']
    if (not groups or not isinstance(receipts, dict) or not 0 < len(receipts) <= MAX_QUANTITY
            or set(receipts) - set(groups)):
        raise ValueError('Starting equipment receipts require matching pinned groups')
    seen = _other_receipt_ids(character)
    for identifier, receipt in receipts.items():
        group = groups[identifier]
        if (not isinstance(receipt, dict) or set(receipt) != {'selection', 'grants', 'source'}
                or not isinstance(receipt['selection'], str) or receipt['selection'] not in group['options']
                or not isinstance(receipt['grants'], list) or len(receipt['grants']) != 1
                or _canonical(receipt['source']) != _canonical(group['source'])):
            raise ValueError('Invalid starting equipment group receipt')
        grant = receipt['grants'][0]
        if (not isinstance(grant, dict) or set(grant) != {'item_id', 'possession_id', 'quantity'}
                or grant['item_id'] != receipt['selection']
                or type(grant['quantity']) is not int or grant['quantity'] != group['quantity']
                or not _possession_id(grant['possession_id']) or grant['possession_id'] in seen):
            raise ValueError('Invalid starting equipment group grant')
        seen.add(grant['possession_id'])


def acquire_starting_group(character, pack, group_id, selection, identifier_factory):
    """Add one free selected grant once, preserving funds and current possessions."""
    validate_starting_groups(character, pack)
    groups = _rules(character, pack)
    if not isinstance(group_id, str) or group_id not in groups:
        raise ValueError('Select an available starting equipment group')
    receipts = deepcopy(character.get('starting_equipment_groups', {}))
    if group_id in receipts:
        raise ValueError('This starting equipment group has already been granted')
    group = groups[group_id]
    if not isinstance(selection, str) or selection not in group['options']:
        raise ValueError('Select a reviewed starting equipment option')
    inventory = deepcopy(character.get('equipment', {'credits': 0, 'items': []}))
    if (not isinstance(inventory, dict) or set(inventory) != {'credits', 'items'}
            or type(inventory['credits']) is not int or abs(inventory['credits']) > MAX_SAFE_INTEGER
            or not isinstance(inventory['items'], list) or len(inventory['items']) >= MAX_QUANTITY):
        raise ValueError('Invalid or full starting equipment inventory')
    existing = {item['id'] for item in inventory['items']} | _other_receipt_ids(character)
    existing.update(grant['possession_id'] for receipt in receipts.values() for grant in receipt['grants'])
    identifier = identifier_factory()
    if not _possession_id(identifier) or identifier in existing:
        raise ValueError('Starting equipment needs a new UUID possession identity')
    definition = next(item for item in pack['items'] if item['id'] == selection)
    shots = (definition['capacity'] if definition['category'] == 'ammunition'
             or (definition['category'] == 'weapon' and definition.get('weapon_kind', 'ranged') == 'ranged')
             else None)
    inventory['items'].append({'id': identifier, 'item_id': selection, 'quantity': group['quantity'],
                               'location': group['location'], 'equipped': False, 'shots': shots})
    receipts[group_id] = {'selection': selection, 'grants': [{'item_id': selection,
                            'possession_id': identifier, 'quantity': group['quantity']}],
                         'source': deepcopy(group['source'])}
    return {'equipment': inventory, 'starting_equipment_groups': receipts}


def project_starting_groups(character, pack):
    """Project available groups and original receipts without granting possessions."""
    validate_starting_groups(character, pack)
    groups = _rules(character, pack)
    receipts = character.get('starting_equipment_groups', {})
    return {'supported': bool(groups), 'groups': [
        {'id': identifier, **deepcopy(group), 'generated': identifier in receipts,
         'receipt': deepcopy(receipts.get(identifier))} for identifier, group in groups.items()]}


def validate_starting_group_upgrade(character, previous, target):
    """Permit added groups but require acquired definitions to stay unchanged."""
    validate_starting_groups(character, previous)
    before, after = _rules(character, previous), _rules(character, target)
    for identifier in character.get('starting_equipment_groups', {}):
        if _canonical(before.get(identifier)) != _canonical(after.get(identifier)):
            raise ValueError('This update changes recorded starting equipment group rules. '
                             'Receipt migration is not yet supported; current rules remain intact.')
