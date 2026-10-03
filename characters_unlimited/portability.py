"""Portable save validation. Bundles contain data and never execute rule prose."""

import json
from copy import deepcopy
from datetime import datetime, timezone
from uuid import UUID, uuid4
from .generation import roll_attribute, generation_settings
from .attribute_modifiers import attribute_value

ATTRIBUTES = ('IQ', 'ME', 'MA', 'PS', 'PP', 'PE', 'PB', 'SPD')
MAX_BYTES = 10_000_000


def canonical(value):
    try:
        encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, RecursionError) as error:
        raise ValueError('The bundle must contain finite JSON data') from error
    if len(encoded) > MAX_BYTES:
        raise ValueError('The portable character exceeds the 10 MB limit')
    return encoded


def integer(value):
    return type(value) is int and abs(value) <= 9_007_199_254_740_991


def validate_attributes(attributes):
    if not isinstance(attributes, dict) or set(attributes) - set(ATTRIBUTES):
        raise ValueError('Invalid attribute names')
    for value in attributes.values():
        if not isinstance(value, dict) or not integer(value.get('base')) or not integer(value.get('value')):
            raise ValueError('Attribute values must be supported whole numbers')
        if not integer(value.get('adjustment', 0)) or (value.get('fixed') is not None and not integer(value['fixed'])):
            raise ValueError('Invalid manual attribute value')
        for key in ('rolls', 'bonus_rolls', 'original_rolls', 'kept', 'discarded'):
            rolls = value.get(key, None if key in ('rolls', 'bonus_rolls') else [])
            if not isinstance(rolls, list) or len(rolls) > 2000 or any(not integer(die) for die in rolls):
                raise ValueError('Invalid attribute dice')
        explanation = value.get('explanation')
        source = explanation.get('source') if isinstance(explanation, dict) else None
        if not isinstance(source, dict) or any(not isinstance(source.get(key), str) for key in ('book', 'section')):
            raise ValueError('Attribute source information is missing')
        if 'generation' in value:
            validate_generation(value['generation'])
        rerolls = value.get('rerolls', [])
        if not isinstance(rerolls, list):
            raise ValueError('Invalid reroll history')
        for reroll in rerolls:
            if not isinstance(reroll, dict) or not integer(reroll.get('index')) or not isinstance(reroll.get('rolls'), list) or any(not integer(die) for die in reroll['rolls']):
                raise ValueError('Invalid reroll history')
        modifiers = value.get('modifiers', [])
        if not isinstance(modifiers, list) or len(modifiers) > 100:
            raise ValueError('Invalid attribute modifiers')
        for modifier in modifiers:
            if not isinstance(modifier, dict) or set(modifier) != {'id', 'value', 'rolls', 'source'} or not isinstance(modifier['id'], str) or not integer(modifier['value']):
                raise ValueError('Invalid attribute modifier')
            if not isinstance(modifier['rolls'], list) or any(not integer(roll) for roll in modifier['rolls']) or not isinstance(modifier['source'], dict):
                raise ValueError('Invalid attribute modifier rolls or source')
        expected_value = attribute_value(value)
        if value['value'] != expected_value:
            raise ValueError('Attribute value does not match its fixed value or adjusted base')
        validate_recorded_roll(value)


def validate_recorded_roll(value):
    formula = {'count': 3, 'sides': 6, 'constant': 0, 'exceptional': {'thresholds': [16, 17, 18], 'max_bonus_dice': 2}}
    settings = value.get('generation', {'reroll_ones': False, 'extra_die': False})
    originals = value.get('original_rolls', value['rolls'])
    if len(originals) != 3 + int(settings['extra_die']):
        raise ValueError('Recorded dice do not match the racial attribute pool')
    rerolls = {item['index']: item['rolls'] for item in value.get('rerolls', [])}
    if len(rerolls) != len(value.get('rerolls', [])) or set(rerolls) - set(range(len(originals))):
        raise ValueError('Invalid reroll positions')
    sequence = []
    for index, original in enumerate(originals):
        attempts = rerolls.get(index, [original])
        if not attempts or attempts[0] != original:
            raise ValueError('Reroll attempts do not match the original die')
        sequence.extend(attempts)
    sequence.extend(value['bonus_rolls'])
    dice = iter(sequence)
    expected = roll_attribute(formula, settings, lambda sides: next(dice, 0), value['explanation']['source'])
    if next(dice, None) is not None:
        raise ValueError('Recorded dice contain unexplained extra rolls')
    for key in ('base', 'rolls', 'bonus_rolls'):
        if value[key] != expected[key]:
            raise ValueError(f'Recorded {key} does not match the generation rules')
    for key in ('original_rolls', 'kept', 'discarded', 'rerolls'):
        if key in value and value[key] != expected[key]:
            raise ValueError(f'Recorded {key} does not match the generation rules')


def validate_generation(value):
    if not isinstance(value, dict) or set(value) != {'reroll_ones', 'extra_die'} or any(type(option) is not bool for option in value.values()):
        raise ValueError('Invalid generation options')


def validate_character(character):
    if not isinstance(character, dict) or type(character.get('format_version')) is not int or character['format_version'] != 1:
        raise ValueError('Unsupported character format version')
    if character.get('game') != 'rifts' or character.get('race') != 'human' or character.get('character_class') != 'vagabond':
        raise ValueError('This application version cannot reopen that game or character option')
    try:
        UUID(character['id'])
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise ValueError('Invalid character identity') from error
    for key in ('name', 'notes'):
        if not isinstance(character.get(key), str):
            raise ValueError(f'{key} must be text')
    if character.get('level') != 1 or type(character.get('level')) is not int:
        raise ValueError('This application version supports level-one imports')
    for key in ('completion', 'automation_gaps'):
        if not isinstance(character.get(key), list) or any(not isinstance(item, str) for item in character[key]):
            raise ValueError(f'Invalid {key}')
    attributes = character.get('attributes')
    if not isinstance(attributes, dict):
        raise ValueError('Attribute records are missing')
    validate_attributes(attributes)
    if set(attributes) != set(ATTRIBUTES):
        raise ValueError('The character must retain all eight attribute records')
    if 'generation' in character:
        validate_generation(character['generation'])
    history = character.get('roll_history', [])
    if not isinstance(history, list):
        raise ValueError('Invalid roll history')
    for event in history:
        if not isinstance(event, dict) or not isinstance(event.get('kind'), str):
            raise ValueError('Invalid roll history entry')
        if event.get('at') is not None:
            try:
                datetime.fromisoformat(event['at'])
            except (TypeError, ValueError) as error:
                raise ValueError('Invalid roll history date') from error
        validate_attributes(event.get('attributes'))
        if 'generation' in event:
            validate_generation(event['generation'])


def pinned_packs(character, packs):
    primary = character.get('rules')
    additional = character.get('additional_rule_packs', {})
    if not isinstance(primary, dict) or not isinstance(additional, dict):
        raise ValueError('Rule version pins are missing')
    pins = {**additional}
    if not isinstance(primary.get('id'), str) or not isinstance(primary.get('version'), str):
        raise ValueError('Invalid primary rule version')
    if primary['id'] in pins and pins[primary['id']] != primary['version']:
        raise ValueError('Conflicting rule version pins')
    pins[primary['id']] = primary['version']
    result = []
    for identifier, version in pins.items():
        match = next((pack for pack in packs if pack['id'] == identifier and pack['version'] == version), None)
        if match is None:
            raise ValueError(f'Unsupported rule version: {identifier} {version}')
        result.append(deepcopy(match))
    return result


def export_bundle(character, packs):
    validate_character(character)
    validate_sources(character, packs)
    bundle = {'format': 'characters-unlimited', 'bundle_version': 1,
              'character': deepcopy(character), 'rule_packs': pinned_packs(character, packs)}
    canonical(bundle)
    return bundle


def import_bundle(bundle, packs):
    canonical(bundle)
    if not isinstance(bundle, dict) or bundle.get('format') != 'characters-unlimited' or type(bundle.get('bundle_version')) is not int or bundle['bundle_version'] != 1:
        raise ValueError('Unsupported portable bundle format')
    character = bundle.get('character')
    if not isinstance(character, dict):
        raise ValueError('The character record is missing')
    validate_character(character)
    expected = pinned_packs(character, packs)
    validate_sources(character, expected)
    if character['rules']['id'] != 'rifts-core':
        raise ValueError('The primary rule pack must match the selected game')
    if 'rifts-domestic-skills' not in character.get('additional_rule_packs', {}):
        raise ValueError('The skill projection must retain its rule version pin')
    supplied = bundle.get('rule_packs')
    if not isinstance(supplied, list) or len(supplied) != len(expected):
        raise ValueError('The exact pinned rule definitions must be included')
    for pack in expected:
        if not any(canonical(candidate) == canonical(pack) for candidate in supplied):
            raise ValueError(f"Missing or altered rule definitions: {pack['id']} {pack['version']}")
    return fresh_copy(character)


def validate_sources(character, packs):
    core = next((pack for pack in packs if pack['id'] == 'rifts-core' and pack['version'] == character['rules']['version']), None)
    if core is None:
        raise ValueError('The generated attribute rule source is unavailable')
    records = [character['attributes'], *(event['attributes'] for event in character.get('roll_history', []))]
    selected_class = next(item for item in core['classes'] if item['id'] == character['character_class'])
    for attributes in records:
        for name, value in attributes.items():
            if canonical(value['explanation']['source']) != canonical(core['source']):
                raise ValueError('Generated attribute sources must match the pinned rule definition')
            formula = selected_class.get('attribute_bonuses', {}).get(name)
            modifiers = value.get('modifiers', [])
            if formula is None:
                if modifiers:
                    raise ValueError('Attribute modifiers are unavailable in this pinned rule version')
                continue
            if len(modifiers) != 1:
                raise ValueError('The recorded class attribute contribution is required exactly once')
            modifier = modifiers[0]
            rolls = iter(modifier['rolls'])
            source = selected_class['attribute_bonus_source']
            result = roll_attribute(formula, generation_settings(), lambda sides: next(rolls, 0), source)
            expected = {'id': 'class:' + selected_class['id'], 'value': result['base'], 'rolls': result['rolls'], 'source': source}
            if next(rolls, None) is not None or canonical(modifier) != canonical(expected):
                raise ValueError('Recorded class attribute contribution does not match the pinned rules')


def fresh_copy(character):
    result = deepcopy(character)
    result['copied_from'] = character['id']
    result['id'] = str(uuid4())
    result['revision'] = 0
    result['updated_at'] = datetime.now(timezone.utc).isoformat()
    return result
