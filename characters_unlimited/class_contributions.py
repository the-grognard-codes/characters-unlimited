"""Translate legacy class metadata into shared numeric contributions."""

from .numeric_contributions import (compile_numeric_contributions, numeric_formula_catalog,
    acquire_numeric_contributions, project_numeric_contributions)
from .recorded_formulas import MAX_INTEGER


def class_saving_definitions(pack):
    """Source-owned save categories without adding rows to other class views."""
    rows = pack.get('class_bonuses', {}).get('saving_definitions', [])
    if not isinstance(rows, list) or len(rows) > 100:
        raise ValueError('Class saving definitions need a bounded list')
    seen = {row['id'] for row in pack.get('attribute_saves', {}).get('definitions', [])}
    for row in rows:
        if (not isinstance(row, dict) or set(row) != {'id', 'name', 'source'}
                or any(not isinstance(row[key], str) or not row[key].strip() for key in ('id', 'name'))
                or row['id'] in seen or not isinstance(row['source'], dict)
                or any(not isinstance(row['source'].get(key), str) or not row['source'][key].strip()
                       for key in ('book', 'section'))):
            raise ValueError('Class saving definitions need distinct categories and source evidence')
        seen.add(row['id'])
    return [{**row, 'unit': '', 'contributions': []} for row in rows]


def class_numeric_contributions(pack, *, level=1, character=None):
    rules = pack.get('class_bonuses', {})
    if rules == {}:
        if character is not None:
            project_numeric_contributions([], set(), character.get('numeric_acquisitions', {}))
        return []
    if (not isinstance(rules, dict) or not {'class_id', 'perception', 'saving', 'source'} <= set(rules) or
            set(rules) - {'class_id', 'perception', 'saving', 'source', 'combat', 'level_bonuses', 'rolled_bonuses', 'saving_definitions'} or
            not isinstance(rules['class_id'], str) or not rules['class_id'].strip() or
            not isinstance(rules['saving'], dict) or
            any(not isinstance(key, str) or not key.strip() for key in rules['saving'])):
        raise ValueError('Unsupported class numeric bonus declaration')
    targets = {'saving:' + row['id'] for row in pack.get('attribute_saves', {}).get('definitions', [])}
    targets.update('saving:' + row['id'] for row in class_saving_definitions(pack))
    targets.add('perception')
    targets.update('combat:' + key for key in ('attacks', 'initiative', 'roll_with_impact', 'dodge', 'disarm', 'strike', 'parry', 'pull_punch'))
    rolled = rules.get('rolled_bonuses', [])
    numeric_formula_catalog(rolled, {target for target in targets if target.startswith('saving:')})
    combat = rules.get('combat', {})
    if not isinstance(combat, dict) or any(not isinstance(key, str) for key in combat):
        raise ValueError('Class combat additions require supported targets')
    amounts = {'perception': rules['perception'], **{'saving:' + key: value for key, value in rules['saving'].items()},
               **{'combat:' + key: value for key, value in combat.items()}}
    if any(target not in targets or type(amount) is not int or abs(amount) > MAX_INTEGER
           for target, amount in amounts.items()):
        raise ValueError('Class additions need known targets and bounded exact amounts')
    bounds = {target: (amount, amount) for target, amount in amounts.items()}
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
        base = amounts.get(row['target'], 0)
        if abs(base + row['amount'] * len(row['levels'])) > MAX_INTEGER:
            raise ValueError('Class milestone totals exceed the supported exact range')
        endpoint = base + row['amount'] * len(row['levels'])
        bounds[row['target']] = (min(base, endpoint), max(base, endpoint))
        amounts[row['target']] = base + row['amount'] * sum(value <= level for value in row['levels'])
        seen.add(row['target'])
    for row in rolled:
        formula = row['formula']
        low, high = bounds.get(row['target'], (0, 0))
        constant, multiplier = formula.get('constant', 0), formula.get('multiplier', 1)
        bounds[row['target']] = (low + (formula['count'] + constant) * multiplier,
                                high + (formula['count'] * formula['sides'] + constant) * multiplier)
    if any(abs(value) > MAX_INTEGER for interval in bounds.values() for value in interval):
        raise ValueError('Combined class additions exceed the exact integer range')
    rows = [{'id': 'class:' + rules['class_id'] + ':' + target, 'name': 'O.C.C.',
             'operation': 'add', 'target': target, 'amount': amount, 'source': rules['source']}
            for target, amount in amounts.items()]
    placeholders = [{key: value for key, value in row.items() if key != 'formula'} |
                    {'operation': 'add', 'amount': 0} for row in rolled]
    compile_numeric_contributions([*rows, *placeholders], targets)
    result = compile_numeric_contributions(rows, targets)
    if character is not None:
        result.extend(project_numeric_contributions(rolled, targets, character.get('numeric_acquisitions', {})))
    return result


def acquire_class_numeric(character, pack, die):
    """Retain permanent source dice at creation; older profiles add no save field."""
    class_numeric_contributions(pack)
    rows = pack.get('class_bonuses', {}).get('rolled_bonuses', [])
    if not rows:
        return {}
    targets = {row['target'] for row in rows}
    return {'numeric_acquisitions': acquire_numeric_contributions(
        rows, targets, character.get('numeric_acquisitions', {}), die)}


def validate_class_numeric_upgrade(previous, target):
    before = previous.get('class_bonuses', {}).get('rolled_bonuses', [])
    after = target.get('class_bonuses', {}).get('rolled_bonuses', [])
    if before != after:
        raise ValueError('This update changes permanent numeric acquisition rules. Receipt migration is not yet supported; current rules remain intact.')
