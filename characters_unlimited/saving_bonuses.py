"""Versioned attribute contributions to saving rolls, separate from roll targets."""


from .class_contributions import class_numeric_contributions
from .numeric_contributions import apply_numeric_contributions


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
    effects = class_numeric_contributions(pack)
    if character['character_class'] == pack.get('class_bonuses', {}).get('class_id'):
        for identifier, result in results.items():
            target = 'saving:' + identifier
            results[identifier] = apply_numeric_contributions(result,
                [effect for effect in effects if effect['target'] == target], target)
    notes = list(rules['notes'])
    for condition in rules['conditions']:
        score = character['attributes'][condition['attribute']]['value']
        if score >= condition['minimum'] and ('maximum' not in condition or score <= condition['maximum']):
            notes.append(condition['text'])
    if any(character['attributes'][name]['value'] < 1 for name in ('IQ', 'ME', 'PE')):
        notes.append('An attribute below 1 has no reviewed saving rule; affected contributions remain blank.')
    return results, notes
