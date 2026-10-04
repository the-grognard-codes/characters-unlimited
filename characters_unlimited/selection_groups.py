"""Distinct, weighted choice accounting independent of game or option family."""


def validate_allowance(count):
    if type(count) is not int or not 0 <= count <= 1000:
        raise ValueError('Selection group allowance must be a whole number from 0 to 1000')


def validate_group(group):
    if (not isinstance(group, dict) or
            not {'count', 'option_ids'} <= set(group) or
            set(group) - {'count', 'option_ids', 'costs', 'unresolved'}):
        raise ValueError('Invalid selection group allowance')
    validate_allowance(group['count'])
    options = group['option_ids']
    if (not isinstance(options, list) or len(options) > 1000 or
            any(not isinstance(item, str) or not item for item in options) or
            len(set(options)) != len(options)):
        raise ValueError('Selection groups need distinct referenced option identities')
    costs = group.get('costs', {})
    if (not isinstance(costs, dict) or set(costs) - set(options) or
            any(type(value) is not int or not 1 <= value <= 100 for value in costs.values())):
        raise ValueError('Selection costs must reference group options and be whole numbers from 1 to 100')
    unresolved = group.get('unresolved', [])
    if (not isinstance(unresolved, list) or
            any(not isinstance(item, str) or item not in options for item in unresolved) or
            len(set(unresolved)) != len(unresolved)):
        raise ValueError('Unresolved selection credit must reference distinct group options')


def project_group(group, selections, *, certified=True):
    """Retain entered choices; credit distinct eligible, resolved choices once."""
    validate_group(group)
    if (not isinstance(selections, list) or len(selections) > 1000 or
            any(not isinstance(item, str) for item in selections) or type(certified) is not bool):
        raise ValueError('Selection group choices must be an identity list')
    distinct = list(dict.fromkeys(selections))
    options = set(group['option_ids'])
    unresolved = [item for item in distinct if item in group.get('unresolved', [])]
    eligible = [item for item in distinct if item in options and item not in unresolved] if certified else []
    credited = sum(group.get('costs', {}).get(item, 1) for item in eligible)
    return {'eligible': eligible, 'credited': credited, 'remaining': group['count'] - credited,
            'unresolved': unresolved, 'outside': [item for item in distinct if item not in options],
            'duplicates': len(distinct) != len(selections)}
