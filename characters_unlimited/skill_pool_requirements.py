"""Source-bound minimum category choices within an existing skill pool."""

from .option_selectors import select_options
from .selection_groups import validate_group, project_group
from .skill_choices import selection_policy, needs_specialty


def requirement_rules(pack):
    result = []
    for pool, rule in pack['pools'].items():
        requirements = rule.get('requirements', [])
        if not isinstance(requirements, list) or len(requirements) > 100:
            raise ValueError('Skill pool requirements need a bounded list')
        seen = set()
        for requirement in requirements:
            if (not isinstance(requirement, dict) or
                    set(requirement) != {'id', 'name', 'count', 'selector', 'source'} or
                    any(not isinstance(requirement[key], str) or not requirement[key].strip()
                        for key in ('id', 'name')) or requirement['id'] in seen):
                raise ValueError('Skill pool requirements need distinct supported identities')
            source = requirement['source']
            if (not isinstance(source, dict) or any(not isinstance(source.get(key), str) or
                    not source[key].strip() for key in ('book', 'section'))):
                raise ValueError('Skill pool requirements need source evidence')
            options = select_options(requirement['selector'], pack['skills'])
            options = [identifier for identifier in options if selection_policy(
                next(row for row in pack['skills'] if row['id'] == identifier), pool, pack)['allowed']]
            group = {'count': requirement['count'], 'option_ids': options}
            validate_group(group)
            if requirement['count'] > len(options):
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
        result.append({key: value for key, value in
                       {**requirement, **projection, 'remaining': max(0, projection['remaining'])}.items()
                       if key != 'group'})
    return result
