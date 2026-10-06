"""Validate and select source-bound independently progressing skill checks."""

from .recorded_formulas import MAX_INTEGER


def independent_check_rules(definition, catalog):
    if 'proficiency_rules' not in definition:
        return None
    rules = definition['proficiency_rules']
    if (not isinstance(rules, dict) or set(rules) != {'independent_checks', 'source'} or
            rules['independent_checks'] is not True):
        raise ValueError('Unsupported independent proficiency declaration')
    source = rules['source']
    if (not isinstance(source, dict) or any(not isinstance(source.get(key), str) or
            not source[key].strip() for key in ('book', 'section'))):
        raise ValueError('Independent proficiency rules need source evidence')
    for field in ('base', 'per_level'):
        if type(definition.get(field)) is not int or not 0 <= definition[field] <= MAX_INTEGER:
            raise ValueError('Independent proficiency needs exact nonnegative base and growth')
    checks = definition.get('additional_checks', [])
    if not isinstance(checks, list) or len(checks) > 1000:
        raise ValueError('Independent checks need a bounded list')
    known = {row['id'] for row in catalog}
    names = set()
    for check in checks:
        if (not isinstance(check, dict) or
                not isinstance(check.get('name'), str) or not check['name'].strip() or
                check['name'] in names):
            raise ValueError('Independent checks need distinct names and exact base and growth')
        if 'context_of' in check:
            allowed = {'name', 'context_of', 'modifier', 'multiplier', 'maximum', 'requires_skill', 'unless_skill'}
            if (set(check) - allowed or check['context_of'] != 'primary' or
                    any(type(check[field]) is not int or abs(check[field]) > MAX_INTEGER
                        for field in ('modifier', 'multiplier', 'maximum') if field in check) or
                    check.get('multiplier', 1) <= 0 or check.get('maximum', 0) < 0):
                raise ValueError('Context checks need a primary reference and bounded exact modifiers')
        elif (not {'base', 'per_level'} <= set(check) or
                set(check) - {'name', 'base', 'per_level', 'requires_skill', 'unless_skill', 'unless_pool', 'bonus_policy', 'requires_skills', 'unless_skills'} or
                any(type(check[field]) is not int or not 0 <= check[field] <= MAX_INTEGER
                    for field in ('base', 'per_level'))):
            raise ValueError('Independent checks need distinct names and exact base and growth')
        if 'bonus_policy' in check and (check['bonus_policy'] != 'intelligence-only' or check['per_level'] != 0):
            raise ValueError('Fixed intelligence-only checks cannot acquire level growth')
        if 'unless_pool' in check and ('unless_skill' not in check or
                check['unless_pool'] not in ('domestic', 'related', 'secondary')):
            raise ValueError('Check pool selectors need a supported pool and skill identity')
        for field in ('requires_skill', 'unless_skill'):
            if field in check and (not isinstance(check[field], str) or check[field] not in known):
                raise ValueError('Independent checks must select a known skill identity')
        for field in ('requires_skills', 'unless_skills'):
            if field in check:
                identifiers = check[field]
                if (not isinstance(identifiers, list) or not 1 <= len(identifiers) <= 1000 or
                        any(not isinstance(identifier, str) or identifier not in known for identifier in identifiers) or
                        len(set(identifiers)) != len(identifiers)):
                    raise ValueError('Independent check conditions need distinct known skill identities')
        names.add(check['name'])
    return rules


def selected_check_definition(definition, available, selection_pools=None):
    if 'proficiency_rules' not in definition:
        return definition
    return {**definition, 'additional_checks': [check for check in definition.get('additional_checks', [])
            if (check.get('requires_skill') is None or check['requires_skill'] in available)
            and all(identifier in available for identifier in check.get('requires_skills', []))
            and not ('unless_skills' in check and all(identifier in available for identifier in check['unless_skills']))
            and not (check.get('unless_skill') in available and
                ('unless_pool' not in check or check['unless_pool'] in
                 (selection_pools or {}).get(check['unless_skill'], set())))]}
