"""Translate legacy class metadata into shared numeric contributions."""

from .numeric_contributions import compile_numeric_contributions
from .recorded_formulas import MAX_INTEGER


def class_numeric_contributions(pack, *, level=1):
    rules = pack.get('class_bonuses', {})
    if rules == {}:
        return []
    if (not isinstance(rules, dict) or not {'class_id', 'perception', 'saving', 'source'} <= set(rules) or
            set(rules) - {'class_id', 'perception', 'saving', 'source', 'combat', 'level_bonuses'} or
            not isinstance(rules['class_id'], str) or not rules['class_id'].strip() or
            not isinstance(rules['saving'], dict) or
            any(not isinstance(key, str) or not key.strip() for key in rules['saving'])):
        raise ValueError('Unsupported class numeric bonus declaration')
    targets = {'saving:' + row['id'] for row in pack.get('attribute_saves', {}).get('definitions', [])}
    targets.add('perception')
    targets.update('combat:' + key for key in ('initiative', 'roll_with_impact'))
    combat = rules.get('combat', {})
    if not isinstance(combat, dict) or any(not isinstance(key, str) for key in combat):
        raise ValueError('Class combat additions require supported targets')
    amounts = {'perception': rules['perception'], **{'saving:' + key: value for key, value in rules['saving'].items()},
               **{'combat:' + key: value for key, value in combat.items()}}
    if any(target not in targets or type(amount) is not int or abs(amount) > MAX_INTEGER
           for target, amount in amounts.items()):
        raise ValueError('Class additions need known targets and bounded exact amounts')
    progression = rules.get('level_bonuses', [])
    if not isinstance(progression, list) or len(progression) > 100 or type(level) is not int or not 1 <= level <= 1000:
        raise ValueError('Class level additions need bounded milestones and a supported level')
    seen = set()
    for row in progression:
        if (not isinstance(row, dict) or set(row) != {'target', 'levels', 'amount'} or
                not isinstance(row['target'], str) or row['target'] not in targets or row['target'] in seen or
                type(row['amount']) is not int or abs(row['amount']) > MAX_INTEGER or
                not isinstance(row['levels'], list) or not 1 <= len(row['levels']) <= 1000 or
                any(type(value) is not int or not 1 <= value <= 1000 for value in row['levels']) or
                len(set(row['levels'])) != len(row['levels'])):
            raise ValueError('Class level additions need distinct known targets and exact milestones')
        amounts[row['target']] = amounts.get(row['target'], 0) + row['amount'] * sum(value <= level for value in row['levels'])
        seen.add(row['target'])
    rows = [{'id': 'class:' + rules['class_id'] + ':' + target, 'name': 'O.C.C.',
             'operation': 'add', 'target': target, 'amount': amount, 'source': rules['source']}
            for target, amount in amounts.items()]
    return compile_numeric_contributions(rows, targets)
