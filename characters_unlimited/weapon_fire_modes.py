"""Opt-in source firing restrictions, with historical behavior preserved."""


def burst_only(definition):
    value = definition.get('burst_only', False)
    if type(value) is not bool:
        raise ValueError('Burst-only firing declarations require an exact boolean')
    return value
