"""Domestic skill projection and selection guidance from reviewed source pages."""

from collections import Counter
import json
from pathlib import Path
from .required_skills import project_required_skills
from .skill_choices import needs_specialty, selection_policy, choice_guidance, learned_selection_ids, specialty_key
from .proficiency import synergy_contributions, project_proficiency
from .combat import combat_skill_cost
from .physical import project_physical
from .advancement import learning_age
from .selection_groups import validate_group, project_group
from .skill_effects import pack_skill_effects, matching_skill_effects
from .skill_attribute_bonuses import attribute_bonus_rules, attribute_contributions
from .skill_grants import skill_grant_rules, resolve_skill_grants

PACK = json.loads((Path(__file__).parent / 'packs' / 'rifts-domestic-skills.json').read_text(encoding='utf-8'))
DOMESTIC = PACK['skills']
POOLS = PACK['pools']


def optional_pool_groups(pack):
    skill_grant_rules(pack)
    for definition in pack['skills']:
        attribute_bonus_rules(definition)
    identifiers = [definition['id'] for definition in pack['skills']]
    for categories in pack.get('selection_rules', {}).values():
        for rule in categories.values():
            validate_group({'count': 0, 'option_ids': identifiers, 'costs': rule.get('costs', {})})
    groups = {}
    for pool, rule in pack['pools'].items():
        group = {'count': rule['count'], 'option_ids': identifiers, 'counting': 'entries',
                 'costs': {definition['id']: selection_policy(definition, pool, pack)['cost']
                           for definition in pack['skills']}}
        validate_group(group)
        groups[pool] = group
    return groups


def validate_selections(selections, pack=PACK):
    if not isinstance(selections, list) or len(selections) > 1000:
        raise ValueError("Provide a skill selection list with at most 1000 entries")
    optional_pool_groups(pack)
    known = {skill['id']: skill for skill in pack['skills']}
    result = []
    for item in selections:
        if not isinstance(item, dict) or not isinstance(item.get('skill_id'), str) or not isinstance(item.get('pool'), str) or item['skill_id'] not in known or item['pool'] not in pack['pools']:
            raise ValueError("Select an available skill and pool")
        selection_policy(known[item['skill_id']], item['pool'], pack)
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
                if skill.get('kind') == 'physical' and 'effects' in skill:
                    for effect_group,effects in skill['effects'].items():
                        for name,value in effects.items():
                            result[(*identity,occurrence,'effect:'+effect_group+':'+name)] = {
                                'name':skill['name']+' — '+name.replace('_',' '),
                                'specialty':skill.get('specialty',''), 'percentage':value['value'] if isinstance(value,dict) else value,
                                'unit':''}
                    for activity in skill.get('activities', []):
                        fields = (('yards_per_melee','yards/melee'),('meters_per_melee','meters/melee'),('minutes','minutes')) if 'yards_per_melee' in activity else (('speed_attribute','Spd'),('miles','miles'),('kilometers','km'))
                        for field,unit in fields:
                            result[(*identity,occurrence,'activity:'+activity['id']+':'+field)] = {
                                'name':skill['name']+' — '+activity['name'],
                                'specialty':skill.get('specialty',''), 'percentage':activity[field], 'unit':unit}
                    if 'percentage' not in skill:
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
    skill_effects = pack_skill_effects(pack)
    intelligence_rule = pack.get('intelligence')
    iq = character['attributes']['IQ']['value']
    intelligence = 0
    if intelligence_rule:
        intelligence = intelligence_rule['bonuses'].get(str(min(iq, 30)), 0)
        if iq > 30:
            rule = intelligence_rule['beyond_30']
            intelligence += ((iq - 30) // rule['step']) * rule['bonus']
    selections = character.get('skill_selections', [])
    groups = optional_pool_groups(pack)
    counts = {pool: project_group(group, [item['skill_id'] for item in selections
                                        if item['pool'] == pool])['credited']
              for pool, group in groups.items()}
    occurrences = Counter(skill_key(item, pack) for item in selections if skill_key(item, pack) != ('instrument', ''))
    domestic_grants = pack.get('fixed_domestic_grants', [{'id':'cook','bonus':15}])
    bonuses = {}
    for grant in domestic_grants:
        key = (grant['id'], '')
        occurrences[key] += 1
        bonuses[key] = grant['bonus']
    for item in selections:
        key = skill_key(item, pack)
        definition = next(skill for skill in domestic if skill['id'] == item['skill_id'])
        bonuses[key] = max(bonuses.get(key, 0), selection_policy(definition, item['pool'], pack)['bonus'])
    required = project_required_skills(character, pack, intelligence)
    roots = [{'id': grant['id'], 'learned_level': 1} for grant in domestic_grants]
    roots.extend({**row, 'learned_level': 1} for row in required['grants'])
    roots.extend({'id': item['skill_id'], 'specialty': item.get('specialty', '')} for item in selections
                 if not needs_specialty(next(row for row in domestic if row['id'] == item['skill_id'])) or item.get('specialty'))
    derived = resolve_skill_grants(character, pack, roots)
    if derived:
        for identifier, training in derived.items():
            definition = next(row for row in domestic if row['id'] == identifier)
            training['ordinary_bonus'] = max([
                *[row['contributions']['class'] for row in required['grants'] if row['id'] == identifier and not row.get('specialty')],
                *[row['bonus'] for row in domestic_grants if row['id'] == identifier],
                *[selection_policy(definition, item['pool'], pack)['bonus'] for item in selections if item['skill_id'] == identifier],
                0])
        required = project_required_skills(character, pack, intelligence, skill_grants=derived)
    granted = {item['id'] for item in required['grants']}
    physical = project_physical(character,pack)
    automatic_physical = [{**item, 'quality':'trained'} for item in physical['selected'] if item.get('grant')]
    warnings = choice_guidance(selections, pack, [*required['grants'], *automatic_physical,
        *[{'id': identifier, 'grant_origins': row['origins']} for identifier, row in derived.items()]])
    available = learned_selection_ids(selections, pack)
    available.update(granted)
    available.update(derived)
    selected = []
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
        if definition.get('kind') == 'physical' and 'base' not in definition:
            selected.append({**physical_entries[definition['id']], **item, 'quality':'trained', 'selection_cost':policy['cost'], 'selection_cost_source':pack['source']})
            continue
        bonus = bonuses[key] if is_domestic and key != ('instrument', '') else policy['bonus']
        contributions = {'base': definition['base'], 'class': bonus, 'repeated_domestic': 10 if repeated and is_domestic else 0, 'intelligence': intelligence}
        training = derived.get(definition['id']) if not needs_specialty(definition) else None
        if training:
            bonus = max(bonus, training['ordinary_bonus'])
            contributions['class'] = bonus
            contributions['Skill grant training'] = max(0, training['bonus'] - bonus)
        if character['level'] > 1:
            age = learning_age(character, 'skill', definition['id'], item.get('specialty', ''))
            if training:
                age = character['level'] - training['learned_level'] + 1
            contributions['advancement'] = (age - 1) * definition['per_level']
        if 'class_ability' in definition and character['character_class'] == pack.get('default_class', 'vagabond'):
            contributions['class_ability'] = definition['class_ability']
        if not is_domestic and repetition:
            contributions['repeated_skill'] = repetition['bonus'] if repeated else 0
        contributions.update(synergy_contributions(definition, available))
        contributions.update(attribute_contributions(definition, character['attributes']))
        quality = 'trained'
        if is_domestic:
            quality = 'professional' if item['pool'] != 'secondary' or repeated else 'amateur'
        elif definition.get('quality_by_pool'):
            quality = 'professional' if repeated else definition['quality_by_pool'].get(item['pool'], 'trained')
        effects = physical_entries.get(definition['id'], {}) if definition.get('kind') == 'physical' else {}
        selected.append({**definition, **effects, **item, **({'grant_origins': training['origins'], 'learned_level': training['learned_level']} if training else {}), **project_proficiency(definition, contributions, effect_contributions=matching_skill_effects(definition['id'], skill_effects)), 'quality': quality,
                         'selection_cost':policy['cost'], 'selection_cost_source':pack['source']})
    remaining = {pool: rule['count'] - counts[pool] for pool, rule in pools.items()}
    for pool in ('related', 'secondary'):
        remaining[pool] += sum(level <= character['level'] for level in pack.get('higher_advancement', {}).get(pool + '_levels', []))
    remaining['related'] -= combat_skill_cost(character, pack)
    for pool, count in remaining.items():
        if count < 0:
            warnings.append(f"{pool.title()}: {-count} selection(s) over the current level allowance.")
    fixed_grants = []
    for grant in domestic_grants:
        definition = next(skill for skill in domestic if skill['id'] == grant['id'])
        repeated_bonus = 10 if occurrences[(grant['id'], '')] >= 2 else 0
        gain = (learning_age(character, 'skill', grant['id']) - 1) * definition['per_level']
        contributions = {'base':definition['base'], 'class':grant['bonus'],
                         'repeated_domestic':repeated_bonus, 'intelligence':intelligence}
        training = derived.get(grant['id'])
        if training:
            contributions['class'] = max(grant['bonus'], training['ordinary_bonus'])
            contributions['Skill grant training'] = max(0, training['bonus'] - contributions['class'])
        if character['level'] > 1:
            contributions['advancement'] = gain
        contributions.update(attribute_contributions(definition, character['attributes']))
        fixed_grants.append({**definition, **({'grant_origins': training['origins']} if training else {}), **project_proficiency(definition, contributions, effect_contributions=matching_skill_effects(definition['id'], skill_effects)), 'quality':'professional'})
    derived_grants = []
    for identifier, training in derived.items():
        if identifier in granted or any(grant['id'] == identifier for grant in domestic_grants):
            continue
        definition = next(row for row in domestic if row['id'] == identifier)
        optional_bonus = training['ordinary_bonus']
        contributions = {'base': definition['base'], 'class': optional_bonus,
                         'Skill grant training': max(0, training['bonus'] - optional_bonus), 'intelligence': intelligence}
        if character['level'] > 1:
            contributions['advancement'] = (character['level'] - training['learned_level']) * definition['per_level']
        contributions.update(synergy_contributions(definition, available))
        contributions.update(attribute_contributions(definition, character['attributes']))
        parents = ', '.join(dict.fromkeys(next(row['name'] for row in domestic if row['id'] == origin['parent_id'])
                                         for origin in training['origins']))
        derived_grants.append({**definition, 'description': definition.get('description', '') + f' Automatically granted by {parents}.',
            'grant_origins': training['origins'], 'learned_level': training['learned_level'],
            **project_proficiency(definition, contributions, effect_contributions=matching_skill_effects(identifier, skill_effects)), 'quality': 'trained'})
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
    if 'advancement' in pack:
        gaps[1] = ('Other attribute-related skill effects and progression for other character paths remain pending.'
                   if 'higher_advancement' in pack else 'Other attribute-related skill effects and progression after level two remain pending.')
        sources.append('Recorded learned levels determine proficiency growth; new skills begin at base: pp. 98, 300. First advancement and XP table: pp. 287, 295.')
    if pack.get('path_guidance'):
        gaps = list(pack['path_guidance'])
        sources = [f"{pack['source']['book']}, class rules printed pp. " + ', '.join(map(str,pack['source']['pages'])),
                   'General skill growth, secondary restrictions and percentage cap: pp. 300–301.',
                   'Physical bonuses apply once per skill: pp. 316–317.',
                   'I.Q. bonuses: pp. 281, 284. HP growth and class XP: pp. 287, 295.']
    return {'catalog': domestic, 'physical':physical, 'grants': [*fixed_grants, *required['grants'], *automatic_physical, *derived_grants], 'selected': selected, 'remaining': remaining,
            'pool_catalog':pools,
            'required_remaining': required['remaining'], 'required_catalog': required['catalog'],
            'warnings': list(dict.fromkeys([*warnings, *required['warnings']])),
            'sources': sources, 'gaps': gaps,
            'intelligence_source': intelligence_rule['source'] if intelligence_rule else None}
