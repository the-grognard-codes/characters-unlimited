"""Source-bound Rifts equipment inventory and projection helpers."""

from copy import deepcopy
from .starting_funds import project_starting_funds
from .starting_gear import project_starting_gear
from .starting_choices import project_starting_choices


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
            if definition.get('weapon_kind', 'ranged') == 'melee':
                if item['shots'] is not None:
                    raise ValueError('Melee weapons cannot have shots')
            elif definition.get('weapon_kind', 'ranged') == 'ranged':
                capacity = definition.get('capacity')
                if (type(capacity) is not int or capacity < 1 or type(item['shots']) is not int
                        or not 0 <= item['shots'] <= capacity):
                    raise ValueError('Weapon shots must be within the source capacity')
            else:
                raise ValueError('Unsupported weapon kind')
        elif definition.get('category') in ('armor', 'gear'):
            if item['shots'] is not None:
                raise ValueError('Non-weapon equipment cannot have weapon shots')
        elif definition.get('category') == 'ammunition':
            capacity = definition.get('capacity')
            if (type(capacity) is not int or not 1 <= capacity <= MAX_QUANTITY
                    or type(item['shots']) is not int or not 0 <= item['shots'] <= capacity):
                raise ValueError('Ammunition shots must be within the source capacity')
        else:
            raise ValueError('Unsupported equipment kind')
    return definitions


def validate_inventory(record, pack):
    """Validate a saved inventory against its exact accepted equipment catalog."""
    _inventory(record, pack)
    return deepcopy(record)


def purchase_inventory(record, pack, item_id, quantity, possession_id, unit_cost=None):
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
    price_range = definition.get('cost_credits_range')
    if price_range is not None:
        if (not isinstance(price_range, dict) or set(price_range) != {'min', 'max'}
                or type(price_range['min']) is not int or type(price_range['max']) is not int
                or not 0 <= price_range['min'] <= price_range['max'] <= MAX_SAFE_INTEGER
                or cost is not None):
            raise ValueError('Equipment price range is invalid')
        if type(unit_cost) is not int or not price_range['min'] <= unit_cost <= price_range['max']:
            raise ValueError('Select a whole-number unit price within the reviewed range')
        cost = unit_cost
    elif cost is None:
        raise ValueError('This item has no reviewed purchase price. Its class starting grant is available separately.')
    elif unit_cost is not None and (type(unit_cost) is not int or unit_cost != cost):
        raise ValueError('The supplied unit price differs from the reviewed fixed price')
    if type(cost) is not int or cost < 0 or cost * quantity > MAX_SAFE_INTEGER:
        raise ValueError('Equipment cost is outside the supported range')
    credits = record['credits'] - cost * quantity
    if not _safe_integer(credits):
        raise ValueError('Purchase would exceed the supported credit range')
    shots = (definition['capacity'] if definition['category'] == 'ammunition' or
             (definition['category'] == 'weapon' and
              definition.get('weapon_kind', 'ranged') == 'ranged') else None)
    result = {'credits': credits, 'items': [*deepcopy(record['items']), {
        'id': possession_id, 'item_id': item_id, 'quantity': quantity,
        'location': 'carried', 'equipped': False, 'shots': shots,
    }]}
    _inventory(result, pack)
    return result


def split_inventory(record, pack, possession_id, new_possession_id):
    """Move one unit from a grouped possession into its own unchanged-condition row."""
    _inventory(record, pack)
    possession = next((item for item in record['items'] if item['id'] == possession_id), None)
    if possession is None or possession['quantity'] <= 1:
        raise ValueError('Select a grouped possession with at least two units')
    result = deepcopy(record)
    grouped = next(item for item in result['items'] if item['id'] == possession_id)
    single = {**deepcopy(grouped), 'id': new_possession_id, 'quantity': 1}
    grouped['quantity'] -= 1
    result['items'].append(single)
    _inventory(result, pack)
    return result


def reload_inventory(record, pack, weapon_possession_id, clip_possession_id):
    """Exchange the remaining shots in one carried gun and one carried spare clip."""
    definitions = _inventory(record, pack)
    if (not isinstance(weapon_possession_id, str) or not isinstance(clip_possession_id, str)
            or not weapon_possession_id or not clip_possession_id
            or weapon_possession_id == clip_possession_id):
        raise ValueError('Select distinct gun and clip possessions')
    possessions = {item['id']: item for item in record['items']}
    weapon = possessions.get(weapon_possession_id)
    clip = possessions.get(clip_possession_id)
    if weapon is None or clip is None:
        raise ValueError('Select existing gun and clip possessions')
    weapon_rule = definitions[weapon['item_id']]
    clip_rule = definitions[clip['item_id']]
    if (weapon_rule.get('category') != 'weapon'
            or weapon_rule.get('weapon_kind', 'ranged') != 'ranged'
            or clip_rule.get('category') != 'ammunition'
            or weapon['item_id'] not in clip_rule.get('compatible_weapons', [])
            or weapon_rule['capacity'] != clip_rule['capacity']):
        raise ValueError('This clip is not reviewed for the selected gun')
    if weapon['location'] != 'carried' or clip['location'] != 'carried':
        raise ValueError('Carry both the gun and clip to reload')
    if weapon['quantity'] != 1 or clip['quantity'] != 1:
        raise ValueError('Reload one gun and one clip at a time; split grouped rows into individual possessions')
    result = deepcopy(record)
    by_id = {item['id']: item for item in result['items']}
    by_id[weapon_possession_id]['shots'], by_id[clip_possession_id]['shots'] = (
        by_id[clip_possession_id]['shots'], by_id[weapon_possession_id]['shots'])
    _inventory(result, pack)
    return result


def project_equipment(character, pack, combat):
    """Project catalog and possessions; only carried, equipped items are active."""
    definitions = _catalog(pack)
    inventory = deepcopy(character.get('equipment', {'credits': 0, 'items': []}))
    _inventory(inventory, pack)
    selected = []
    attacks = []
    melee_attacks = []
    armor = []
    sources = []
    warnings = []
    guidance = [
        'Purchases use the recorded character credits.',
        'Removing a possession does not refund its purchase cost.',
        'Stored items have no active combat or armor effects.',
    ]
    carried_weight = 0
    unknown_weight_quantity = 0
    if inventory['credits'] < 0:
        warnings.append('Credit balance is below zero; the deficit is retained and does not block further purchases.')
    low_pp = (combat is None or combat.get('totals', {}).get('strike', {}).get('value') is None)
    choices = combat.get('choices', {}) if isinstance(combat, dict) else {}
    trained = set(choices.get('modern', []))
    reviewed_low_strength = bool(combat and (combat.get('catalog') or {}).get('reviewed_low_strength_melee'))
    weapon_proficiencies = {item['id']: item for item in combat.get('shooting', [])} if isinstance(combat, dict) else {}
    melee_training = {item['id']: item for item in combat.get('melee', [])} if isinstance(combat, dict) else {}
    totals = combat.get('totals', {}) if isinstance(combat, dict) else {}

    for possession in inventory['items']:
        definition = definitions[possession['item_id']]
        projected = {**deepcopy(definition), **deepcopy(possession), 'item_id': possession['item_id']}
        selected.append(projected)
        if possession['location'] == 'carried':
            if definition['weight_lbs'] is None:
                unknown_weight_quantity += possession['quantity']
            else:
                carried_weight += definition['weight_lbs'] * possession['quantity']
        if definition['source'] not in sources:
            sources.append(deepcopy(definition['source']))
        if possession['location'] == 'stored' and possession['equipped']:
            warnings.append(f"{definition['name']} is stored but marked equipped; state is retained without active effects.")
        if possession['location'] != 'carried' or not possession['equipped']:
            continue
        if definition['category'] == 'weapon':
            if definition.get('weapon_kind', 'ranged') == 'melee':
                training = melee_training.get(definition['proficiency'], {})
                results = {}
                for stat in ('strike', 'parry'):
                    result = deepcopy(training.get(stat, totals.get(stat, {
                        'value': None, 'contributions': {}, 'actions': 1, 'sources': [],
                    })))
                    result['sources'] = [*result.get('sources', []), deepcopy(definition['source'])]
                    results[stat] = result
                ps = character.get('attributes', {}).get('PS', {}).get('value')
                damage_total = totals.get('damage', {})
                contributions = damage_total.get('contributions', {})
                normal_bonus = contributions.get('normal_strength')
                damage_bonus = deepcopy(damage_total) if damage_total else {
                    'value': None, 'contributions': {}, 'actions': 1, 'sources': [],
                }
                damage_bonus['sources'] = [*damage_bonus.get('sources', []), {
                    'book': 'Rifts - Ultimate Edition', 'pages': [279, 281],
                    'pdf_pages': [282, 284], 'section': 'Normal human strength damage',
                }]
                normal_strength = (character.get('strength_type', 'normal') == 'normal'
                                   and set(contributions).issubset({'normal_strength','hand_to_hand'})
                                   and type(normal_bonus) is int)
                melee_guidance = ['Held-knife melee only; throwing and enhanced-strength rules remain pending.']
                if low_pp:
                    melee_guidance.append('P.P. below 8 leaves strike and parry totals pending.')
                if type(ps) is not int or ps < 1 or (ps <= 4 and not reviewed_low_strength):
                    damage = 'Pending low-strength melee damage'
                    melee_guidance.append('P.S. 4 or less needs a reviewed melee damage interpretation.')
                elif not damage_total:
                    damage = 'Pending strength damage rules'
                    melee_guidance.append('The accepted combat rules have no reviewed strength damage contribution; review a rule update.')
                elif not normal_strength:
                    damage = 'Pending enhanced-strength melee damage'
                    melee_guidance.append('Enhanced strength melee damage is not yet reviewed.')
                else:
                    damage = definition['damage'].removesuffix(' S.D.C.')
                    combined_bonus = sum(contributions.values()) if ps > 2 else 0
                    if combined_bonus:
                        damage += ' + ' + str(combined_bonus)
                    if ps <= 4:
                        damage = '½ × (' + damage + ')'
                        melee_guidance.append('Physical damage is halved; rounding is not specified by this source.')
                    damage += ' S.D.C.'
                melee_attacks.append({
                    'possession_id': possession['id'], 'item_id': definition['id'],
                    'name': definition['name'], 'quantity': possession['quantity'],
                    'base_damage': definition['damage'], 'damage': damage,
                    'damage_bonus': damage_bonus,
                    'strike': results['strike'], 'parry': results['parry'],
                    'guidance': ' '.join(melee_guidance),
                    'source': deepcopy(definition['source']),
                })
                continue
            wp_id = definition['proficiency']
            has_wp = wp_id in trained and wp_id in weapon_proficiencies
            training = weapon_proficiencies.get(wp_id, {})
            shooting_contributions = deepcopy(training.get('single', {}).get('contributions', {'weapon_proficiency':0}))
            ammunition_guidance = ('No shots remain in this weapon.' if possession['shots'] == 0 else '')
            if not has_wp:
                warnings.append(f"{definition['name']}: matching weapon proficiency is missing; aimed total is unavailable.")
            if ammunition_guidance:
                warnings.append(f"{definition['name']}: {ammunition_guidance}")
            single = {
                'value': None if low_pp or possession['shots'] == 0 else sum(shooting_contributions.values()),
                'contributions': shooting_contributions,
                'actions': 1,
                'sources': [*deepcopy(training.get('single', {}).get('sources', [])), deepcopy(definition['source'])],
            }
            aimed_contributions = ({**shooting_contributions, 'aimed_shot': 2,
                                    'weapon_aimed_bonus': definition['aimed_bonus']} if has_wp else {})
            aimed = {
                'value': None if low_pp or not has_wp or possession['shots'] == 0
                         else sum(aimed_contributions.values()),
                'contributions': aimed_contributions,
                'actions': 2,
                'sources': [*deepcopy(training.get('aimed', {}).get('sources', [])), deepcopy(definition['source'])],
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
    if unknown_weight_quantity:
        guidance.append('Some carried equipment has no source weight; the known carried weight is an incomplete total.')
    if melee_attacks:
        guidance.append('Held knife damage uses the reviewed normal-human strength and training contributions once. Throwing and enhanced strength remain pending.' if reviewed_low_strength else
                        'Held knife damage adds the normal human strength bonus once. Throwing, enhanced strength and low P.S. melee damage remain pending.')
    if any(item.get('category') == 'ammunition' for item in definitions.values()):
        guidance.append('Reload by swapping the remaining shots in one carried gun and one compatible carried clip. Split grouped gun or clip rows into individual possessions first.')
    funds = project_starting_funds(character, pack)
    gear = project_starting_gear(character, pack)
    starting = project_starting_choices(character, pack)
    if starting['supported']:
        # Historical pack guidance remains immutable; show the currently available path.
        funds['guidance'] = [note for note in funds['guidance']
                             if note != 'The rest of the Vagabond starting equipment is not yet implemented.']
        gear['guidance'] = [note for note in gear['guidance']
                            if note != 'Knife, armor, gun, spare clip and transport choices remain pending.']
    return {
        'catalog': deepcopy(pack['items']), 'inventory': inventory, 'items': selected,
        'attacks': attacks, 'melee_attacks': melee_attacks,
        'armor': armor, 'carried_weight_lbs': carried_weight,
        'warnings': warnings, 'guidance': guidance, 'sources': sources,
        'starting_funds': funds,
        'starting_gear': gear,
        'starting_choices': starting,
        'carried_weight_complete': unknown_weight_quantity == 0,
        'unknown_carried_weight_quantity': unknown_weight_quantity,
    }


def compare_equipment_views(before, after):
    """Describe catalog corrections and their effects without changing possessions."""
    changes = []
    def add(name, old, new):
        if old != new:
            changes.append({'name': name, 'before': deepcopy(old), 'after': deepcopy(new)})

    add('Carried weight (lb)', before['carried_weight_lbs'], after['carried_weight_lbs'])
    add('Starting funds rules', before['starting_funds']['definitions'], after['starting_funds']['definitions'])
    add('Starting personal gear rules', before['starting_gear']['definitions'], after['starting_gear']['definitions'])
    add('Starting equipment choice rules', before['starting_choices']['definitions'], after['starting_choices']['definitions'])
    add('Carried items with unspecified weight', before['unknown_carried_weight_quantity'], after['unknown_carried_weight_quantity'])
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
    old_melee = {item['possession_id']: item for item in before.get('melee_attacks', [])}
    new_melee = {item['possession_id']: item for item in after.get('melee_attacks', [])}
    for number, possession_id in enumerate(dict.fromkeys([*old_melee, *new_melee]), start=1):
        old = old_melee.get(possession_id, {})
        new = new_melee.get(possession_id, {})
        name = new.get('name', old.get('name', possession_id))
        add(f'{name} (melee {number}): damage', old.get('damage'), new.get('damage'))
        add(f'{name} (melee {number}): guidance', old.get('guidance'), new.get('guidance'))
        for field in ('value', 'contributions'):
            add(f'{name} (melee {number}): strength damage bonus {field}',
                old.get('damage_bonus', {}).get(field), new.get('damage_bonus', {}).get(field))
        for stat in ('strike', 'parry'):
            for field in ('value', 'contributions'):
                label = ' total' if field == 'value' else ' contributions'
                add(f'{name} (melee {number}): {stat}{label}',
                    old.get(stat, {}).get(field), new.get(stat, {}).get(field))
    add('Equipment warnings', before['warnings'], after['warnings'])
    add('Equipment guidance', before['guidance'], after['guidance'])
    return changes
