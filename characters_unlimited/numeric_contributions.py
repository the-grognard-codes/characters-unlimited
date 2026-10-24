"""Source-bound additive numeric effects, independent of game and owner."""

from copy import deepcopy
from .recorded_formulas import MAX_INTEGER, formula_value
from .retained_acquisitions import validate_cached_acquisitions, acquire_selected


def numeric_formula_catalog(rows, targets):
    """Preflight source-bound rolled additions, including unused declarations."""
    if not isinstance(rows, list):
        raise ValueError('Rolled numeric contributions require a bounded list')
    fixed = []
    catalog = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'id', 'name', 'target', 'formula', 'source'}:
            raise ValueError('Rolled numeric contributions need identities, targets, formulas and sources')
        fixed.append({key: value for key, value in row.items() if key != 'formula'} |
                     {'operation': 'add', 'amount': 0})
    compile_numeric_contributions(fixed, targets)
    catalog = {row['id']: {'amount': row['formula']} for row in rows}
    validate_cached_acquisitions(catalog, {})
    return catalog


def acquire_numeric_contributions(rows, targets, acquisitions, die):
    catalog = numeric_formula_catalog(rows, targets)
    return acquire_selected(catalog, acquisitions, list(catalog), die)


def project_numeric_contributions(rows, targets, acquisitions):
    """Replay permanent additions without dice, allowing no missing/extra receipts."""
    catalog = numeric_formula_catalog(rows, targets)
    validate_cached_acquisitions(catalog, acquisitions)
    if set(acquisitions) != set(catalog):
        raise ValueError('Numeric contributions require every retained acquisition')
    return compile_numeric_contributions([
        {key: value for key, value in row.items() if key != 'formula'} |
        {'operation': 'add', 'amount': formula_value(row['formula'], acquisitions[row['id']]['rolls']['amount'])}
        for row in rows], targets)


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
