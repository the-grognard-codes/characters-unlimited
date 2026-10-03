"""Domestic skill projection and selection guidance from reviewed source pages."""

from collections import Counter
import json
from pathlib import Path
from .required_skills import project_required_skills
from .skill_choices import needs_specialty, selection_policy, choice_guidance, learned_selection_ids, specialty_key
from .proficiency import synergy_contributions, project_proficiency
from .combat import combat_skill_cost
from .physical import project_physical

PACK = json.loads((Path(__file__).parent / 'packs' / 'rifts-domestic-skills.json').read_text(encoding='utf-8'))
DOMESTIC = PACK['skills']
POOLS = PACK['pools']


def validate_selections(selections, pack=PACK):
    if not isinstance(selections, list) or len(selections) > 1000:
        raise ValueError("Provide a skill selection list with at most 1000 entries")
    known = {skill['id']: skill for skill in pack['skills']}
    result = []
    for item in selections:
        if not isinstance(item, dict) or not isinstance(item.get('skill_id'), str) or not isinstance(item.get('pool'), str) or item['skill_id'] not in known or item['pool'] not in pack['pools']:
            raise ValueError("Select an available skill and pool")
        specialty = item.get('specialty', '')
        if not isinstance(specialty, str):
            raise ValueError("Skill specialty must be text")
        result.append({'skill_id': item['skill_id'], 'pool': item['pool'], 'specialty': specialty.strip() if needs_specialty(known[item['skill_id']]) else ''})
    return result


def skill_key(item, pack=PACK):
    definition = next(skill for skill in pack['skills'] if skill['id'] == item['skill_id'])
    specialty = specialty_key(item.get('specialty', '')) if needs_specialty(definition) else ''
    return (item['skill_id'], specialty)


def compare_skill_views(before, after):
    def index(view):
        result = {}
        occurrences: Counter[tuple[str, str, str]] = Counter()
        for group in ('grants', 'selected'):
            for skill in view[group]:
                identity = (group, skill['id'], specialty_key(skill.get('specialty', '')))
                occurrence = occurrences[identity]
                occurrences[identity] += 1
                if skill.get('kind') == 'physical':
                    for effect_group,effects in skill['effects'].items():
                        for name,value in effects.items():
                            result[(*identity,occurrence,'effect:'+effect_group+':'+name)] = {
                                'name':skill['name']+' — '+name.replace('_',' '),
                                'specialty':skill.get('specialty',''), 'percentage':value['value'] if isinstance(value,dict) else value,
                                'unit':''}
                    for activity in skill.get('activities', []):
                        for field,unit in (('speed_attribute','Spd'),('miles','miles'),('kilometers','km')):
                            result[(*identity,occurrence,'activity:'+activity['id']+':'+field)] = {
                                'name':skill['name']+' — '+activity['name'],
                                'specialty':skill.get('specialty',''), 'percentage':activity[field], 'unit':unit}
                    continue
                result[(*identity, occurrence, 'primary')] = skill
                for check in skill.get('additional_checks', []):
                    result[(*identity, occurrence, 'check:' + check['name'])] = {
                        **check, 'name': skill['name'] + ' — ' + check['name'], 'specialty': skill.get('specialty', '')}
        return result
    previous, following = index(before), index(after)
    changes = []
    for key in dict.fromkeys([*following, *previous]):
        skill = following.get(key, previous.get(key))
        changes.append({'name': skill['name'], 'specialty': skill.get('specialty', ''),
                        'before': previous[key]['percentage'] if key in previous else None,
                        'after': following[key]['percentage'] if key in following else None,
                        **({'unit':skill['unit']} if 'unit' in skill else {})})
    return changes


def project_skills(character, pack=PACK):
    domestic, pools = pack['skills'], pack['pools']
    intelligence_rule = pack.get('intelligence')
    iq = character['attributes']['IQ']['value']
    intelligence = 0
    if intelligence_rule:
        intelligence = intelligence_rule['bonuses'].get(str(min(iq, 30)), 0)
        if iq > 30:
            rule = intelligence_rule['beyond_30']
            intelligence += ((iq - 30) // rule['step']) * rule['bonus']
    selections = character.get('skill_selections', [])
    counts = Counter(item['pool'] for item in selections)
    occurrences = Counter(skill_key(item, pack) for item in selections if skill_key(item, pack) != ('instrument', ''))
    occurrences[('cook', '')] += 1
    bonuses = {('cook', ''): 15}
    for item in selections:
        key = skill_key(item, pack)
        definition = next(skill for skill in domestic if skill['id'] == item['skill_id'])
        bonuses[key] = max(bonuses.get(key, 0), selection_policy(definition, item['pool'], pack)['bonus'])
    required = project_required_skills(character, pack, intelligence)
    granted = {item['id'] for item in required['grants']}
    warnings = choice_guidance(selections, pack, required['grants'])
    available = learned_selection_ids(selections, pack)
    available.update(granted)
    selected = []
    physical = project_physical(character,pack)
    physical_entries = {item['id']:item for item in physical['selected']}
    for item in selections:
        definition = next(skill for skill in domestic if skill['id'] == item['skill_id'])
        key = skill_key(item, pack)
        is_domestic = definition.get('category', 'domestic') == 'domestic'
        repetition = definition.get('repetition', {'at': 2, 'bonus': 10} if is_domestic else None)
        repeated = repetition is not None and occurrences[key] >= repetition['at']
        if repetition is not None and occurrences[key] > repetition['at']:
            warnings.append(f"{definition['name']}: more than two selections; the repeated-skill bonus applies once.")
        if repetition is None and occurrences[key] > 1:
            benefit = 'Physical bonus' if definition.get('kind') == 'physical' else 'proficiency bonus'
            warnings.append(f"{definition['name']}: duplicate selections are retained without another {benefit}.")
        if needs_specialty(definition) and not item.get('specialty'):
            warnings.append(f"Choose the specialty for each {definition['name']} selection.")
        policy = selection_policy(definition, item['pool'], pack)
        if definition.get('kind') == 'physical':
            selected.append({**physical_entries[definition['id']], **item, 'quality':'trained'})
            continue
        bonus = bonuses[key] if is_domestic and key != ('instrument', '') else policy['bonus']
        contributions = {'base': definition['base'], 'class': bonus, 'repeated_domestic': 10 if repeated and is_domestic else 0, 'intelligence': intelligence}
        if 'class_ability' in definition:
            contributions['class_ability'] = definition['class_ability']
        if not is_domestic and repetition:
            contributions['repeated_skill'] = repetition['bonus'] if repeated else 0
        contributions.update(synergy_contributions(definition, available))
        quality = 'trained'
        if is_domestic:
            quality = 'professional' if item['pool'] != 'secondary' or repeated else 'amateur'
        elif definition.get('quality_by_pool'):
            quality = 'professional' if repeated else definition['quality_by_pool'].get(item['pool'], 'trained')
        selected.append({**definition, **item, **project_proficiency(definition, contributions), 'quality': quality})
    remaining = {pool: rule['count'] - counts[pool] for pool, rule in pools.items()}
    remaining['related'] -= combat_skill_cost(character, pack)
    for pool, count in remaining.items():
        if count < 0:
            warnings.append(f"{pool.title()}: {-count} selection(s) over the level-one allowance.")
    repeat_cook = 10 if occurrences[('cook', '')] >= 2 else 0
    cook = next(skill for skill in domestic if skill['id'] == 'cook')
    uncapped_cook = cook['base'] + 15 + repeat_cook + intelligence
    gaps = ['Other required choices and skill categories are pending.',
            'Other attribute-related skill effects and acquired-level advancement are pending; percentages omit these modifiers.']
    if not intelligence_rule:
        gaps.append('The pinned rules omit I.Q. bonuses. Preview a rule update to incorporate the reviewed bonus chart.')
    if iq < 9:
        gaps.append('Below-average I.Q. skill entitlements and penalties are pending; displayed counts and percentages do not apply them.')
    sources = ['Vagabond O.C.C. allowances and bonuses: Ultimate Edition pp. 97–98.',
               'Secondary skill restrictions: p. 300; percentage cap: p. 301; repeated domestic skill bonus: p. 307.']
    if any(skill.get('kind') == 'physical' for skill in domestic):
        sources.append('Reviewed Physical bonuses accumulate once per skill: p. 316. Gun-dodge restrictions: p. 361.')
        gaps.append('Other Physical skills are pending. Starting S.D.C. is generated separately.' if 'resources' in pack
                    else 'Physical S.D.C. bonuses are recorded; starting S.D.C. totals and other Physical skills are pending.')
    if intelligence_rule:
        sources.append('I.Q. bonus applies once to every skill: Attribute Bonus Chart p. 281; beyond 30 adds 2% per five points, p. 284.')
    if required['catalog']:
        gaps[0] = ('Begging interpretation, remaining weapon proficiencies, other categories and prerequisites are pending.' if 'combat' in pack
                   else 'Begging interpretation, weapon/hand-to-hand choices, other categories and prerequisites are pending.')
        gaps.append('Conditional repair/horsemanship effects are pending.' if 'selection_rules' in pack else 'Barter literacy/mathematics synergies and conditional repair/horsemanship effects are pending.')
        sources.append('Required choices and Eyeball a Fella bonuses: p. 97; Streetwise adds 10% to I.D. Undercover Agents, p. 321.')
    return {'catalog': domestic, 'physical':physical, 'grants': [{**cook, 'percentage': min(98, uncapped_cook), 'uncapped_percentage': uncapped_cook, 'quality': 'professional',
             'contributions': {'base': cook['base'], 'class': 15, 'repeated_domestic': repeat_cook, 'intelligence': intelligence}}, *required['grants']], 'selected': selected, 'remaining': remaining,
            'required_remaining': required['remaining'], 'required_catalog': required['catalog'],
            'warnings': list(dict.fromkeys([*warnings, *required['warnings']])),
            'sources': sources, 'gaps': gaps,
            'intelligence_source': intelligence_rule['source'] if intelligence_rule else None}
