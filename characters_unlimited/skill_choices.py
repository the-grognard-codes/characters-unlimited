"""Category entitlements and prerequisite guidance for reviewed skill choices."""


def needs_specialty(definition):
    return definition.get('requires_specialty', definition['id'] == 'instrument')


def selection_policy(definition, pool, pack):
    if 'selection_rules' not in pack:
        return {'allowed': True, 'bonus': pack['pools'][pool]['bonus']}
    rule = pack['selection_rules'][pool].get(definition.get('category', 'domestic'), {})
    allowed = rule.get('allow') == 'any' or definition['id'] in rule.get('allow', [])
    return {'allowed': allowed, 'bonus': rule.get('bonus', 0) if allowed else 0}


def learned_selection_ids(selections, pack):
    known = {definition['id']: definition for definition in pack['skills']}
    return {item['skill_id'] for item in selections
            if not needs_specialty(known[item['skill_id']]) or item.get('specialty')}


def choice_guidance(selections, pack):
    known = {definition['id']: definition for definition in pack['skills']}
    available = learned_selection_ids(selections, pack)
    warnings = []
    for item in selections:
        definition = known[item['skill_id']]
        if not selection_policy(definition, item['pool'], pack)['allowed']:
            warnings.append(f"{definition['name']}: not available in the {item['pool']} pool under these rules; the choice is retained without an O.C.C. bonus.")
        for alternatives in definition.get('prerequisites', []):
            if not available.intersection(alternatives):
                labels = ' or '.join(known[identifier]['name'] for identifier in alternatives)
                warnings.append(f"{definition['name']}: missing prerequisite {labels}; the choice is retained.")
    return warnings
