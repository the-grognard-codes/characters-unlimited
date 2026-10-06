"""Source-bound fixed weapon training, independent of elective choices."""


def proficiency_allowances(rules):
    counts = rules.get('proficiency_counts', {'ancient': 1, 'modern': 1})
    if (not isinstance(counts, dict) or set(counts) != {'ancient', 'modern'} or
            any(type(value) is not int or not 0 <= value <= 1000 for value in counts.values()) or
            ('proficiency_counts' in rules and 'combined_proficiency_count' in rules)):
        raise ValueError('Weapon allowances require bounded family counts')
    if 'additional_proficiency_cost' in rules:
        amount = rules['additional_proficiency_cost']
        if (type(amount) is not int or not 0 <= amount <= 1000 or
                'proficiency_counts' not in rules):
            raise ValueError('Additional weapon training needs family allowances and a bounded cost')
    if 'proficiency_counts' in rules:
        required = rules.get('required_proficiencies')
        if not isinstance(required, dict) or set(required) != {'ancient', 'modern'}:
            raise ValueError('Weapon allowances need explicit required families')
        for family in ('ancient', 'modern'):
            allowed = required[family]
            if allowed == 'any':
                continue
            known = {row['id'] for row in rules[family]}
            if (not isinstance(allowed, list) or len(allowed) > 1000 or
                    any(not isinstance(value, str) or value not in known for value in allowed) or
                    len(set(allowed)) != len(allowed)):
                raise ValueError('Required weapon slots need distinct known training identities')
    return counts


def proficiency_selection_cost(choices, rules):
    counts = proficiency_allowances(rules)
    cost = rules.get('additional_proficiency_cost', 0)
    fixed = fixed_proficiencies(rules)
    extras = 0
    for family in ('ancient', 'modern'):
        selected = set(choices[family]) - set(fixed[family])
        allowed = rules['required_proficiencies'][family]
        eligible = selected if allowed == 'any' else selected.intersection(allowed)
        filled = min(counts[family], len(eligible))
        extras += len(selected) - filled
    return extras * cost


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
