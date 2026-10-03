"""Source-bound fixed personal gear for the Rifts Vagabond."""

from copy import deepcopy
import json
from typing import Any, Callable
from uuid import UUID


MAX_SAFE_INTEGER = 9_007_199_254_740_991
MAX_QUANTITY = 1000


def _canonical(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError, RecursionError) as error:
        raise ValueError('Invalid starting gear source evidence') from error


def _possession_id(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return str(UUID(value)) == value
    except (ValueError, AttributeError):
        return False


def _rules(pack: dict[str, Any]) -> dict[str, Any] | None:
    if (not isinstance(pack, dict) or pack.get('id') != 'rifts-equipment'
            or pack.get('game') != 'rifts'):
        raise ValueError('Unsupported starting gear rule pack')
    rules = pack.get('starting_gear')
    if rules is None:
        return None
    if (not isinstance(rules, dict)
            or set(rules) != {'character_class', 'grants', 'source', 'guidance'}
            or rules['character_class'] != 'vagabond'
            or not isinstance(rules['grants'], list)
            or not 0 < len(rules['grants']) <= MAX_QUANTITY
            or not isinstance(rules['source'], dict)
            or not isinstance(rules['guidance'], list)
            or len(rules['guidance']) > 100
            or any(not isinstance(note, str) for note in rules['guidance'])
            or not isinstance(pack.get('items'), list)):
        raise ValueError('Invalid pinned starting gear rules')
    source = _canonical(rules['source'])
    catalog = {}
    for item in pack['items']:
        if (not isinstance(item, dict) or not isinstance(item.get('id'), str)
                or not item['id'] or item['id'] in catalog):
            raise ValueError('Invalid starting gear catalog')
        catalog[item['id']] = item
    seen = set()
    for grant in rules['grants']:
        if (not isinstance(grant, dict) or set(grant) != {'item_id', 'quantity'}
                or not isinstance(grant['item_id'], str)
                or grant['item_id'] not in catalog or grant['item_id'] in seen
                or type(grant['quantity']) is not int
                or not 1 <= grant['quantity'] <= MAX_QUANTITY):
            raise ValueError('Invalid pinned starting gear grant')
        item = catalog[grant['item_id']]
        if (item.get('category') != 'gear' or item.get('cost_credits', object()) is not None
                or item.get('weight_lbs', object()) is not None
                or _canonical(item.get('source')) != source):
            raise ValueError('Starting gear grant requires matching unpriced personal gear')
        seen.add(grant['item_id'])
    return rules


def _supported(character: dict[str, Any], rules: dict[str, Any] | None) -> bool:
    return (rules is not None and character.get('game') == 'rifts'
            and character.get('character_class') == rules['character_class'])


def validate_starting_gear(character: dict[str, Any], pack: dict[str, Any]) -> None:
    """Check the original grant receipt against the exact pinned rules."""
    if 'starting_gear' not in character:
        return
    rules = _rules(pack)
    if not _supported(character, rules):
        raise ValueError('Starting gear requires pinned Rifts Vagabond rules')
    assert rules is not None
    receipt = character['starting_gear']
    if (not isinstance(receipt, dict) or set(receipt) != {'grants', 'source'}
            or not isinstance(receipt['grants'], list)
            or len(receipt['grants']) != len(rules['grants'])
            or _canonical(receipt['source']) != _canonical(rules['source'])):
        raise ValueError('Starting gear receipt does not match pinned rules')
    expected = {grant['item_id']: grant['quantity'] for grant in rules['grants']}
    seen_items = set()
    seen_possessions = set()
    for grant in receipt['grants']:
        if (not isinstance(grant, dict)
                or set(grant) != {'item_id', 'possession_id', 'quantity'}
                or not isinstance(grant['item_id'], str)
                or grant['item_id'] not in expected or grant['item_id'] in seen_items
                or not _possession_id(grant['possession_id'])
                or grant['possession_id'] in seen_possessions
                or type(grant['quantity']) is not int
                or grant['quantity'] != expected[grant['item_id']]):
            raise ValueError('Invalid starting gear receipt grant')
        seen_items.add(grant['item_id'])
        seen_possessions.add(grant['possession_id'])


def acquire_starting_gear(
        character: dict[str, Any], pack: dict[str, Any], identifier_factory: Callable[[], str]
) -> dict[str, Any]:
    """Append each free fixed grant and return the original receipt for one save."""
    if 'starting_gear' in character:
        raise ValueError('Starting gear has already been granted')
    rules = _rules(pack)
    if not _supported(character, rules):
        raise ValueError('Starting gear is available only to Rifts Vagabonds with pinned rules')
    if not callable(identifier_factory):
        raise ValueError('A possession identity source is required')
    assert rules is not None
    inventory = deepcopy(character.get('equipment', {'credits': 0, 'items': []}))
    if (not isinstance(inventory, dict) or set(inventory) != {'credits', 'items'}
            or type(inventory['credits']) is not int
            or not -MAX_SAFE_INTEGER <= inventory['credits'] <= MAX_SAFE_INTEGER
            or not isinstance(inventory['items'], list)
            or len(inventory['items']) + len(rules['grants']) > MAX_QUANTITY):
        raise ValueError('Invalid or full equipment inventory')
    existing = set()
    for item in inventory['items']:
        if (not isinstance(item, dict) or not isinstance(item.get('id'), str)
                or not item['id'] or item['id'] in existing):
            raise ValueError('Invalid existing equipment possession identities')
        existing.add(item['id'])
    receipt_grants = []
    for grant in rules['grants']:
        possession_id = identifier_factory()
        if not _possession_id(possession_id) or possession_id in existing:
            raise ValueError('Starting gear needs new UUID possession identities')
        existing.add(possession_id)
        receipt_grants.append({'item_id': grant['item_id'],
                               'possession_id': possession_id,
                               'quantity': grant['quantity']})
        inventory['items'].append({
            'id': possession_id, 'item_id': grant['item_id'],
            'quantity': grant['quantity'], 'location': 'carried',
            'equipped': False, 'shots': None,
        })
    return {'starting_gear': {'grants': receipt_grants,
                              'source': deepcopy(rules['source'])},
            'equipment': inventory}


def project_starting_gear(character: dict[str, Any], pack: dict[str, Any]) -> dict[str, Any]:
    """Show fixed grants and the saved receipt without adding possessions."""
    validate_starting_gear(character, pack)
    rules = _rules(pack)
    if not _supported(character, rules):
        guidance = (['Update the equipment rules to preview Vagabond starting gear.']
                    if rules is None and character.get('game') == 'rifts'
                    and character.get('character_class') == 'vagabond' else [])
        return {'supported': False, 'generated': False, 'grants': [],
                'definitions': [], 'source': None, 'guidance': guidance}
    assert rules is not None
    generated = 'starting_gear' in character
    return {'supported': True, 'generated': generated,
            'grants': deepcopy(character['starting_gear']['grants']) if generated else [],
            'definitions': deepcopy(rules['grants']),
            'source': deepcopy(rules['source']),
            'guidance': list(rules['guidance'])}
