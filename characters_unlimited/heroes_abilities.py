"""Best duplicated Physical checks, preserving each training's source values."""

from copy import deepcopy
from typing import Any


def project_shared_abilities(skills):
    available = {row['id']:row for row in skills}
    groups: set[tuple[str, ...]] = set()
    for skill in skills:
        partners = set(skill.get('shared_check_skill_ids', [])).intersection(available)
        if partners:
            groups.add(tuple(sorted({skill['id'], *partners})))
    checks = []
    members: set[str] = set()
    for group in sorted(groups):
        members.update(group)
        by_name: dict[str, list[dict[str, Any]]] = {}
        for skill in skills:
            if skill['id'] not in group:
                continue
            candidates = [('', skill['primary_check_name'], skill),
                          *[(f'.check{index}', check['name'], check)
                            for index,check in enumerate(skill.get('additional_checks', []))]]
            for suffix,name,check in candidates:
                origin = {'name':name, 'skill_id':skill['id'], 'skill_name':skill['name'],
                          'key_suffix':suffix, 'percentage':check['percentage'],
                          'per_level':check['per_level'], 'contributions':deepcopy(check['contributions']),
                          'secondary_selected':skill['secondary_selected'], 'source':deepcopy(skill['source'])}
                by_name.setdefault(name, []).append(origin)
        for origins in by_name.values():
            winner = max(origins, key=lambda row:row['percentage'])
            checks.append({**deepcopy(winner), 'origins':origins})
    return {'skill_ids':sorted(members), 'checks':checks}
