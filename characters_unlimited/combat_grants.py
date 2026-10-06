"""Source-bound fixed weapon training, independent of elective choices."""


def fixed_proficiencies(rules):
    if 'fixed_proficiencies' not in rules:
        return {'ancient': [], 'modern': []}
    grants = rules['fixed_proficiencies']
    if not isinstance(grants, dict) or set(grants) != {'ancient', 'modern', 'source'}:
        raise ValueError('Fixed weapon training needs supported families and source evidence')
    source = grants['source']
    if (not isinstance(source, dict) or any(not isinstance(source.get(key), str) or
            not source[key].strip() for key in ('book', 'section'))):
        raise ValueError('Fixed weapon training needs book and section evidence')
    for family in ('ancient', 'modern'):
        values = grants[family]
        known = {row['id'] for row in rules[family]}
        if (not isinstance(values, list) or len(values) > 1000 or
                any(not isinstance(value, str) or value not in known for value in values) or
                len(set(values)) != len(values)):
            raise ValueError('Fixed weapon training must reference distinct known identities')
    return grants
