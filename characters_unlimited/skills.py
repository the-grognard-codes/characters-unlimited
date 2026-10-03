"""Domestic skill projection and selection guidance from reviewed source pages."""

from collections import Counter
import json
from pathlib import Path

PACK = json.loads((Path(__file__).parent / 'packs' / 'rifts-domestic-skills.json').read_text(encoding='utf-8'))
DOMESTIC = PACK['skills']
POOLS = PACK['pools']


def validate_selections(selections, pack=PACK):
    if not isinstance(selections, list) or len(selections) > 1000:
        raise ValueError("Provide a skill selection list with at most 1000 entries")
    known = {skill['id'] for skill in pack['skills']}
    result = []
    for item in selections:
        if not isinstance(item, dict) or not isinstance(item.get('skill_id'), str) or not isinstance(item.get('pool'), str) or item['skill_id'] not in known or item['pool'] not in pack['pools']:
            raise ValueError("Select an available skill and pool")
        specialty = item.get('specialty', '')
        if not isinstance(specialty, str):
            raise ValueError("Skill specialty must be text")
        result.append({'skill_id': item['skill_id'], 'pool': item['pool'], 'specialty': specialty.strip() if item['skill_id'] == 'instrument' else ''})
    return result


def skill_key(item):
    specialty = ' '.join(item.get('specialty', '').split()).casefold() if item['skill_id'] == 'instrument' else ''
    return (item['skill_id'], specialty)


def project_skills(character, pack=PACK):
    domestic, pools = pack['skills'], pack['pools']
    selections = character.get('skill_selections', [])
    counts = Counter(item['pool'] for item in selections)
    occurrences = Counter(skill_key(item) for item in selections if skill_key(item) != ('instrument', ''))
    occurrences[('cook', '')] += 1
    bonuses = {('cook', ''): 15}
    for item in selections:
        key = skill_key(item)
        bonuses[key] = max(bonuses.get(key, 0), pools[item['pool']]['bonus'])
    warnings = []
    selected = []
    for item in selections:
        definition = next(skill for skill in domestic if skill['id'] == item['skill_id'])
        key = skill_key(item)
        repeated = occurrences[key] >= 2
        if occurrences[key] > 2:
            warnings.append(f"{definition['name']}: more than two selections; the repeated-skill bonus applies once.")
        if item['skill_id'] == 'instrument' and not item.get('specialty'):
            warnings.append("Choose the instrument for each Play Musical Instrument selection.")
        bonus = pools[item['pool']]['bonus'] if key == ('instrument', '') else bonuses[key]
        selected.append({**definition, **item, 'percentage': min(98, definition['base'] + bonus + (10 if repeated else 0)),
                         'quality': 'professional' if item['pool'] != 'secondary' or repeated else 'amateur',
                         'contributions': {'base': definition['base'], 'class': bonus, 'repeated_domestic': 10 if repeated else 0}})
    remaining = {pool: rule['count'] - counts[pool] for pool, rule in pools.items()}
    for pool, count in remaining.items():
        if count < 0:
            warnings.append(f"{pool.title()}: {-count} selection(s) over the level-one allowance.")
    repeat_cook = 10 if occurrences[('cook', '')] >= 2 else 0
    cook = next(skill for skill in domestic if skill['id'] == 'cook')
    return {'catalog': domestic, 'grants': [{**cook, 'percentage': min(98, cook['base'] + 15 + repeat_cook), 'quality': 'professional',
             'contributions': {'base': cook['base'], 'class': 15, 'repeated_domestic': repeat_cook}}], 'selected': selected, 'remaining': remaining,
            'warnings': list(dict.fromkeys(warnings)),
            'sources': ['Vagabond O.C.C. allowances and bonuses: Ultimate Edition pp. 97–98.',
                        'Secondary skill restrictions: p. 300; percentage cap: p. 301; repeated domestic skill bonus: p. 307.'],
            'gaps': ['Other required choices and skill categories are pending.',
                     'I.Q. modifiers and acquired-level advancement are pending; percentages shown omit these modifiers.']}
