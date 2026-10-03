"""Source-bound representative starting choices for the Rifts Vagabond."""

from copy import deepcopy
import json
from typing import Any, Callable
from uuid import UUID


MAX_SAFE_INTEGER = 9_007_199_254_740_991
MAX_QUANTITY = 1000
CHOICE_GROUPS = ('armor', 'gun', 'knife', 'transport')


def _canonical(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError, RecursionError) as error:
        raise ValueError('Invalid starting choices source evidence') from error


def _possession_id(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return str(UUID(value)) == value
    except (ValueError, AttributeError):
        return False


def _catalog(pack: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items = pack.get('items')
    if not isinstance(items, list):
        raise ValueError('Starting choices require an equipment catalog')
    catalog = {}
    for item in items:
        if (not isinstance(item, dict) or not isinstance(item.get('id'), str)
                or not item['id'] or item['id'] in catalog):
            raise ValueError('Invalid starting choices catalog')
        catalog[item['id']] = item
    return catalog


def _rules(pack: dict[str, Any]) -> dict[str, Any] | None:
    if (not isinstance(pack, dict) or pack.get('id') != 'rifts-equipment'
            or pack.get('game') != 'rifts'):
        raise ValueError('Unsupported starting choices rule pack')
    rules = pack.get('starting_choices')
    if rules is None:
        return None
    if (not isinstance(rules, dict)
            or set(rules) != {'character_class', 'options', 'clips', 'source', 'guidance'}
            or rules['character_class'] != 'vagabond'
            or not isinstance(rules['options'], dict)
            or set(rules['options']) != set(CHOICE_GROUPS)
            or not isinstance(rules['clips'], dict)
            or not isinstance(rules['source'], dict)
            or not isinstance(rules['guidance'], list)
            or len(rules['guidance']) > 100
            or any(not isinstance(note, str) for note in rules['guidance'])):
        raise ValueError('Invalid pinned starting choices rules')
    _canonical(rules['source'])
    catalog = _catalog(pack)
    for group in CHOICE_GROUPS:
        options = rules['options'][group]
        if (not isinstance(options, list) or not 0 < len(options) <= MAX_QUANTITY
                or any(not isinstance(identifier, str) or identifier not in catalog
                       for identifier in options)
                or len(set(options)) != len(options)):
            raise ValueError('Invalid pinned starting choices options')
        for identifier in options:
            item = catalog[identifier]
            if ((group == 'armor' and item.get('category') != 'armor')
                    or (group == 'gun' and (item.get('category') != 'weapon'
                                            or item.get('weapon_kind', 'ranged') != 'ranged'))
                    or (group == 'knife' and (item.get('category') != 'weapon'
                                              or item.get('weapon_kind') != 'melee'))
                    or (group == 'transport' and item.get('category') != 'gear')):
                raise ValueError('Starting choice has an incompatible equipment category')
    if set(rules['clips']) != set(rules['options']['gun']):
        raise ValueError('Each starting gun needs a pinned spare clip')
    for gun_id, clip_id in rules['clips'].items():
        if not isinstance(clip_id, str) or clip_id not in catalog:
            raise ValueError('Invalid starting clip choice')
        clip = catalog[clip_id]
        gun = catalog[gun_id]
        if (clip.get('category') != 'ammunition'
                or gun_id not in clip.get('compatible_weapons', [])
                or type(clip.get('capacity')) is not int
                or clip['capacity'] != gun.get('capacity')):
            raise ValueError('Starting clip is incompatible with its gun')
    return rules


def _supported(character: dict[str, Any], rules: dict[str, Any] | None) -> bool:
    return (rules is not None and character.get('game') == 'rifts'
            and character.get('character_class') == rules['character_class'])


def _selected(choices: Any, rules: dict[str, Any]) -> dict[str, str]:
    if (not isinstance(choices, dict) or set(choices) != set(CHOICE_GROUPS)
            or any(not isinstance(choices[group], str)
                   or choices[group] not in rules['options'][group]
                   for group in CHOICE_GROUPS)):
        raise ValueError('Select one reviewed armor, gun, knife and transport option')
    return {group: choices[group] for group in CHOICE_GROUPS}


def _grant_ids(choices: dict[str, str], rules: dict[str, Any]) -> list[str]:
    return [*(choices[group] for group in CHOICE_GROUPS), rules['clips'][choices['gun']]]


def validate_starting_choices(character: dict[str, Any], pack: dict[str, Any]) -> None:
    """Check saved selections and grant identities against their pinned rules."""
    if 'starting_choices' not in character:
        return
    rules = _rules(pack)
    if not _supported(character, rules):
        raise ValueError('Starting choices require pinned Rifts Vagabond rules')
    assert rules is not None
    receipt = character['starting_choices']
    if (not isinstance(receipt, dict) or set(receipt) != {'choices', 'grants', 'source'}
            or not isinstance(receipt['grants'], list)
            or len(receipt['grants']) != 5
            or _canonical(receipt['source']) != _canonical(rules['source'])):
        raise ValueError('Starting choices receipt does not match pinned rules')
    choices = _selected(receipt['choices'], rules)
    identifiers = _grant_ids(choices, rules)
    seen_possessions = set()
    for grant, identifier in zip(receipt['grants'], identifiers):
        if (not isinstance(grant, dict)
                or set(grant) != {'item_id', 'possession_id', 'quantity'}
                or grant['item_id'] != identifier
                or type(grant['quantity']) is not int or grant['quantity'] != 1
                or not _possession_id(grant['possession_id'])
                or grant['possession_id'] in seen_possessions):
            raise ValueError('Invalid starting choices grant receipt')
        seen_possessions.add(grant['possession_id'])


def acquire_starting_choices(
        character: dict[str, Any], pack: dict[str, Any], choices: dict[str, str],
        identifier_factory: Callable[[], str]
) -> dict[str, Any]:
    """Append five free selected possessions and retain their original receipt."""
    if 'starting_choices' in character:
        raise ValueError('Starting choices have already been granted')
    rules = _rules(pack)
    if not _supported(character, rules):
        raise ValueError('Starting choices are available only to Rifts Vagabonds with pinned rules')
    if not callable(identifier_factory):
        raise ValueError('A possession identity source is required')
    assert rules is not None
    selected = _selected(choices, rules)
    catalog = _catalog(pack)
    inventory = deepcopy(character.get('equipment', {'credits': 0, 'items': []}))
    if (not isinstance(inventory, dict) or set(inventory) != {'credits', 'items'}
            or type(inventory['credits']) is not int
            or not -MAX_SAFE_INTEGER <= inventory['credits'] <= MAX_SAFE_INTEGER
            or not isinstance(inventory['items'], list)
            or len(inventory['items']) + 5 > MAX_QUANTITY):
        raise ValueError('Invalid or full equipment inventory')
    existing = set()
    for item in inventory['items']:
        if (not isinstance(item, dict) or not isinstance(item.get('id'), str)
                or not item['id'] or item['id'] in existing):
            raise ValueError('Invalid existing equipment possession identities')
        existing.add(item['id'])
    grants = []
    for item_id in _grant_ids(selected, rules):
        possession_id = identifier_factory()
        if not _possession_id(possession_id) or possession_id in existing:
            raise ValueError('Starting choices need new UUID possession identities')
        existing.add(possession_id)
        definition = catalog[item_id]
        shots = (definition['capacity'] if definition['category'] == 'ammunition'
                 or (definition['category'] == 'weapon'
                     and definition.get('weapon_kind', 'ranged') == 'ranged') else None)
        grants.append({'item_id': item_id, 'possession_id': possession_id, 'quantity': 1})
        inventory['items'].append({
            'id': possession_id, 'item_id': item_id, 'quantity': 1,
            'location': 'stored' if item_id == selected['transport'] else 'carried',
            'equipped': False, 'shots': shots,
        })
    return {'starting_choices': {'choices': selected, 'grants': grants,
                                 'source': deepcopy(rules['source'])},
            'equipment': inventory}


def project_starting_choices(character: dict[str, Any], pack: dict[str, Any]) -> dict[str, Any]:
    """Show the recorded choice receipt and reviewed options without changing inventory."""
    validate_starting_choices(character, pack)
    rules = _rules(pack)
    if not _supported(character, rules):
        guidance = (['Update the equipment rules to preview Vagabond starting choices.']
                    if rules is None and character.get('game') == 'rifts'
                    and character.get('character_class') == 'vagabond' else [])
        return {'supported': False, 'generated': False, 'choices': {},
                'grants': [], 'definitions': {}, 'source': None, 'guidance': guidance}
    assert rules is not None
    generated = 'starting_choices' in character
    receipt = character['starting_choices'] if generated else {}
    return {'supported': True, 'generated': generated,
            'choices': deepcopy(receipt.get('choices', {})),
            'grants': deepcopy(receipt.get('grants', [])),
            'definitions': deepcopy(rules['options']),
            'source': deepcopy(rules['source']),
            'guidance': list(rules['guidance'])}
