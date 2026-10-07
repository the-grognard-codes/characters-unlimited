"""Category entitlements and prerequisite guidance for reviewed skill choices."""

from .combat_grants import fixed_proficiencies


def needs_specialty(definition):
    return definition.get('requires_specialty', definition['id'] == 'instrument')


def specialty_key(value):
    return ' '.join(value.split()).casefold()


def selection_limit(rule):
    if 'max_choices' not in rule:
        return None
    maximum = rule['max_choices']
    if type(maximum) is not int or not 0 <= maximum <= 1000:
        raise ValueError('Category choice limits need an exact bounded nonnegative count')
    return maximum


def selection_policy(definition, pool, pack):
    if 'selection_rules' not in pack:
        return {'allowed': True, 'bonus': pack['pools'][pool]['bonus'], 'cost':1}
    rule = pack['selection_rules'][pool].get(definition.get('category', 'domestic'), {})
    allowed = rule.get('allow') == 'any' or definition['id'] in rule.get('allow', [])
    allowed = allowed and definition['id'] not in rule.get('exclude', [])
    cost = rule.get('costs', {}).get(definition['id'], 1) if allowed else 1
    if type(cost) is not int or not 1 <= cost <= 100:
        raise ValueError('Skill selection costs must be positive whole numbers up to 100')
    bonus = rule.get('bonuses', {}).get(definition['id'], rule.get('bonus', 0)) if allowed else 0
    return {'allowed': allowed, 'bonus': bonus, 'cost':cost}


def learned_selection_ids(selections, pack):
    known = {definition['id']: definition for definition in pack['skills']}
    return {item['skill_id'] for item in selections
            if not needs_specialty(known[item['skill_id']]) or item.get('specialty')}


def learned_selection_pools(selections, pack):
    known = {definition['id']: definition for definition in pack['skills']}
    result: dict[str, set[str]] = {}
    for item in selections:
        if not needs_specialty(known[item['skill_id']]) or item.get('specialty'):
            result.setdefault(item['skill_id'], set()).add(item['pool'])
    return result


def weapon_prerequisites(definition, pack):
    declarations = definition.get('weapon_prerequisites', [])
    if not isinstance(declarations, list) or len(declarations) > 1000:
        raise ValueError('Weapon prerequisites need a bounded list')
    seen = set()
    for declaration in declarations:
        if (not isinstance(declaration, dict) or set(declaration) != {'family', 'id', 'source'} or
                declaration.get('family') not in ('ancient', 'modern') or
                not isinstance(declaration.get('id'), str)):
            raise ValueError('Weapon prerequisites need a supported family and identity')
        identity = (declaration['family'], declaration['id'])
        known = {row['id'] for row in pack.get('combat', {}).get(declaration['family'], [])}
        source = declaration['source']
        if (identity in seen or declaration['id'] not in known or not isinstance(source, dict) or
                any(not isinstance(source.get(key), str) or not source[key].strip() for key in ('book', 'section'))):
            raise ValueError('Weapon prerequisites need distinct known proficiencies and source evidence')
        seen.add(identity)
    return declarations


def choice_guidance(selections, pack, granted=(), *, combat_choices=None):
    known = {definition['id']: definition for definition in pack['skills']}
    available = learned_selection_ids(selections, pack)
    granted_ids = {item['id'] for item in granted}
    available.update(granted_ids)
    granted_languages = {specialty_key(item['specialty']) for item in granted
                         if item['id'] in ('native-language', 'other-language') and item.get('specialty')}
    warnings = []
    for item in selections:
        definition = known[item['skill_id']]
        if not selection_policy(definition, item['pool'], pack)['allowed']:
            training = ('without additional pool training' if pack.get('required_skill_training') is not None
                        else 'without an O.C.C. bonus')
            warnings.append(f"{definition['name']}: not available in the {item['pool']} pool under these rules; the choice is retained {training}.")
        if definition['id'] in granted_ids and not needs_specialty(definition):
            owner = 'an acquired skill' if any(row['id'] == definition['id'] and row.get('grant_origins') for row in granted) else 'the O.C.C.'
            warnings.append(f"{definition['name']}: already granted by {owner}; the extra choice is retained without another proficiency bonus.")
        if definition['id'] == 'language-other' and specialty_key(item.get('specialty', '')) in granted_languages:
            warnings.append(f"{definition['name']} — {item['specialty']}: already granted; the retained choice does not create another language proficiency.")
        for dependency in definition.get('pending_prerequisites', []):
            warnings.append(f"{definition['name']}: pending prerequisite — {dependency}")
        for alternatives in definition.get('prerequisites', []):
            if not available.intersection(alternatives):
                labels = ' or '.join(known[identifier]['name'] for identifier in alternatives)
                warnings.append(f"{definition['name']}: missing prerequisite {labels}; the choice is retained.")
        for prerequisite in weapon_prerequisites(definition, pack):
            family = prerequisite['family']
            granted_weapons = fixed_proficiencies(pack.get('combat', {}))
            if prerequisite['id'] not in [*(combat_choices or {}).get(family, []), *granted_weapons[family]]:
                label = next(row['name'] for row in pack['combat'][family] if row['id'] == prerequisite['id'])
                warnings.append(f"{definition['name']}: missing prerequisite {label}; the choice is retained.")
    for pool, categories in pack.get('selection_rules', {}).items():
        for category, rule in categories.items():
            maximum = selection_limit(rule)
            if maximum is None:
                continue
            qualified = {(item['skill_id'], specialty_key(item.get('specialty', '')))
                         for item in selections if item['pool'] == pool and
                         known[item['skill_id']].get('category', 'domestic') == category and
                         selection_policy(known[item['skill_id']], pool, pack)['allowed'] and
                         (not needs_specialty(known[item['skill_id']]) or item.get('specialty'))}
            if len(qualified) > maximum:
                warnings.append(f'{pool.title()} {category}: choose at most {maximum} distinct skill(s); choices are retained.')
    return warnings
