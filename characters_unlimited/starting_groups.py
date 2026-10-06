"""Independent, source-bound starting equipment groups and original receipts."""

from copy import deepcopy
import json
import re
from uuid import UUID
from .recorded_formulas import validate_formula, formula_value, roll_formula
from .ability_requirements import compile_ability_requirements, project_ability_requirements

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


def starting_group_rules(character, pack, elective_count=None):
    """Compile equipment groups for a declared game/class identity without receipts."""
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
                or set(group) - {'name', 'category', 'options', 'quantity', 'location', 'source', 'guidance', 'additional_grants', 'condition', 'option_requirements', 'proficiency_slot', 'repeat_for_proficiencies'}
                or not {'name', 'category', 'options', 'quantity', 'location', 'source', 'guidance'} <= set(group)
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
        if 'proficiency_slot' in group and (type(group['proficiency_slot']) is not int or
                not 1 <= group['proficiency_slot'] <= MAX_QUANTITY):
            raise ValueError('Starting proficiency groups need a bounded elective slot')
        if 'repeat_for_proficiencies' in group:
            minimum = group['repeat_for_proficiencies']
            if (type(minimum) is not int or not 1 <= minimum <= MAX_QUANTITY or
                    'proficiency_slot' in group or not group.get('option_requirements')):
                raise ValueError('Repeated proficiency equipment needs a bounded minimum and training requirements')
            for other in rules['groups']:
                if not isinstance(other, str):
                    raise ValueError('Starting equipment identities must be strings')
                match = re.fullmatch(re.escape(identifier) + r'-([1-9][0-9]{0,3})', other)
                if match and int(match[1]) <= MAX_QUANTITY:
                    raise ValueError('Starting equipment group identities collide')
        requirements = group.get('option_requirements', {})
        if not isinstance(requirements, dict) or set(requirements) - set(group['options']):
            raise ValueError('Starting requirements need known equipment options')
        catalogs = pack.get('training_catalogs', {})
        if requirements:
            if not isinstance(catalogs, dict) or set(catalogs) != {'skills', 'ancient', 'modern'}:
                raise ValueError('Starting requirements need explicit training catalogs')
            for rows in catalogs.values():
                if (not isinstance(rows, list) or not 1 <= len(rows) <= MAX_QUANTITY or
                        any(not isinstance(row, dict) or set(row) != {'id', 'name'} or
                            any(not isinstance(row[key], str) or not row[key].strip() for key in ('id', 'name'))
                            for row in rows) or len({row['id'] for row in rows}) != len(rows)):
                    raise ValueError('Starting training catalogs need distinct known identities')
        for rows in requirements.values():
            compiled = compile_ability_requirements({'requirements': rows}, catalogs, ())
            if not compiled or any('selected_options' not in row or not row['option_ids'] for row in compiled):
                raise ValueError('Starting equipment requirements need known training options')
        if 'condition' in group:
            condition = group['condition']
            if (not isinstance(condition, dict) or set(condition) != {'name', 'formula'}
                    or not isinstance(condition['name'], str) or not condition['name'].strip()):
                raise ValueError('Starting equipment condition needs a label and reviewed formula')
            validate_formula(condition['formula'])
            formula = condition['formula']
            minimum = (formula['count'] + formula.get('constant', 0)) * formula.get('multiplier', 1)
            maximum = (formula['count'] * formula['sides'] + formula.get('constant', 0)) * formula.get('multiplier', 1)
            if not 0 <= minimum <= maximum <= 100:
                raise ValueError('Starting condition percentage must remain between zero and one hundred')
        additional = group.get('additional_grants', {})
        if (not isinstance(additional, dict) or set(additional) - set(group['options'])):
            raise ValueError('Additional equipment grants need known selected options')
        for grants in additional.values():
            if not isinstance(grants, list) or not 1 <= len(grants) <= 100:
                raise ValueError('Additional equipment grants require a bounded list')
            for grant in grants:
                if (not isinstance(grant, dict) or set(grant) != {'item_id', 'quantity_formula'}
                        or not isinstance(grant['item_id'], str) or grant['item_id'] not in catalog):
                    raise ValueError('Additional equipment grants need reviewed items and formulas')
                formula = grant['quantity_formula']
                validate_formula(formula)
                minimum = (formula['count'] + formula.get('constant', 0)) * formula.get('multiplier', 1)
                maximum = (formula['count'] * formula['sides'] + formula.get('constant', 0)) * formula.get('multiplier', 1)
                if not 1 <= minimum <= maximum <= MAX_QUANTITY:
                    raise ValueError('Additional equipment quantities must remain within inventory bounds')
    return _expanded_groups(character, rules['groups'], pack.get('training_catalogs', {}), elective_count)


def _expanded_groups(character, groups, catalogs, elective_count=None):
    """One stable numbered receipt per distinct selected proficiency; retain old slots."""
    result = {}
    for identifier, group in groups.items():
        if 'repeat_for_proficiencies' not in group:
            if identifier in result:
                raise ValueError('Starting equipment group identities collide')
            result[identifier] = group
            continue
        count = group['repeat_for_proficiencies']
        choices = character.get('combat_choices', {})
        if not isinstance(choices, dict):
            raise ValueError('Repeated equipment needs saved proficiency choices')
        if elective_count is not None and (type(elective_count) is not int or not 0 <= elective_count <= MAX_QUANTITY):
            raise ValueError('Repeated equipment needs a bounded elective count')
        for family in ('ancient', 'modern'):
            values = choices.get(family, [])
            known = {row['id'] for row in catalogs[family]}
            if (not isinstance(values, list) or len(values) > MAX_QUANTITY or
                    any(not isinstance(value, str) or value not in known for value in values)):
                raise ValueError('Repeated equipment needs bounded known weapon choices')
        count = max(count, elective_count or 0)
        receipts = character.get('starting_equipment_groups', {})
        if not isinstance(receipts, dict) or len(receipts) > MAX_QUANTITY:
            raise ValueError('Repeated equipment needs bounded retained receipts')
        for saved in receipts:
            if not isinstance(saved, str):
                raise ValueError('Starting equipment identities must be strings')
            match = re.fullmatch(re.escape(identifier) + r'-([1-9][0-9]{0,3})', saved)
            if match:
                count = max(count, int(match[1]))
        if count > MAX_QUANTITY or len(result) + count > MAX_QUANTITY:
            raise ValueError('Repeated equipment exceeds supported group count')
        for slot in range(1, count + 1):
            key = identifier + '-' + str(slot)
            if key in result or key in groups:
                raise ValueError('Starting equipment group identities collide')
            expanded = deepcopy(group)
            expanded.pop('repeat_for_proficiencies')
            expanded.update(name=group['name'] + ' ' + str(slot), proficiency_slot=slot)
            result[key] = expanded
    if len(result) > MAX_QUANTITY:
        raise ValueError('Starting equipment exceeds supported group count')
    return result


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
    groups = starting_group_rules(character, pack)
    receipts = character['starting_equipment_groups']
    if (not groups or not isinstance(receipts, dict) or not 0 < len(receipts) <= MAX_QUANTITY
            or set(receipts) - set(groups)):
        raise ValueError('Starting equipment receipts require matching pinned groups')
    seen = _other_receipt_ids(character)
    for identifier, receipt in receipts.items():
        group = groups[identifier]
        expected_fields = {'selection', 'grants', 'source'} | ({'condition'} if 'condition' in group else set())
        if (not isinstance(receipt, dict) or set(receipt) != expected_fields
                or not isinstance(receipt['selection'], str) or receipt['selection'] not in group['options']
                or not isinstance(receipt['grants'], list)
                or _canonical(receipt['source']) != _canonical(group['source'])):
            raise ValueError('Invalid starting equipment group receipt')
        if 'condition' in group:
            condition = receipt['condition']
            if (not isinstance(condition, dict) or set(condition) != {'rolls', 'value'}
                    or type(condition['value']) is not int
                    or condition['value'] != formula_value(group['condition']['formula'], condition['rolls'])):
                raise ValueError('Invalid original starting condition dice')
        definitions = [{'item_id': receipt['selection'], 'quantity': group['quantity']},
                       *group.get('additional_grants', {}).get(receipt['selection'], [])]
        if len(receipt['grants']) != len(definitions):
            raise ValueError('Starting equipment grants do not match their original selection')
        for grant, definition in zip(receipt['grants'], definitions):
            expected = {'item_id', 'possession_id', 'quantity'}
            if 'quantity_formula' in definition:
                expected.add('rolls')
                quantity = formula_value(definition['quantity_formula'], grant.get('rolls') if isinstance(grant, dict) else None)
            else:
                quantity = definition['quantity']
            if (not isinstance(grant, dict) or set(grant) != expected
                    or grant['item_id'] != definition['item_id']
                    or type(grant['quantity']) is not int or grant['quantity'] != quantity
                    or not _possession_id(grant['possession_id']) or grant['possession_id'] in seen):
                raise ValueError('Invalid starting equipment group grant')
            seen.add(grant['possession_id'])


def acquire_starting_group(character, pack, group_id, selection, identifier_factory, die=None, *, elective_count=None):
    """Add one free selected grant once, preserving funds and current possessions."""
    validate_starting_groups(character, pack)
    groups = starting_group_rules(character, pack, elective_count)
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
    definitions = [{'item_id': selection, 'quantity': group['quantity']},
                   *group.get('additional_grants', {}).get(selection, [])]
    if len(inventory['items']) + len(definitions) > MAX_QUANTITY:
        raise ValueError('Starting equipment inventory is full')
    if ('condition' in group or any('quantity_formula' in item for item in definitions)) and not callable(die):
        raise ValueError('Random starting equipment requires a dice source')
    grants = []
    for grant in definitions:
        identifier = identifier_factory()
        if not _possession_id(identifier) or identifier in existing:
            raise ValueError('Starting equipment needs a new UUID possession identity')
        existing.add(identifier)
        record = {'item_id': grant['item_id'], 'possession_id': identifier}
        if 'quantity_formula' in grant:
            record['rolls'] = roll_formula(grant['quantity_formula'], die)
            record['quantity'] = formula_value(grant['quantity_formula'], record['rolls'])
        else:
            record['quantity'] = grant['quantity']
        definition = next(item for item in pack['items'] if item['id'] == grant['item_id'])
        shots = (definition['capacity'] if definition['category'] == 'ammunition'
                 or (definition['category'] == 'weapon' and definition.get('weapon_kind', 'ranged') == 'ranged')
                 else None)
        inventory['items'].append({'id': identifier, 'item_id': grant['item_id'], 'quantity': record['quantity'],
                                  'location': group['location'], 'equipped': False, 'shots': shots})
        grants.append(record)
    receipts[group_id] = {'selection': selection, 'grants': grants, 'source': deepcopy(group['source'])}
    if 'condition' in group:
        formula = group['condition']['formula']
        rolls = roll_formula(formula, die)
        receipts[group_id]['condition'] = {'rolls': rolls, 'value': formula_value(formula, rolls)}
    return {'equipment': inventory, 'starting_equipment_groups': receipts}


def project_starting_groups(character, pack, training=None):
    """Project retained grants and honor-system training guidance without dice."""
    validate_starting_groups(character, pack)
    groups = starting_group_rules(character, pack, len(training['elective']) if training is not None else None)
    receipts = character.get('starting_equipment_groups', {})
    result = []
    for identifier, group in groups.items():
        view = {'id': identifier, **deepcopy(group), 'generated': identifier in receipts,
                'receipt': deepcopy(receipts.get(identifier))}
        if group.get('option_requirements'):
            if training is None:
                raise ValueError('Starting equipment requirements need actual saved training')
            selections = {key: list(training[key]) for key in ('skills', 'ancient', 'modern')}
            if 'proficiency_slot' in group:
                elective = training['elective']
                slot = group['proficiency_slot'] - 1
                selected = elective[slot] if slot < len(elective) else None
                for family in ('ancient', 'modern'):
                    selections[family] = [selected['id']] if selected and selected['family'] == family else []
                view['training_name'] = (next(row['name'] for row in pack['training_catalogs'][selected['family']]
                    if row['id'] == selected['id']) if selected else 'Choose this weapon proficiency')
            view['option_requirements'] = {option: project_ability_requirements(
                compile_ability_requirements({'requirements': rows}, pack['training_catalogs'], ()),
                level=character['level'], attributes={}, selections=selections)
                for option, rows in group['option_requirements'].items()}
            for requirements in view['option_requirements'].values():
                for row in requirements:
                    row['text'] = row['name'] + (' is recorded.' if row['satisfied'] else ' is not recorded for this starting choice.')
        result.append(view)
    return {'supported': bool(groups), 'groups': result}


def validate_starting_group_upgrade(character, previous, target):
    """Permit added groups but require acquired definitions to stay unchanged."""
    validate_starting_groups(character, previous)
    before, after = starting_group_rules(character, previous), starting_group_rules(character, target)
    for identifier in character.get('starting_equipment_groups', {}):
        if _canonical(before.get(identifier)) != _canonical(after.get(identifier)):
            raise ValueError('This update changes recorded starting equipment group rules. '
                             'Receipt migration is not yet supported; current rules remain intact.')
