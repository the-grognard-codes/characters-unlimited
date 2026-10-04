"""Recorded first advancement and the experience age of each learned skill."""

from copy import deepcopy
from .required_definitions import required_catalog
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
    if 'higher_advancement' in pack and (character['level'] > 2 or
            (method == 'level' and value > 2) or (method == 'xp' and value > rules['xp_ranges'][1][1])):
        return advance_levels(character, pack, method, value, levels, die)
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
              if key not in ('id', 'revision', 'updated_at', 'advancement', 'later_advancements')}
    record = {'active': True, 'xp': xp, 'hp_roll': face, 'source': deepcopy(rules['source']), 'before': before}
    return {'level': 2, 'experience': xp, 'learning_levels': levels, 'advancement': record}


def advance_levels(character, pack, method, value, levels, die):
    """Build each intermediate snapshot without nesting the later-level cache."""
    rules = pack['higher_advancement']
    if method == 'xp':
        target = next((level for level, (low, high) in enumerate(rules['xp_ranges'], 1)
                       if low <= value <= high), None)
        if target is None:
            raise ValueError('XP is outside the reviewed progression range')
        xp = value
    else:
        target = value
        if not 1 <= target <= rules['max_level']:
            raise ValueError('Level is outside the reviewed progression range')
        xp = rules['xp_ranges'][target - 1][0]
    if target < character['level']:
        raise ValueError('Undo advancement before selecting a lower level')
    if target == character['level']:
        return {'experience': xp}
    candidate = deepcopy(character)
    candidate['learning_levels'] = levels
    if candidate['level'] == 1:
        candidate.pop('learning_levels', None)
        candidate.update(first_advance(candidate, pack, 'level', 2, levels, die))
    events = deepcopy(candidate.get('later_advancements', []))
    for level in range(candidate['level'] + 1, target + 1):
        cached = next((event for event in events if event['level'] == level), None)
        face = cached['hp_roll'] if cached else die(rules['hp_die'])
        if type(face) is not int or not 1 <= face <= rules['hp_die']:
            raise ValueError('Invalid advancement Hit Point die')
        before = {key: deepcopy(item) for key, item in candidate.items()
                  if key not in ('id', 'revision', 'updated_at', 'later_advancements')}
        event = {'level': level, 'hp_roll': face, 'source': deepcopy(rules['source']), 'before': before}
        events = sorted([event, *(item for item in events if item['level'] != level)], key=lambda item: item['level'])
        candidate.update(level=level, experience=rules['xp_ranges'][level - 1][0],
                         later_advancements=events)
    candidate['experience'] = xp
    return {key: candidate[key] for key in ('level', 'experience', 'advancement', 'learning_levels', 'later_advancements')}


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
            type(record['active']) is not bool or (character['level'] < 2 if record['active'] else character['level'] != 1) or
            type(record['hp_roll']) is not int or not 1 <= record['hp_roll'] <= rules['hp_die'] or
            type(record['xp']) is not int or not rules['xp_ranges'][1][0] <= record['xp'] <= rules['xp_ranges'][1][1] or
            json.dumps(record['source'], sort_keys=True) != json.dumps(rules['source'], sort_keys=True)):
        raise ValueError('Invalid recorded advancement')
    if record['active'] and character['level'] == 2 and character.get('experience') != record['xp']:
        raise ValueError('Experience must match the active advancement')
    before = record['before']
    if (not isinstance(before, dict) or before.get('level') != 1 or
            set(before).intersection({'id', 'revision', 'updated_at', 'advancement', 'later_advancements'}) or
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
    required = required_catalog(pack) or {'grants':[], 'groups':[]}
    skill_ids.update(item['id'] for item in required['grants'])
    for group in required['groups']:
        skill_ids.update(item['id'] for item in group.get('options', []))
        if 'skill' in group:
            skill_ids.add(group['skill']['id'])
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


def validate_later_advancements(character, pack, *, history_frame=False):
    events = character.get('later_advancements', [])
    rules = pack.get('higher_advancement')
    if not isinstance(events, list) or len(events) > 13:
        raise ValueError('Invalid later advancement history')
    if events and 'advancement' not in character:
        raise ValueError('Later gains require their initial advancement record')
    if (events or character['level'] > 2) and not rules:
        raise ValueError('Later advancement requires its reviewed rules')
    if rules:
        if not 1 <= character['level'] <= rules['max_level']:
            raise ValueError('Level is outside the reviewed progression range')
        low, high = rules['xp_ranges'][character['level'] - 1]
    else:
        low, high = (0, 1875) if character['level'] == 1 else (1876, 3750)
    if character['level'] > 1 and type(character.get('experience')) is not int:
        raise ValueError('Advanced characters require their recorded experience')
    if 'experience' in character and not low <= character['experience'] <= high:
        raise ValueError('Experience must match a reviewed level range')
    seen = []
    for event in events:
        if (not isinstance(event, dict) or set(event) != {'level', 'hp_roll', 'source', 'before'} or
                type(event['level']) is not int or not 3 <= event['level'] <= rules['max_level'] or
                type(event['hp_roll']) is not int or not 1 <= event['hp_roll'] <= rules['hp_die']):
            raise ValueError('Invalid later advancement record')
        before = event['before']
        if (not isinstance(before, dict) or before.get('level') != event['level'] - 1 or
                set(before).intersection({'id', 'revision', 'updated_at', 'later_advancements'}) or
                any(before.get(key) != character[key] for key in ('game', 'race', 'character_class')) or
                'resources' not in before or 'advancement' not in before):
            raise ValueError('Invalid later pre-advancement snapshot')
        seen.append(event['level'])
    if seen != sorted(set(seen)):
        raise ValueError('Later advancement levels must be unique and ordered')
    if not history_frame and not set(range(3, character['level'] + 1)).issubset(seen):
        raise ValueError('Each attained level requires its recorded advancement')


def project_advancement(character, pack):
    rules = pack.get('advancement')
    record = character.get('advancement')
    supported = bool(rules and character['character_class'] == rules['class_id'])
    progression = pack.get('higher_advancement', rules) or {}
    maximum = progression.get('max_level', 2)
    maximum_xp = progression.get('xp_ranges', [[0,1875],[1876,3750]])[-1][1]
    dice = ([{'level':2,'face':record['hp_roll'],'active':record['active']}] if record else [])
    dice.extend({'level':event['level'],'face':event['hp_roll'],'active':event['level'] <= character['level']}
                for event in character.get('later_advancements', []))
    return {'supported': supported, 'level': character['level'],
            'max_level':maximum,'max_xp':maximum_xp,'dice':dice,
            'xp': character.get('experience', 0), 'active': bool(record and record['active']),
            'hp_roll': record['hp_roll'] if record else None,
            'source': deepcopy(rules['source']) if rules else None,
            'guidance': (f'Reviewed Vagabond progression covers levels 1–{maximum} (0–{maximum_xp} XP). '
                         'Generate starting resources before gaining a level. Newly added optional skills and training start at the current level; '
                         'required O.C.C. choices belong to level one. Removed and reselected skills retain their learned level. '
                         'Undo restores the complete pre-level save and keeps later edits as a separate recovery character. '
                         'Replay reuses the recorded HP die.' if supported else
                         'Review a rule update to enable first Vagabond advancement.')}
