"""Ordinary bonus dice shared by skills, powers and class mechanics.

This module knows neither option identities nor attribute-generation house rules.
Its inputs are reviewed numeric definitions and retained dice; it never evaluates
book prose, expressions, or executable operations.
"""

MAX_INTEGER = 9_007_199_254_740_991


def validate_formula(formula):
    if (not isinstance(formula, dict) or
            set(formula) - {'count', 'sides', 'constant', 'multiplier'} or
            type(formula.get('count')) is not int or not 0 <= formula['count'] <= 1000 or
            type(formula.get('sides')) is not int or not 0 <= formula['sides'] <= 1000 or
            (formula['count'] and formula['sides'] == 0) or
            type(formula.get('constant', 0)) is not int or
            abs(formula.get('constant', 0)) > MAX_INTEGER or
            type(formula.get('multiplier', 1)) is not int or
            not 1 <= formula.get('multiplier', 1) <= MAX_INTEGER):
        raise ValueError('Unsupported recorded bonus formula')


def formula_value(formula, rolls):
    """Replay retained dice strictly and return (sum + constant) * multiplier."""
    validate_formula(formula)
    if (not isinstance(rolls, list) or len(rolls) != formula['count'] or
            any(type(face) is not int or not 1 <= face <= formula['sides'] for face in rolls)):
        raise ValueError('Recorded bonus dice must match their reviewed formula')
    value = (sum(rolls) + formula.get('constant', 0)) * formula.get('multiplier', 1)
    if abs(value) > MAX_INTEGER:
        raise ValueError('Recorded bonus exceeds the supported whole-number range')
    return value


def roll_formula(formula, die):
    """Draw once per specified die, retaining raw ones without extra/drop rules."""
    validate_formula(formula)
    rolls = []
    for _ in range(formula['count']):
        face = die(formula['sides'])
        if type(face) is not int or not 1 <= face <= formula['sides']:
            raise ValueError('Dice source returned an invalid recorded bonus value')
        rolls.append(face)
    formula_value(formula, rolls)
    return rolls
