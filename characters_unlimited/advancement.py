"""Recorded first advancement and the experience age of each learned skill."""

from copy import deepcopy
import json


def learning_key(kind, identifier, specialty=''):
    specialty = ' '.join(specialty.split()).casefold()
    return json.dumps([kind, identifier, specialty], ensure_ascii=False)


def learning_age(character, kind, identifier, specialty=''):
    acquired = character.get('learning_levels', {}).get(learning_key(kind, identifier, specialty),
                                                     character['level'])
    return character['level'] - acquired + 1


def remember_learning(character, skill_view, combat_choices):
    levels = deepcopy(character.get('learning_levels', {}))
    for group in ('grants', 'selected'):
        for skill in skill_view[group]:
            levels.setdefault(learning_key('skill', skill['id'], skill.get('specialty', '')), 1 if group == 'grants' else character['level'])
    levels.setdefault(learning_key('hand', combat_choices['hand_to_hand']), character['level'])
    for family in ('ancient', 'modern'):
        for identifier in combat_choices[family]:
            levels.setdefault(learning_key('weapon', identifier), character['level'])
    return levels


def first_advance(character, pack, method, value, levels, die):
    rules = pack.get('advancement')
    if not rules or character['character_class'] != rules['class_id']:
        raise ValueError('Preview a rule update to enable reviewed Vagabond advancement')
    if method not in ('xp', 'level') or type(value) is not int:
        raise ValueError('Choose XP or a whole-number level')
    if method == 'xp':
        low, high = rules['xp_ranges'][1]
        if not 0 <= value <= high:
            raise ValueError('Reviewed XP range is 0-3750; later levels remain pending')
        if value < low:
            if character['level'] != 1:
                raise ValueError('Undo advancement before returning to level-one XP')
            return {'experience': value}
        if character['level'] == 2:
            return {'experience': value, 'advancement': {**character['advancement'], 'xp': value}}
        xp = value
    else:
        if value != 2:
            raise ValueError('Only first advancement to level two is currently reviewed')
        xp = rules['xp_ranges'][1][0]
    if character['level'] != 1:
        raise ValueError('This character has already reached level two')
    if 'resources' not in character:
        raise ValueError('Generate starting resources before advancing')
    prior = character.get('advancement')
    face = prior['hp_roll'] if prior else die(rules['hp_die'])
    if type(face) is not int or not 1 <= face <= rules['hp_die']:
        raise ValueError('Invalid advancement Hit Point die')
    before = {key: deepcopy(value) for key, value in character.items()
              if key not in ('id', 'revision', 'updated_at', 'advancement')}
    record = {'active': True, 'xp': xp, 'hp_roll': face, 'source': deepcopy(rules['source']), 'before': before}
    return {'level': 2, 'experience': xp, 'learning_levels': levels, 'advancement': record}


def validate_advancement(character, pack):
    """Reject incomplete or unsupported progression records before using their data."""
    record = character.get('advancement')
    levels = character.get('learning_levels')
    if record is None:
        if character['level'] != 1 or levels is not None:
            raise ValueError('Advancement and learning records are required')
        return
    rules = pack.get('advancement')
    if not rules or character['game'] != 'rifts' or character['character_class'] != rules['class_id']:
        raise ValueError('Advancement requires its reviewed class and pinned rules')
    if (not isinstance(record, dict) or set(record) != {'active', 'xp', 'hp_roll', 'source', 'before'} or
            type(record['active']) is not bool or character['level'] != (2 if record['active'] else 1) or
            type(record['hp_roll']) is not int or not 1 <= record['hp_roll'] <= rules['hp_die'] or
            type(record['xp']) is not int or not rules['xp_ranges'][1][0] <= record['xp'] <= rules['xp_ranges'][1][1] or
            json.dumps(record['source'], sort_keys=True) != json.dumps(rules['source'], sort_keys=True)):
        raise ValueError('Invalid recorded advancement')
    if record['active'] and character.get('experience') != record['xp']:
        raise ValueError('Experience must match the active advancement')
    before = record['before']
    if (not isinstance(before, dict) or before.get('level') != 1 or
            set(before).intersection({'id', 'revision', 'updated_at', 'advancement'}) or
            before.get('game') != character['game'] or before.get('race') != character['race'] or
            before.get('character_class') != character['character_class'] or 'resources' not in before):
        raise ValueError('Invalid pre-advancement snapshot')
    if not record['active']:
        if levels is not None:
            raise ValueError('Undone advancement must restore pre-level learning records')
        return
    if not isinstance(levels, dict) or len(levels) > 4000:
        raise ValueError('Invalid learned-level records')
    skill_ids = {item['id'] for item in pack['skills']}
    required = pack.get('required', {})
    skill_ids.update(item['id'] for item in required.get('grants', []))
    for name in ('pilot', 'repair'):
        skill_ids.update(item['id'] for item in required.get(name, {}).get('options', []))
    if 'other_languages' in required:
        skill_ids.add(required['other_languages']['skill']['id'])
    allowed = {'skill': skill_ids,
               'hand': {item['id'] for item in pack['combat']['hand_to_hand']},
               'weapon': {item['id'] for family in ('ancient', 'modern') for item in pack['combat'][family]}}
    for key, level in levels.items():
        try:
            identity = json.loads(key)
        except (TypeError, ValueError, RecursionError) as error:
            raise ValueError('Invalid learned-skill identity') from error
        if (not isinstance(identity, list) or len(identity) != 3 or
                any(not isinstance(part, str) for part in identity) or identity[0] not in allowed or
                identity[1] not in allowed[identity[0]] or key != learning_key(*identity) or
                type(level) is not int or not 1 <= level <= character['level']):
            raise ValueError('Invalid learned-skill level')


def project_advancement(character, pack):
    rules = pack.get('advancement')
    record = character.get('advancement')
    supported = bool(rules and character['character_class'] == rules['class_id'])
    return {'supported': supported, 'level': character['level'],
            'xp': character.get('experience', 0), 'active': bool(record and record['active']),
            'hp_roll': record['hp_roll'] if record else None,
            'source': deepcopy(rules['source']) if rules else None,
            'guidance': ('Reviewed Vagabond progression currently covers levels 1 and 2 (0-3750 XP). '
                         'Generate starting resources before gaining a level. Newly added optional skills and training start at the current level; '
                         'required O.C.C. choices belong to level one. Removed and reselected skills retain their learned level. '
                         'Undo restores the complete pre-level save and keeps later edits as a separate recovery character. '
                         'Replay reuses the recorded HP die.' if supported else
                         'Review a rule update to enable first Vagabond advancement.')}
