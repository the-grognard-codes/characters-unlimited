"""Dice-pool generation from accepted racial formulas."""

from copy import deepcopy
from .attribute_modifiers import ATTRIBUTE_NAMES
from .recorded_formulas import MAX_INTEGER


def generation_settings(value=None):
    if value is None:
        return {"reroll_ones": False, "extra_die": False}
    if not isinstance(value, dict) or set(value) - {"reroll_ones", "extra_die"}:
        raise ValueError("Unknown generation setting")
    settings = {"reroll_ones": False, "extra_die": False, **value}
    if any(type(setting) is not bool for setting in settings.values()):
        raise ValueError("Generation settings must be true or false")
    return settings


def validate_attribute_formula(formula):
    if (not isinstance(formula, dict) or not {'count', 'sides'} <= set(formula) or
            set(formula) - {'count', 'sides', 'constant', 'exceptional', 'cap', 'multiplier'} or
            type(formula['count']) is not int or not 0 <= formula['count'] <= 1000 or
            type(formula['sides']) is not int or not 1 <= formula['sides'] <= 1000 or
            type(formula.get('constant', 0)) is not int or
            abs(formula.get('constant', 0)) > MAX_INTEGER or
            type(formula.get('multiplier', 1)) is not int or
            not 1 <= formula.get('multiplier', 1) <= MAX_INTEGER or
            formula['count'] * formula['sides'] * formula.get('multiplier', 1) +
            abs(formula.get('constant', 0)) > MAX_INTEGER):
        raise ValueError('Unsupported attribute dice formula')
    if 'cap' in formula and (type(formula['cap']) is not int or abs(formula['cap']) > MAX_INTEGER):
        raise ValueError('Attribute ceiling must be a whole number')
    if 'exceptional' in formula:
        exceptional = formula['exceptional']
        if (not isinstance(exceptional, dict) or set(exceptional) != {'thresholds', 'max_bonus_dice'} or
                not isinstance(exceptional['thresholds'], list) or len(exceptional['thresholds']) > 1000 or
                any(type(value) is not int for value in exceptional['thresholds']) or
                len(set(exceptional['thresholds'])) != len(exceptional['thresholds']) or
                (exceptional['max_bonus_dice'] is not None and
                 (type(exceptional['max_bonus_dice']) is not int or not 0 <= exceptional['max_bonus_dice'] <= 1000))):
            raise ValueError('Unsupported exceptional attribute rule')
        multiplier = formula.get('multiplier', 1)
        constant = formula.get('constant', 0)
        minimum = formula['count'] * multiplier + constant
        maximum = formula['count'] * formula['sides'] * multiplier + constant
        limit = exceptional['max_bonus_dice']
        # Unbounded exploding dice still share roll_attribute's 10,000-draw cap.
        bonus_limit = 10000 if limit is None else min(limit, 10000)
        if any(minimum <= threshold <= maximum and (threshold - constant) % multiplier == 0 and
               threshold + bonus_limit * formula['sides'] > MAX_INTEGER
               for threshold in exceptional['thresholds']):
            raise ValueError('Exceptional attributes exceed the supported whole-number range')


def racial_formulas(race, settings=None):
    pools = race.get('attribute_pools', {})
    caps = race.get('attribute_caps', {})
    if (not isinstance(pools, dict) or set(pools) - set(ATTRIBUTE_NAMES) or
            not isinstance(caps, dict) or set(caps) - set(ATTRIBUTE_NAMES) or
            any(type(value) is not int for value in caps.values())):
        raise ValueError('Racial pools and ceilings must reference known attributes')
    default = race.get('attributes')
    if default is not None:
        validate_attribute_formula(default)
    elif set(pools) != set(ATTRIBUTE_NAMES):
        raise ValueError('A race without a default pool must define all eight attributes')
    for formula in pools.values():
        validate_attribute_formula(formula)
    formulas = {name: {**(pools[name] if name in pools else default),
                       **({'cap': caps[name]} if name in caps else {})}
                for name in ATTRIBUTE_NAMES}
    if settings is not None and generation_settings(settings)['reroll_ones']:
        if any(formula['count'] and formula['sides'] == 1 for formula in formulas.values()):
            raise ValueError('Cannot reroll ones on a one-sided die')
    return formulas


def racial_sources(race, core_source):
    overrides = race.get('attribute_sources', {})
    default = race.get('source', core_source)
    if not isinstance(overrides, dict) or set(overrides) - set(ATTRIBUTE_NAMES):
        raise ValueError('Racial attribute sources must reference known attributes')
    for source in [default, *overrides.values()]:
        if (not isinstance(source, dict) or
                any(not isinstance(source.get(key), str) or not source[key].strip()
                    for key in ('book', 'section'))):
            raise ValueError('Racial attribute evidence needs a book and section')
    return {name: deepcopy(overrides.get(name, default)) for name in ATTRIBUTE_NAMES}


def racial_formula(race, attribute):
    if attribute not in ATTRIBUTE_NAMES:
        raise ValueError('Select a known attribute')
    return racial_formulas(race)[attribute]


def roll_attribute(formula, settings, die, source):
    validate_attribute_formula(formula)
    count, sides, constant = formula["count"], formula["sides"], formula.get("constant", 0)
    if count and sides == 1 and settings["reroll_ones"]:
        raise ValueError("Cannot reroll ones on a one-sided die")
    draws = 0

    def draw():
        nonlocal draws
        draws += 1
        if draws > 10000:
            raise ValueError("Dice source failed to finish generation; no character changes were saved")
        value = die(sides)
        if type(value) is not int or not 1 <= value <= sides:
            raise ValueError("Dice source returned an invalid value")
        return value

    originals, pool, rerolls = [], [], []
    for index in range(count + int(settings["extra_die"] and count > 0)):
        value = draw()
        originals.append(value)
        history = [value]
        while settings["reroll_ones"] and value == 1:
            value = draw()
            history.append(value)
        if len(history) > 1:
            rerolls.append({"index": index, "rolls": history})
        pool.append(value)
    kept = pool.copy()
    discarded = []
    if settings["extra_die"] and count:
        discarded.append(kept.pop(kept.index(min(kept))))
    total = sum(kept) * formula.get("multiplier", 1) + constant
    bonus_rolls: list[int] = []
    exceptional = formula.get("exceptional")
    if exceptional and total in exceptional["thresholds"]:
        limit = exceptional["max_bonus_dice"]
        while limit is None or len(bonus_rolls) < limit:
            bonus = draw()
            bonus_rolls.append(bonus)
            total += bonus
            if bonus != sides:
                break
    if abs(total) > MAX_INTEGER:
        raise ValueError('Generated attribute exceeds the supported whole-number range')
    expression = f"{count}D{sides}"
    if formula.get('multiplier', 1) != 1:
        expression += ' × ' + str(formula['multiplier'])
    if constant:
        expression += f"{constant:+d}"
    return {
        **({"cap": formula["cap"]} if "cap" in formula else {}),
        "base": total, "value": min(total, formula["cap"]) if "cap" in formula else total, "adjustment": 0, "fixed": None,
        "rolls": pool, "original_rolls": originals, "kept": kept, "discarded": discarded,
        "rerolls": rerolls, "bonus_rolls": bonus_rolls,
        "generation": settings,
        "explanation": {"formula": expression, "source": source},
    }
