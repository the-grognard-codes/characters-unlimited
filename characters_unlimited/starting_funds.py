"""Source-bound starting money for reviewed Rifts classes."""

from copy import deepcopy
import json
from typing import Any, Callable
from .recorded_formulas import validate_formula, formula_value, roll_formula

MAX_SAFE_INTEGER = 9_007_199_254_740_991


def _safe_integer(value: Any) -> bool:
    return type(value) is int and -MAX_SAFE_INTEGER <= value <= MAX_SAFE_INTEGER


def _canonical(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError, RecursionError) as error:
        raise ValueError('Invalid starting funds source evidence') from error


def _formula(definition, choice=None):
    formula = {key: definition[key] for key in ('count', 'sides', 'constant', 'multiplier') if key in definition}
    if 'choice' in definition:
        formula['constant'] = choice
    return formula


def _validate_choice(definition, value):
    bounds = definition['choice']
    if not _safe_integer(value) or not bounds['minimum'] <= value <= bounds['maximum']:
        raise ValueError('Select starting funds within the reviewed whole-number range')


def starting_funds_rules(pack: dict[str, Any]) -> dict[str, Any] | None:
    """Compile pinned definitions without drawing dice or validating receipts."""
    if (not isinstance(pack, dict) or pack.get('id') != 'rifts-equipment'
            or pack.get('game') != 'rifts'):
        raise ValueError('Unsupported starting funds rule pack')
    rules = pack.get('starting_funds')
    if rules is None:
        return None
    owned = pack.get('class_profile_format') == 'owned-v1'
    if (not isinstance(rules, dict) or set(rules) != {'character_class', 'definitions', 'guidance'}
            or not isinstance(rules['character_class'],str) or not rules['character_class']
            or not isinstance(rules['definitions'], list)
            or not (1 <= len(rules['definitions']) <= 2 if owned else len(rules['definitions']) == 2)
            or not isinstance(rules['guidance'], list)
            or len(rules['guidance']) > 100
            or any(not isinstance(note, str) for note in rules['guidance'])):
        raise ValueError('Invalid pinned starting funds rules')
    identifiers = set()
    for definition in rules['definitions']:
        if (not isinstance(definition, dict)
                or not {'id', 'name', 'count', 'sides', 'multiplier', 'source'} <= set(definition)
                or set(definition) - {'id', 'name', 'count', 'sides', 'multiplier', 'source', *(['constant', 'choice'] if owned else [])}
                or definition['id'] not in ('credits', 'saleable_goods')
                or definition['id'] in identifiers
                or not isinstance(definition['name'], str) or not definition['name']
                or (not owned and (type(definition['count']) is not int or definition['count'] < 1
                                  or type(definition['sides']) is not int or definition['sides'] < 1))
                or not isinstance(definition['source'], dict)):
            raise ValueError('Invalid pinned starting funds definition')
        if 'choice' in definition:
            choice = definition['choice']
            if (not isinstance(choice, dict) or set(choice) != {'name', 'minimum', 'maximum'}
                    or not isinstance(choice['name'], str) or not choice['name'].strip()
                    or not _safe_integer(choice['minimum']) or not _safe_integer(choice['maximum'])
                    or not 0 <= choice['minimum'] <= choice['maximum']
                    or type(definition['count']) is not int or definition['count'] != 0
                    or type(definition['sides']) is not int or definition['sides'] != 0
                    or 'constant' in definition):
                raise ValueError('Starting funds choices need bounded amounts without dice or another constant')
        formula = _formula(definition, definition.get('choice', {}).get('maximum'))
        validate_formula(formula)
        if (formula.get('constant', 0) < 0 or
                (formula['count'] * formula['sides'] + formula.get('constant', 0)) * formula['multiplier'] > MAX_SAFE_INTEGER):
            raise ValueError('Starting funds exceed the supported nonnegative range')
        _canonical(definition['source'])
        identifiers.add(definition['id'])
    if 'credits' not in identifiers or (not owned and identifiers != {'credits', 'saleable_goods'}):
        raise ValueError('Incomplete pinned starting funds definitions')
    return rules


def _supported(character: dict[str, Any], rules: dict[str, Any] | None) -> bool:
    return (rules is not None and character.get('game') == 'rifts'
            and character.get('character_class') == rules['character_class'])


def validate_starting_funds(character: dict[str, Any], pack: dict[str, Any]) -> None:
    """Validate saved rolls and evidence against their pinned definitions."""
    if 'starting_funds' not in character:
        return
    rules = starting_funds_rules(pack)
    if not _supported(character, rules):
        raise ValueError('Starting funds require pinned Rifts rules for this class')
    assert rules is not None
    records = character['starting_funds']
    definitions = {item['id']: item for item in rules['definitions']}
    if not isinstance(records, dict) or set(records) != definitions.keys():
        raise ValueError('Starting funds do not match pinned definitions')
    for identifier, definition in definitions.items():
        record = records[identifier]
        if 'choice' in definition:
            _validate_choice(definition, record.get('choice') if isinstance(record, dict) else None)
        if (not isinstance(record, dict) or set(record) != {'rolls', 'value', 'source'} | ({'choice'} if 'choice' in definition else set())
                or not isinstance(record['rolls'], list)
                or len(record['rolls']) != definition['count']
                or any(type(face) is not int or not 1 <= face <= definition['sides']
                       for face in record['rolls'])
                or not _safe_integer(record['value'])
                or record['value'] != formula_value(_formula(definition, record.get('choice')), record['rolls'])
                or _canonical(record['source']) != _canonical(definition['source'])):
            raise ValueError('Invalid starting funds record')


def acquire_starting_funds(
        character: dict[str, Any], pack: dict[str, Any], die: Callable[[int], int], *, choices=None
) -> dict[str, Any]:
    """Draw declared money amounts once and add only credits to inventory."""
    if 'starting_funds' in character:
        raise ValueError('Starting funds have already been generated')
    rules = starting_funds_rules(pack)
    if not _supported(character, rules):
        raise ValueError('Starting funds require reviewed rules for the selected Rifts class')
    if not callable(die):
        raise ValueError('A dice source is required')
    assert rules is not None
    choices = {} if choices is None else choices
    expected_choices = {definition['id'] for definition in rules['definitions'] if 'choice' in definition}
    if not isinstance(choices, dict) or set(choices) != expected_choices:
        raise ValueError('Starting funds choices must match the reviewed definitions')
    for definition in rules['definitions']:
        if 'choice' in definition:
            _validate_choice(definition, choices[definition['id']])
    inventory = deepcopy(character.get('equipment', {'credits': 0, 'items': []}))
    if (not isinstance(inventory, dict) or set(inventory) != {'credits', 'items'}
            or not _safe_integer(inventory['credits']) or not isinstance(inventory['items'], list)):
        raise ValueError('Invalid equipment inventory')
    records = {}
    for definition in rules['definitions']:
        formula = _formula(definition, choices.get(definition['id']))
        rolls = roll_formula(formula, die)
        records[definition['id']] = {
            'rolls': rolls,
            'value': formula_value(formula, rolls),
            'source': deepcopy(definition['source']),
        }
        if 'choice' in definition:
            records[definition['id']]['choice'] = choices[definition['id']]
    credits = inventory['credits'] + records['credits']['value']
    if not _safe_integer(credits):
        raise ValueError('Starting credits exceed the supported range')
    inventory['credits'] = credits
    return {'starting_funds': records, 'equipment': inventory}


def project_starting_funds(character: dict[str, Any], pack: dict[str, Any]) -> dict[str, Any]:
    """Show recorded money and pinned rules without drawing dice."""
    validate_starting_funds(character, pack)
    rules = starting_funds_rules(pack)
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
