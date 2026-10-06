"""Source-bound minimum category choices within an existing skill pool."""

from .option_selectors import select_options
from .selection_groups import validate_group, project_group
from .skill_choices import selection_policy, needs_specialty, specialty_key


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
                    set(requirement) - {'id', 'name', 'count', 'selector', 'source', 'counting'} or
                    any(not isinstance(requirement[key], str) or not requirement[key].strip()
                        for key in ('id', 'name')) or requirement['id'] in seen):
                raise ValueError('Skill pool requirements need distinct supported identities')
            counting = requirement.get('counting', 'distinct')
            if counting not in ('distinct', 'distinct-specialties'):
                raise ValueError('Skill pool requirements need supported choice counting')
            source = requirement['source']
            if (not isinstance(source, dict) or any(not isinstance(source.get(key), str) or
                    not source[key].strip() for key in ('book', 'section'))):
                raise ValueError('Skill pool requirements need source evidence')
            options = select_options(requirement['selector'], pack['skills'])
            options = [identifier for identifier in options if selection_policy(
                next(row for row in pack['skills'] if row['id'] == identifier), pool, pack)['allowed']]
            group = {'count': requirement['count'], 'option_ids': options}
            validate_group(group)
            specialty_options = any(row['id'] in options and needs_specialty(row) for row in pack['skills'])
            if requirement['count'] > len(options) and not (counting == 'distinct-specialties' and specialty_options):
                raise ValueError('Skill pool requirement exceeds its eligible distinct options')
            result.append({**requirement, 'pool': pool, 'group': group})
            seen.add(requirement['id'])
    return result


def project_requirements(character, pack):
    known = {row['id']: row for row in pack['skills']}
    result = []
    for requirement in requirement_rules(pack):
        selections = [item['skill_id'] for item in character.get('skill_selections', [])
                      if item['pool'] == requirement['pool'] and
                      (not needs_specialty(known[item['skill_id']]) or item.get('specialty'))]
        projection = project_group(requirement['group'], selections)
        if requirement.get('counting') == 'distinct-specialties':
            eligible = set(projection['eligible'])
            qualified = [(item['skill_id'], specialty_key(item.get('specialty', ''))
                          if needs_specialty(known[item['skill_id']]) else '')
                         for item in character.get('skill_selections', [])
                         if item['pool'] == requirement['pool'] and item['skill_id'] in eligible and
                         (not needs_specialty(known[item['skill_id']]) or item.get('specialty'))]
            distinct = len(set(qualified))
            projection.update(credited=distinct, remaining=requirement['count']-distinct,
                              duplicates=distinct != len(qualified))
        result.append({key: value for key, value in
                       {**requirement, **projection, 'remaining': max(0, projection['remaining'])}.items()
                       if key != 'group'})
    return result
