"""Level-owned fixed training and age-qualified weapon-only awards."""

from copy import deepcopy
from typing import Any
from .advancement import learning_key


def weapon_schedule(rules):
    schedule = rules.get('proficiency_schedule')
    if schedule is None and 'proficiency_schedule' not in rules:
        return None
    if (not isinstance(schedule, dict) or set(schedule) != {'fixed', 'awards', 'initial_paid_minimum'} or
            'proficiency_counts' not in rules):
        raise ValueError('Scheduled weapon training needs explicit family allowances')
    known = {family: {row['id'] for row in rules[family]} for family in ('ancient', 'modern')}
    def source(row):
        evidence = row.get('source')
        if (not isinstance(evidence, dict) or any(not isinstance(evidence.get(key), str) or
                not evidence[key].strip() for key in ('book', 'section'))):
            raise ValueError('Scheduled weapon training needs source evidence')
    seen = set()
    for field in ('fixed', 'awards'):
        rows = schedule[field]
        if not isinstance(rows, list) or len(rows) > 100:
            raise ValueError('Scheduled weapon training needs bounded declarations')
        for row in rows:
            fields = {'level', 'family', 'id', 'source'} if field == 'fixed' else {'level', 'id', 'name', 'count', 'source'}
            if (not isinstance(row, dict) or set(row) != fields or
                    type(row['level']) is not int or not 2 <= row['level'] <= 1000 or
                    not isinstance(row['id'], str) or not row['id'].strip()):
                raise ValueError('Scheduled weapon training needs exact identities and levels')
            source(row)
            if field == 'fixed':
                if (not isinstance(row['family'], str) or row['family'] not in known or row['id'] not in known[row['family']] or
                        row['id'] in rules.get('fixed_proficiencies', {}).get(row['family'], [])):
                    raise ValueError('Scheduled fixed training needs known nonfixed identities')
                identity = (field, row['family'], row['id'])
            else:
                if (not isinstance(row['name'], str) or not row['name'].strip() or
                        type(row['count']) is not int or not 1 <= row['count'] <= 1000):
                    raise ValueError('Weapon awards need names and bounded positive counts')
                identity = (field, '', row['id'])
            if identity in seen:
                raise ValueError('Scheduled weapon training must be distinct')
            seen.add(identity)
    minimum = schedule['initial_paid_minimum']
    if (not isinstance(minimum, dict) or set(minimum) != {'count', 'before_level', 'source'} or
            type(minimum['count']) is not int or not 0 <= minimum['count'] <= 1000 or
            type(minimum['before_level']) is not int or not 2 <= minimum['before_level'] <= 1000):
        raise ValueError('Initial paid weapon requirements need bounded counts and levels')
    source(minimum)
    cost = rules.get('additional_proficiency_cost', 0)
    if minimum['count'] and (type(cost) is not int or not 1 <= cost <= 1000):
        raise ValueError('A paid weapon minimum requires a positive additional training cost')
    available = 0
    for family in ('ancient', 'modern'):
        options = known[family] - set(rules.get('fixed_proficiencies', {}).get(family, []))
        allowed = rules['required_proficiencies'][family]
        eligible = options if allowed == 'any' else options.intersection(allowed)
        available += len(options) - min(rules['proficiency_counts'][family], len(eligible))
    if minimum['count'] > available:
        raise ValueError('Initial paid weapon minimum exceeds distinct available extra training')
    return schedule


def scheduled_training(character, choices, rules, fixed, counts):
    """Allocate older family training first; later awards never free earlier paid WPs."""
    schedule = weapon_schedule(rules)
    if schedule is None:
        return None
    choices = {family: choices.get(family, []) for family in ('ancient', 'modern')}
    level = character['level']
    levels = character.get('learning_levels', {})
    def acquired(identifier):
        return levels.get(learning_key('weapon', identifier), level)
    grants = deepcopy(fixed)
    grant_levels = {identifier: 1 for family in ('ancient', 'modern') for identifier in grants[family]}
    grant_sources = {identifier: deepcopy(grants['source']) for identifier in grant_levels}
    for row in schedule['fixed']:
        if row['level'] <= level:
            grants[row['family']].append(row['id'])
            manual = acquired(row['id']) if row['id'] in choices[row['family']] else row['level']
            grant_levels[row['id']] = min(manual, row['level'])
            grant_sources[row['id']] = deepcopy(row['source'])
            grants.setdefault('source', deepcopy(row['source']))
    extras: list[dict[str, Any]] = []
    remaining = {}
    for family in ('ancient', 'modern'):
        selected = set(choices[family]) - set(grants[family])
        allowed = rules['required_proficiencies'][family]
        eligible = selected if allowed == 'any' else selected.intersection(allowed)
        free = set(sorted(eligible, key=lambda key: (acquired(key), key))[:counts[family]])
        remaining[family] = max(0, counts[family] - len(free))
        extras.extend({'family': family, 'id': key, 'learned_level': acquired(key)} for key in sorted(selected - free))
    awards = [{**deepcopy(row), 'credited': 0, 'remaining': row['count']}
              for row in schedule['awards'] if row['level'] <= level]
    paid = []
    for row in sorted(extras, key=lambda item: (item['learned_level'], item['family'], item['id'])):
        award = next((award for award in sorted(awards, key=lambda item: item['level'], reverse=True)
                      if award['remaining'] and award['level'] <= row['learned_level']), None)
        if award is None:
            paid.append(row)
        else:
            award['remaining'] -= 1
            award['credited'] += 1
    minimum = schedule['initial_paid_minimum']
    initial = sum(row['learned_level'] < minimum['before_level'] for row in paid)
    return {'fixed': grants, 'grant_levels': grant_levels, 'grant_sources': grant_sources,
            'remaining': remaining, 'awards': awards, 'paid': paid,
            'initial_paid_requirement': {**deepcopy(minimum), 'credited': initial,
                                       'remaining': max(0, minimum['count'] - initial)}}


def validate_weapon_learning_history(character, before, rules):
    if weapon_schedule(rules) is None or before['level'] >= character['level']:
        return
    current = character.get('learning_levels', {})
    for key, age in before.get('learning_levels', {}).items():
        # Canonical key validation is performed by the existing advancement validator.
        if key.startswith('["weapon",') and current.get(key) != age:
            raise ValueError('Scheduled weapon training must retain historical acquisition levels')
