"""Category entitlements and prerequisite guidance for reviewed skill choices."""


def needs_specialty(definition):
    return definition.get('requires_specialty', definition['id'] == 'instrument')


def specialty_key(value):
    return ' '.join(value.split()).casefold()


def selection_policy(definition, pool, pack):
    if 'selection_rules' not in pack:
        return {'allowed': True, 'bonus': pack['pools'][pool]['bonus'], 'cost':1}
    rule = pack['selection_rules'][pool].get(definition.get('category', 'domestic'), {})
    allowed = rule.get('allow') == 'any' or definition['id'] in rule.get('allow', [])
    allowed = allowed and definition['id'] not in rule.get('exclude', [])
    cost = rule.get('costs', {}).get(definition['id'], 1) if allowed else 1
    if type(cost) is not int or not 1 <= cost <= 100:
        raise ValueError('Skill selection costs must be positive whole numbers up to 100')
    return {'allowed': allowed, 'bonus': rule.get('bonus', 0) if allowed else 0, 'cost':cost}


def learned_selection_ids(selections, pack):
    known = {definition['id']: definition for definition in pack['skills']}
    return {item['skill_id'] for item in selections
            if not needs_specialty(known[item['skill_id']]) or item.get('specialty')}


def choice_guidance(selections, pack, granted=()):
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
    return warnings
