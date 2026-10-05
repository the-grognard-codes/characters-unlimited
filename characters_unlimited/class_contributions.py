"""Translate legacy class metadata into shared numeric contributions."""

from .numeric_contributions import compile_numeric_contributions


def class_numeric_contributions(pack):
    rules = pack.get('class_bonuses', {})
    if rules == {}:
        return []
    if (not isinstance(rules, dict) or set(rules) != {'class_id', 'perception', 'saving', 'source'} or
            not isinstance(rules['class_id'], str) or not rules['class_id'].strip() or
            not isinstance(rules['saving'], dict) or
            any(not isinstance(key, str) or not key.strip() for key in rules['saving'])):
        raise ValueError('Unsupported class numeric bonus declaration')
    targets = {'saving:' + row['id'] for row in pack.get('attribute_saves', {}).get('definitions', [])}
    targets.add('perception')
    amounts = {'perception': rules['perception'], **{'saving:' + key: value for key, value in rules['saving'].items()}}
    rows = [{'id': 'class:' + rules['class_id'] + ':' + target, 'name': 'O.C.C.',
             'operation': 'add', 'target': target, 'amount': amount, 'source': rules['source']}
            for target, amount in amounts.items()]
    return compile_numeric_contributions(rows, targets)
