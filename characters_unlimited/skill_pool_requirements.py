"""Source-bound minimum category choices within an existing skill pool."""

from .option_selectors import select_options
from .selection_groups import validate_group, project_group
from .skill_choices import selection_policy, needs_specialty, specialty_key
from .advancement import learning_key
from .skill_pool_learning import pool_learning_default


def _paid_training_styles(requirement, pool, pack):
    """Compile source-owned paid styles without conflating weapon slot costs."""
    if 'paid_hand_to_hand' not in requirement:
        return []
    identities = requirement['paid_hand_to_hand']
    if (pool != 'related' or requirement.get('counting', 'distinct') != 'distinct' or
            not isinstance(identities, list) or not 1 <= len(identities) <= 1000 or
            any(not isinstance(value, str) or not value.strip() or len(value) > 1000 for value in identities) or
            len(set(identities)) != len(identities)):
        raise ValueError('Paid training needs distinct bounded styles in a Related distinct minimum')
    combat = pack.get('combat')
    styles = combat.get('hand_to_hand') if isinstance(combat, dict) else None
    if (not isinstance(styles, list) or not 1 <= len(styles) <= 1000 or
            any(not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id']
                for row in styles) or len({row['id'] for row in styles}) != len(styles)):
        raise ValueError('Paid training requires a distinct pinned hand-to-hand catalog')
    known = {row['id']: row for row in styles}
    if (set(identities) - set(known) or any(type(known[identity].get('cost')) is not int or
            not 1 <= known[identity]['cost'] <= 1000 or
            not isinstance(known[identity].get('name'), str) or not known[identity]['name'].strip()
            for identity in identities)):
        raise ValueError('Paid training must reference named styles with a positive Related cost')
    return identities


def requirement_rules(pack):
    result = []
    for pool, rule in pack['pools'].items():
        requirements = rule.get('requirements', [])
        if not isinstance(requirements, list) or len(requirements) > 100:
            raise ValueError('Skill pool requirements need a bounded list')
        seen = set()
        for requirement in requirements:
            if (not isinstance(requirement, dict) or
                    not {'id', 'name', 'count', 'selector', 'source'} <= set(requirement) or
                    set(requirement) - {'id', 'name', 'count', 'selector', 'source', 'counting',
                                       'before_level', 'excluded_specialties', 'paid_hand_to_hand'} or
                    any(not isinstance(requirement[key], str) or not requirement[key].strip()
                        for key in ('id', 'name')) or requirement['id'] in seen):
                raise ValueError('Skill pool requirements need distinct supported identities')
            counting = requirement.get('counting', 'distinct')
            if counting not in ('distinct', 'distinct-specialties'):
                raise ValueError('Skill pool requirements need supported choice counting')
            if 'before_level' in requirement and (type(requirement['before_level']) is not int or
                    not 2 <= requirement['before_level'] <= 1000):
                raise ValueError('Initial skill requirements need an exact bounded acquisition cutoff')
            exclusions = requirement.get('excluded_specialties', [])
            if (not isinstance(exclusions,list) or len(exclusions)>1000 or
                    any(not isinstance(value,str) or not specialty_key(value) or len(value)>1000 for value in exclusions) or
                    len({specialty_key(value) for value in exclusions}) != len(exclusions) or
                    ('excluded_specialties' in requirement and counting != 'distinct-specialties')):
                raise ValueError('Specialty exclusions need distinct bounded names and specialty counting')
            source = requirement['source']
            if (not isinstance(source, dict) or any(not isinstance(source.get(key), str) or
                    not source[key].strip() for key in ('book', 'section'))):
                raise ValueError('Skill pool requirements need source evidence')
            options = select_options(requirement['selector'], pack['skills'])
            options = [identifier for identifier in options if selection_policy(
                next(row for row in pack['skills'] if row['id'] == identifier), pool, pack)['allowed']]
            group = {'count': requirement['count'], 'option_ids': options}
            validate_group(group)
            paid_styles = _paid_training_styles(requirement, pool, pack)
            specialty_options = any(row['id'] in options and needs_specialty(row) for row in pack['skills'])
            capacity = len(options) + bool(paid_styles)
            if requirement['count'] > capacity and not (counting == 'distinct-specialties' and specialty_options):
                raise ValueError('Skill pool requirement exceeds its eligible distinct options')
            result.append({**requirement, 'pool': pool, 'group': group})
            seen.add(requirement['id'])
    return result


def project_requirements(character, pack):
    known = {row['id']: row for row in pack['skills']}
    result = []
    for requirement in requirement_rules(pack):
        exclusions = {specialty_key(value) for value in requirement.get('excluded_specialties', [])}
        qualified_items = []
        for item in character.get('skill_selections', []):
            specialty = item.get('specialty','')
            if (item['pool'] != requirement['pool'] or
                    (needs_specialty(known[item['skill_id']]) and not specialty) or
                    specialty_key(specialty) in exclusions):
                continue
            learned = character.get('learning_levels', {}).get(
                learning_key('skill',item['skill_id'],specialty),
                pool_learning_default(pack,item['pool'],character['level']))
            if 'before_level' in requirement and learned >= requirement['before_level']:
                continue
            qualified_items.append(item)
        selections = [item['skill_id'] for item in qualified_items]
        projection = project_group(requirement['group'], selections)
        if requirement.get('counting') == 'distinct-specialties':
            eligible = set(projection['eligible'])
            qualified = [(item['skill_id'], specialty_key(item.get('specialty', ''))
                          if needs_specialty(known[item['skill_id']]) else '')
                         for item in qualified_items if item['skill_id'] in eligible]
            distinct = len(set(qualified))
            projection.update(credited=distinct, remaining=requirement['count']-distinct,
                              duplicates=distinct != len(qualified))
        if 'paid_hand_to_hand' in requirement:
            credits = []
            selected = character.get('combat_choices', {}).get(
                'hand_to_hand', pack['combat']['default_hand_to_hand'])
            if selected in requirement['paid_hand_to_hand']:
                learned = character.get('learning_levels', {}).get(
                    learning_key('hand', selected), character['level'])
                if 'before_level' not in requirement or learned < requirement['before_level']:
                    style = next(row for row in pack['combat']['hand_to_hand'] if row['id'] == selected)
                    credits.append({'kind': 'hand_to_hand', 'id': selected, 'name': style['name'],
                                    'learned_level': learned, 'source': requirement['source']})
            credited = projection['credited'] + len(credits)
            projection.update(training_credits=credits, credited=credited,
                              remaining=requirement['count']-credited)
        result.append({key: value for key, value in
                       {**requirement, **projection, 'remaining': max(0, projection['remaining'])}.items()
                       if key != 'group'})
    return result
