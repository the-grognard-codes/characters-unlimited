"""Source-bound starting money for reviewed Rifts classes."""

from copy import deepcopy
import json
from typing import Any, Callable

MAX_SAFE_INTEGER = 9_007_199_254_740_991


def _safe_integer(value: Any) -> bool:
    return type(value) is int and -MAX_SAFE_INTEGER <= value <= MAX_SAFE_INTEGER


def _canonical(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError, RecursionError) as error:
        raise ValueError('Invalid starting funds source evidence') from error


def _rules(pack: dict[str, Any]) -> dict[str, Any] | None:
    if (not isinstance(pack, dict) or pack.get('id') != 'rifts-equipment'
            or pack.get('game') != 'rifts'):
        raise ValueError('Unsupported starting funds rule pack')
    rules = pack.get('starting_funds')
    if rules is None:
        return None
    if (not isinstance(rules, dict) or set(rules) != {'character_class', 'definitions', 'guidance'}
            or not isinstance(rules['character_class'],str) or not rules['character_class']
            or not isinstance(rules['definitions'], list)
            or len(rules['definitions']) != 2
            or not isinstance(rules['guidance'], list)
            or len(rules['guidance']) > 100
            or any(not isinstance(note, str) for note in rules['guidance'])):
        raise ValueError('Invalid pinned starting funds rules')
    identifiers = set()
    for definition in rules['definitions']:
        if (not isinstance(definition, dict)
                or set(definition) != {'id', 'name', 'count', 'sides', 'multiplier', 'source'}
                or definition['id'] not in ('credits', 'saleable_goods')
                or definition['id'] in identifiers
                or not isinstance(definition['name'], str) or not definition['name']
                or type(definition['count']) is not int or not 1 <= definition['count'] <= 1000
                or type(definition['sides']) is not int or not 1 <= definition['sides'] <= 1000
                or type(definition['multiplier']) is not int or not 1 <= definition['multiplier'] <= MAX_SAFE_INTEGER
                or definition['count'] * definition['sides'] * definition['multiplier'] > MAX_SAFE_INTEGER
                or not isinstance(definition['source'], dict)):
            raise ValueError('Invalid pinned starting funds definition')
        _canonical(definition['source'])
        identifiers.add(definition['id'])
    if identifiers != {'credits', 'saleable_goods'}:
        raise ValueError('Incomplete pinned starting funds definitions')
    return rules


def _supported(character: dict[str, Any], rules: dict[str, Any] | None) -> bool:
    return (rules is not None and character.get('game') == 'rifts'
            and character.get('character_class') == rules['character_class'])


def validate_starting_funds(character: dict[str, Any], pack: dict[str, Any]) -> None:
    """Validate saved rolls and evidence against their pinned definitions."""
    if 'starting_funds' not in character:
        return
    rules = _rules(pack)
    if not _supported(character, rules):
        raise ValueError('Starting funds require pinned Rifts rules for this class')
    assert rules is not None
    records = character['starting_funds']
    definitions = {item['id']: item for item in rules['definitions']}
    if not isinstance(records, dict) or set(records) != definitions.keys():
        raise ValueError('Starting funds do not match pinned definitions')
    for identifier, definition in definitions.items():
        record = records[identifier]
        if (not isinstance(record, dict) or set(record) != {'rolls', 'value', 'source'}
                or not isinstance(record['rolls'], list)
                or len(record['rolls']) != definition['count']
                or any(type(face) is not int or not 1 <= face <= definition['sides']
                       for face in record['rolls'])
                or not _safe_integer(record['value'])
                or record['value'] != sum(record['rolls']) * definition['multiplier']
                or _canonical(record['source']) != _canonical(definition['source'])):
            raise ValueError('Invalid starting funds record')


def acquire_starting_funds(
        character: dict[str, Any], pack: dict[str, Any], die: Callable[[int], int]
) -> dict[str, Any]:
    """Draw the two separate money amounts once and add only credits to inventory."""
    if 'starting_funds' in character:
        raise ValueError('Starting funds have already been generated')
    rules = _rules(pack)
    if not _supported(character, rules):
        raise ValueError('Starting funds require reviewed rules for the selected Rifts class')
    if not callable(die):
        raise ValueError('A dice source is required')
    assert rules is not None
    inventory = deepcopy(character.get('equipment', {'credits': 0, 'items': []}))
    if (not isinstance(inventory, dict) or set(inventory) != {'credits', 'items'}
            or not _safe_integer(inventory['credits']) or not isinstance(inventory['items'], list)):
        raise ValueError('Invalid equipment inventory')
    records = {}
    for definition in rules['definitions']:
        rolls = []
        for _ in range(definition['count']):
            face = die(definition['sides'])
            if type(face) is not int or not 1 <= face <= definition['sides']:
                raise ValueError('Dice source returned an invalid starting funds value')
            rolls.append(face)
        records[definition['id']] = {
            'rolls': rolls,
            'value': sum(rolls) * definition['multiplier'],
            'source': deepcopy(definition['source']),
        }
    credits = inventory['credits'] + records['credits']['value']
    if not _safe_integer(credits):
        raise ValueError('Starting credits exceed the supported range')
    inventory['credits'] = credits
    return {'starting_funds': records, 'equipment': inventory}


def project_starting_funds(character: dict[str, Any], pack: dict[str, Any]) -> dict[str, Any]:
    """Show recorded money and pinned rules without drawing dice."""
    validate_starting_funds(character, pack)
    rules = _rules(pack)
    supported = _supported(character, rules)
    if not supported:
        guidance = (['The pinned equipment rules do not provide starting funds for this class. Review available equipment rule updates before generation.']
                    if character.get('game') == 'rifts' else [])
        return {'supported': False, 'generated': False, 'funds': {},
                'definitions': [], 'guidance': guidance}
    assert rules is not None
    generated = 'starting_funds' in character
    return {
        'supported': True,
        'generated': generated,
        'funds': deepcopy(character['starting_funds']) if generated else {},
        'definitions': deepcopy(rules['definitions']),
        'guidance': list(rules['guidance']),
    }
