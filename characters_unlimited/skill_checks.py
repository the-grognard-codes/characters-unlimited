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
        if (not isinstance(check, dict) or not {'name', 'base', 'per_level'} <= set(check) or
                set(check) - {'name', 'base', 'per_level', 'requires_skill', 'unless_skill'} or
                not isinstance(check.get('name'), str) or not check['name'].strip() or
                check['name'] in names or any(type(check.get(field)) is not int or
                not 0 <= check[field] <= MAX_INTEGER for field in ('base', 'per_level'))):
            raise ValueError('Independent checks need distinct names and exact base and growth')
        for field in ('requires_skill', 'unless_skill'):
            if field in check and (not isinstance(check[field], str) or check[field] not in known):
                raise ValueError('Independent checks must select a known skill identity')
        names.add(check['name'])
    return rules


def selected_check_definition(definition, available):
    if 'proficiency_rules' not in definition:
        return definition
    return {**definition, 'additional_checks': [check for check in definition.get('additional_checks', [])
            if (check.get('requires_skill') is None or check['requires_skill'] in available)
            and check.get('unless_skill') not in available]}
