"""Versioned attribute contributions to saving rolls, separate from roll targets."""


def project_saving_bonuses(character, pack):
    rules = pack.get('attribute_saves')
    if not rules:
        return {}, []
    results = {}
    for definition in rules['definitions']:
        contributions = {}
        missing = False
        for rule in definition['contributions']:
            score = character['attributes'][rule['attribute']]['value']
            if score < 1:
                missing = True
                continue
            cap = rule['cap_at']
            contributions[rule['key']] = (rule['values'][str(min(score, cap))]
                                          + max(0, score - cap) * rule['beyond_cap_step'])
        results[definition['id']] = {'name': definition['name'], 'unit': definition['unit'],
            'value': None if missing else sum(contributions.values()), 'contributions': contributions,
            'sources': [definition['source']]}
    class_rules = pack.get('class_bonuses',{})
    if character['character_class'] == class_rules.get('class_id'):
        for identifier,bonus in class_rules['saving'].items():
            result = results[identifier]
            result['contributions']['O.C.C.'] = bonus
            if result['value'] is not None:
                result['value'] += bonus
            result['sources'].append(class_rules['source'])
    notes = list(rules['notes'])
    for condition in rules['conditions']:
        score = character['attributes'][condition['attribute']]['value']
        if score >= condition['minimum'] and ('maximum' not in condition or score <= condition['maximum']):
            notes.append(condition['text'])
    if any(character['attributes'][name]['value'] < 1 for name in ('IQ', 'ME', 'PE')):
        notes.append('An attribute below 1 has no reviewed saving rule; affected contributions remain blank.')
    return results, notes
