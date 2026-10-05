"""Resolve source-bound training grants from acquired percentile skills."""

from .advancement import learning_key
from .recorded_formulas import MAX_INTEGER
from .skill_choices import needs_specialty
from .option_selectors import select_options
from typing import Any


def skill_grant_rules(pack):
    catalog = pack['skills']
    select_options({'any_of': [{'ids': []}]}, catalog)
    known = {row['id']: row for row in catalog}
    rules = {}
    for definition in catalog:
        grants = definition.get('granted_skills', [])
        if not isinstance(grants, list) or len(grants) > 1000:
            raise ValueError('Skill-derived grants require a bounded list')
        seen = set()
        for grant in grants:
            if (not isinstance(grant, dict) or set(grant) != {'skill_id', 'bonus', 'source'} or
                    not isinstance(grant['skill_id'], str) or grant['skill_id'] not in known or
                    grant['skill_id'] in seen or type(grant['bonus']) is not int or
                    not 0 <= grant['bonus'] <= MAX_INTEGER):
                raise ValueError('Skill-derived grants need distinct known targets and exact training bonuses')
            target = known[grant['skill_id']]
            if (needs_specialty(target) or target.get('kind') == 'physical' or
                    any(type(target.get(field)) is not int or not 0 <= target[field] <= MAX_INTEGER
                        for field in ('base', 'per_level'))):
                raise ValueError('Skill-derived grants support ordinary percentile targets without specialties')
            source = grant['source']
            if (not isinstance(source, dict) or any(not isinstance(source.get(field), str) or
                    not source[field].strip() for field in ('book', 'section'))):
                raise ValueError('Skill-derived grants need source evidence')
            seen.add(grant['skill_id'])
        if grants:
            if (definition.get('kind') == 'physical' or
                    any(type(definition.get(field)) is not int or not 0 <= definition[field] <= MAX_INTEGER
                        for field in ('base', 'per_level'))):
                raise ValueError('Skill-derived grants need an ordinary percentile parent')
            rules[definition['id']] = grants
    # Iterative topological validation also handles long valid chains without recursion.
    incoming = {identifier: 0 for identifier in known}
    for grants in rules.values():
        for grant in grants:
            incoming[grant['skill_id']] += 1
    queue = [identifier for identifier, count in incoming.items() if count == 0]
    for identifier in queue:
        for grant in rules.get(identifier, []):
            incoming[grant['skill_id']] -= 1
            if incoming[grant['skill_id']] == 0:
                queue.append(grant['skill_id'])
    if len(queue) != len(known):
        raise ValueError('Skill-derived grants cannot contain cycles')
    return rules


def resolve_skill_grants(character, pack, roots):
    rules = skill_grant_rules(pack)
    levels = character.get('learning_levels', {})
    active: dict[str, int] = {}
    for row in roots:
        identifier = row['id']
        acquired = levels.get(learning_key('skill', identifier, row.get('specialty', '')),
                              row.get('learned_level', character['level']))
        active[identifier] = min(active.get(identifier, acquired), acquired)
    granted: dict[str, Any] = {}
    pending = list(active)
    while pending:
        parent = pending.pop(0)
        for grant in rules.get(parent, []):
            identifier = grant['skill_id']
            acquired = levels.get(learning_key('skill', identifier), min(active.get(identifier, active[parent]), active[parent]))
            row = granted.setdefault(identifier, {'bonus': 0, 'learned_level': acquired, 'origins': []})
            row['bonus'] = max(row['bonus'], grant['bonus'])
            row['learned_level'] = min(row['learned_level'], acquired)
            origin = {'parent_id': parent, **grant}
            if origin not in row['origins']:
                row['origins'].append(origin)
            previous = active.get(identifier)
            active[identifier] = min(previous if previous is not None else acquired, acquired)
            if previous is None or active[identifier] < previous:
                pending.append(identifier)
    return granted
