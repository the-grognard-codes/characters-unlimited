"""Numeric effect operations independent of class, race or acquisition family."""


def effect_total(base, effects):
    if type(base) is not int or not isinstance(effects, list) or len(effects) > 100:
        raise ValueError('Numeric effects require an integer base and bounded operation list')
    additions, minima = [], []
    for effect in effects:
        if (not isinstance(effect, dict) or set(effect) != {'operation', 'value'} or
                effect['operation'] not in ('add', 'minimum') or type(effect['value']) is not int):
            raise ValueError('Unsupported numeric effect operation')
        if effect['operation'] == 'add':
            additions.append(effect['value'])
        else:
            minima.append(effect['value'])
    return max([base + sum(additions), *minima])
