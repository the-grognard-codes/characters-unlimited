"""Source-bound additive numeric effects, independent of game and owner."""

from copy import deepcopy
from .recorded_formulas import MAX_INTEGER


def compile_numeric_contributions(rows, targets):
    if (not isinstance(rows, list) or len(rows) > 1000 or
            not isinstance(targets, (set, list, tuple)) or
            any(not isinstance(target, str) or not target.strip() for target in targets)):
        raise ValueError('Numeric contributions require bounded rows and known targets')
    seen = set()
    for row in rows:
        if (not isinstance(row, dict) or set(row) != {'id', 'name', 'operation', 'target', 'amount', 'source'} or
                any(not isinstance(row[key], str) or not row[key].strip() for key in ('id', 'name', 'target')) or
                row['id'] in seen or row['operation'] != 'add' or row['target'] not in targets or
                type(row['amount']) is not int or abs(row['amount']) > MAX_INTEGER):
            raise ValueError('Numeric contributions need distinct identities, known targets and exact additions')
        source = row['source']
        if (not isinstance(source, dict) or any(not isinstance(source.get(key), str) or
                not source[key].strip() for key in ('book', 'section'))):
            raise ValueError('Numeric contributions need book and section evidence')
        seen.add(row['id'])
    return deepcopy(rows)


def apply_numeric_contributions(result, rows, target):
    """Return a projection without losing colliding labels or unknown base values."""
    effects = compile_numeric_contributions(rows, {target})
    if not effects:
        return deepcopy(result)
    base = result['value']
    if base is not None and (type(base) is not int or abs(base) > MAX_INTEGER):
        raise ValueError('Numeric contribution base exceeds the exact integer range')
    total = None if base is None else base + sum(row['amount'] for row in effects)
    if total is not None and abs(total) > MAX_INTEGER:
        raise ValueError('Numeric contribution total exceeds the exact integer range')
    projected = deepcopy(result)
    projected['value'] = total
    for effect in effects:
        label = effect['name']
        suffix = 2
        while label in projected['contributions']:
            label = effect['name'] + ' (' + str(suffix) + ')'
            suffix += 1
        projected['contributions'][label] = effect['amount']
        projected['sources'].append(deepcopy(effect['source']))
    if effects:
        projected.setdefault('effect_contributions', []).extend(effects)
    return projected
