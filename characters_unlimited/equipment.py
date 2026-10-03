"""Source-bound Rifts equipment inventory and projection helpers."""

from copy import deepcopy


MAX_SAFE_INTEGER = 9_007_199_254_740_991
MAX_QUANTITY = 1000


def _catalog(pack):
    if (not isinstance(pack, dict) or pack.get('id') != 'rifts-equipment'
            or pack.get('game') != 'rifts' or not isinstance(pack.get('items'), list)):
        raise ValueError('Unsupported equipment rule pack')
    items = {}
    for item in pack['items']:
        if not isinstance(item, dict) or not isinstance(item.get('id'), str) or item['id'] in items:
            raise ValueError('Equipment catalog has invalid or duplicate item identities')
        items[item['id']] = item
    return items


def _safe_integer(value):
    return type(value) is int and -MAX_SAFE_INTEGER <= value <= MAX_SAFE_INTEGER


def _inventory(record, pack):
    definitions = _catalog(pack)
    if (not isinstance(record, dict) or set(record) != {'credits', 'items'}
            or not _safe_integer(record['credits']) or not isinstance(record['items'], list)
            or len(record['items']) > MAX_QUANTITY):
        raise ValueError('Invalid equipment inventory')
    possessions = set()
    for item in record['items']:
        if not isinstance(item, dict) or set(item) != {
                'id', 'item_id', 'quantity', 'location', 'equipped', 'shots'}:
            raise ValueError('Invalid equipment possession')
        if (not isinstance(item['id'], str) or not item['id'] or item['id'] in possessions
            or not isinstance(item['item_id'], str) or item['item_id'] not in definitions):
            raise ValueError('Unknown or duplicate equipment possession')
        possessions.add(item['id'])
        if (type(item['quantity']) is not int or not 1 <= item['quantity'] <= MAX_QUANTITY
                or item['location'] not in ('carried', 'stored') or type(item['equipped']) is not bool):
            raise ValueError('Invalid equipment quantity or state')
        definition = definitions[item['item_id']]
        if definition.get('category') == 'weapon':
            capacity = definition.get('capacity')
            if (type(capacity) is not int or capacity < 1 or type(item['shots']) is not int
                    or not 0 <= item['shots'] <= capacity):
                raise ValueError('Weapon shots must be within the source capacity')
        elif definition.get('category') == 'armor':
            if item['shots'] is not None:
                raise ValueError('Armor cannot have weapon shots')
        else:
            raise ValueError('Unsupported equipment kind')
    return definitions


def validate_inventory(record, pack):
    """Validate a saved inventory against its exact accepted equipment catalog."""
    _inventory(record, pack)
    return deepcopy(record)


def purchase_inventory(record, pack, item_id, quantity, possession_id):
    """Return an atomic purchase result; this records credits, not a real payment."""
    definitions = _inventory(record, pack)
    if not isinstance(item_id, str) or item_id not in definitions:
        raise ValueError('Select an available equipment item')
    if type(quantity) is not int or not 1 <= quantity <= MAX_QUANTITY:
        raise ValueError('Purchase quantity must be between one and one thousand')
    if not isinstance(possession_id, str) or not possession_id or any(
            item['id'] == possession_id for item in record['items']):
        raise ValueError('Equipment possession ID must be new and nonempty')
    definition = definitions[item_id]
    cost = definition.get('cost_credits')
    if type(cost) is not int or cost < 0 or cost * quantity > MAX_SAFE_INTEGER:
        raise ValueError('Equipment cost is outside the supported range')
    credits = record['credits'] - cost * quantity
    if not _safe_integer(credits):
        raise ValueError('Purchase would exceed the supported credit range')
    shots = definition['capacity'] if definition['category'] == 'weapon' else None
    result = {'credits': credits, 'items': [*deepcopy(record['items']), {
        'id': possession_id, 'item_id': item_id, 'quantity': quantity,
        'location': 'carried', 'equipped': False, 'shots': shots,
    }]}
    _inventory(result, pack)
    return result


def project_equipment(character, pack, combat):
    """Project catalog and possessions; only carried, equipped items are active."""
    definitions = _catalog(pack)
    inventory = deepcopy(character.get('equipment', {'credits': 0, 'items': []}))
    _inventory(inventory, pack)
    selected = []
    attacks = []
    armor = []
    sources = []
    warnings = []
    guidance = [
        'Purchases use the recorded character credits.',
        'Removing a possession does not refund its purchase cost.',
        'Stored items have no active combat or armor effects.',
    ]
    carried_weight = 0
    if inventory['credits'] < 0:
        warnings.append('Credit balance is below zero; the deficit is retained and does not block further purchases.')
    low_pp = (combat is None or combat.get('totals', {}).get('strike', {}).get('value') is None)
    choices = combat.get('choices', {}) if isinstance(combat, dict) else {}
    trained = set(choices.get('modern', []))
    combat_catalog = (combat.get('catalog') or {}) if isinstance(combat, dict) else {}
    weapon_proficiencies = {item['id']: item for item in combat_catalog.get('modern', [])}

    for possession in inventory['items']:
        definition = definitions[possession['item_id']]
        projected = {**deepcopy(definition), **deepcopy(possession), 'item_id': possession['item_id']}
        selected.append(projected)
        if possession['location'] == 'carried':
            carried_weight += definition['weight_lbs'] * possession['quantity']
        if definition['source'] not in sources:
            sources.append(deepcopy(definition['source']))
        if possession['location'] == 'stored' and possession['equipped']:
            warnings.append(f"{definition['name']} is stored but marked equipped; state is retained without active effects.")
        if possession['location'] != 'carried' or not possession['equipped']:
            continue
        if definition['category'] == 'weapon':
            wp_id = definition['proficiency']
            has_wp = wp_id in trained and wp_id in weapon_proficiencies
            wp_bonus = weapon_proficiencies[wp_id]['strike'] if has_wp else 0
            ammunition_guidance = ('No shots remain in this weapon.' if possession['shots'] == 0 else '')
            if not has_wp:
                warnings.append(f"{definition['name']}: matching weapon proficiency is missing; aimed total is unavailable.")
            if ammunition_guidance:
                warnings.append(f"{definition['name']}: {ammunition_guidance}")
            single = {
                'value': None if low_pp or possession['shots'] == 0 else wp_bonus,
                'contributions': {'weapon_proficiency': wp_bonus},
                'actions': 1,
                'sources': [deepcopy(definition['source'])],
            }
            aimed_contributions = ({'weapon_proficiency': wp_bonus, 'aimed_shot': 2,
                                    'weapon_aimed_bonus': definition['aimed_bonus']} if has_wp else {})
            aimed = {
                'value': None if low_pp or not has_wp or possession['shots'] == 0
                         else sum(aimed_contributions.values()),
                'contributions': aimed_contributions,
                'actions': 2,
                'sources': [deepcopy(definition['source'])],
            }
            attacks.append({
                'possession_id': possession['id'], 'item_id': definition['id'],
                'name': definition['name'], 'quantity': possession['quantity'],
                'shots': possession['shots'], 'damage': definition['damage'],
                'range_feet': definition['range_feet'], 'range_meters': definition['range_meters'],
                'single': single, 'aimed': aimed,
                'guidance': ammunition_guidance or ('P.P. below 8 leaves attack totals pending.' if low_pp else ''),
                'source': deepcopy(definition['source']),
            })
        elif definition['category'] == 'armor':
            armor.append({
                'possession_id': possession['id'], 'item_id': definition['id'],
                'name': definition['name'], 'quantity': possession['quantity'],
                'sheet_name': definition.get('sheet_name', definition['name']),
                'cost_credits': definition['cost_credits'], 'weight_lbs': definition['weight_lbs'],
                'locations': deepcopy(definition['locations']),
                'movement_penalty': definition['movement_penalty'],
                'source': deepcopy(definition['source']),
                'movement_source': deepcopy(definition['movement_source']),
            })
            if definition['movement_source'] not in sources:
                sources.append(deepcopy(definition['movement_source']))

    active_armor_quantity = sum(item['quantity'] for item in armor)
    if active_armor_quantity > 1:
        warnings.append('Multiple equipped armor units are retained; location capacities are listed separately and are not stacked.')
    if carried_weight > MAX_SAFE_INTEGER:
        raise ValueError('Carried weight exceeds the supported range')
    if any(item['location'] == 'stored' for item in inventory['items']):
        guidance.append('Stored possessions remain recorded and do not affect carried weight, combat or armor capacity.')
    if armor:
        guidance.append('Armor capacities are per location; movement skill penalties are not applied as a universal speed penalty.')
    return {
        'catalog': deepcopy(pack['items']), 'inventory': inventory, 'items': selected,
        'attacks': attacks, 'armor': armor, 'carried_weight_lbs': carried_weight,
        'warnings': warnings, 'guidance': guidance, 'sources': sources,
    }


def compare_equipment_views(before, after):
    """Describe catalog corrections and their effects without changing possessions."""
    changes = []
    def add(name, old, new):
        if old != new:
            changes.append({'name': name, 'before': deepcopy(old), 'after': deepcopy(new)})

    add('Carried weight (lb)', before['carried_weight_lbs'], after['carried_weight_lbs'])
    old_catalog = {item['id']: item for item in before['catalog']}
    new_catalog = {item['id']: item for item in after['catalog']}
    for item_id in dict.fromkeys([*old_catalog, *new_catalog]):
        old = old_catalog.get(item_id, {})
        new = new_catalog.get(item_id, {})
        name = new.get('name', old.get('name', item_id))
        for field in sorted(set(old) | set(new)):
            if field != 'id':
                add(f'{name}: {field.replace("_", " ")}', old.get(field), new.get(field))
    old_attacks = {item['possession_id']: item for item in before['attacks']}
    new_attacks = {item['possession_id']: item for item in after['attacks']}
    for number, possession_id in enumerate(dict.fromkeys([*old_attacks, *new_attacks]), start=1):
        old = old_attacks.get(possession_id, {})
        new = new_attacks.get(possession_id, {})
        name = new.get('name', old.get('name', possession_id))
        for attack in ('single', 'aimed'):
            for field in ('value', 'contributions', 'actions'):
                label = 'strike total' if field == 'value' else field
                add(f'{name} (weapon {number}): {attack} {label}',
                    old.get(attack, {}).get(field), new.get(attack, {}).get(field))
    add('Equipment warnings', before['warnings'], after['warnings'])
    add('Equipment guidance', before['guidance'], after['guidance'])
    return changes
