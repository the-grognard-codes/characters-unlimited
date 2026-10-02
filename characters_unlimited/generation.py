"""Dice-pool generation from accepted racial formulas."""


def generation_settings(value=None):
    if value is None:
        return {"reroll_ones": False, "extra_die": False}
    if not isinstance(value, dict) or set(value) - {"reroll_ones", "extra_die"}:
        raise ValueError("Unknown generation setting")
    settings = {"reroll_ones": False, "extra_die": False, **value}
    if any(type(setting) is not bool for setting in settings.values()):
        raise ValueError("Generation settings must be true or false")
    return settings


def roll_attribute(formula, settings, die, source):
    count, sides, constant = formula["count"], formula["sides"], formula.get("constant", 0)
    if type(count) is not int or not 0 <= count <= 1000 or type(sides) is not int or not 1 <= sides <= 1000 or type(constant) is not int:
        raise ValueError("Unsupported attribute dice formula")
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
    total = sum(kept) + constant
    bonus_rolls = []
    exceptional = formula.get("exceptional")
    if exceptional and total in exceptional["thresholds"]:
        for _ in range(exceptional["max_bonus_dice"]):
            bonus = draw()
            bonus_rolls.append(bonus)
            total += bonus
            if bonus != sides:
                break
    return {
        "base": total, "value": total, "adjustment": 0, "fixed": None,
        "rolls": pool, "original_rolls": originals, "kept": kept, "discarded": discarded,
        "rerolls": rerolls, "bonus_rolls": bonus_rolls,
        "generation": settings,
        "explanation": {"formula": f"{count}D{sides}{constant:+d}" if constant else f"{count}D{sides}", "source": source},
    }
