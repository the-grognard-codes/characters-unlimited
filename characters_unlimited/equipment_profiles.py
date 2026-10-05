"""Explicit equipment ownership using the common profile composer and rule compilers."""

from .profile_composition import compose_owned_profile
from .starting_funds import starting_funds_rules
from .starting_gear import starting_gear_rules
from .starting_choices import starting_choice_rules
from .starting_groups import starting_group_rules

EQUIPMENT_FIELDS = {'source': dict, 'starting_funds': dict, 'starting_gear': dict,
                    'starting_choices': dict, 'starting_groups': dict}


def _source(source):
    if (not isinstance(source, dict) or any(not isinstance(source.get(key), str) or
            not source[key].strip() for key in ('book', 'section'))):
        raise ValueError('Equipment declarations need book and section evidence')


def owned_equipment_rules(pack, character):
    if pack.get('id') != 'rifts-equipment' or pack.get('game') != 'rifts':
        raise ValueError('Unsupported owned equipment pack')
    result = compose_owned_profile(pack, character['character_class'], EQUIPMENT_FIELDS)
    for identity, profile in result['class_profiles'].items():
        field = 'source'
        try:
            _source(profile['source'])
            composed = {**result, **profile}
            for field in EQUIPMENT_FIELDS:
                if field == 'source':
                    continue
                rules = profile[field]
                if rules and rules.get('character_class') != identity:
                    raise ValueError('Equipment entitlements must identify their class owner')
                composed[field] = rules or None
            field = 'starting_funds'
            funds = starting_funds_rules(composed)
            for definition in funds['definitions'] if funds else []:
                _source(definition['source'])
            field = 'starting_gear'
            gear = starting_gear_rules(composed)
            if gear:
                _source(gear['source'])
            field = 'starting_choices'
            choices = starting_choice_rules(composed)
            if choices:
                _source(choices['source'])
            field = 'starting_groups'
            groups = starting_group_rules({'game':pack['game'], 'character_class':identity}, composed)
            for group in groups.values():
                _source(group['source'])
        except (ValueError, TypeError, KeyError, AttributeError) as error:
            raise ValueError(identity + ' ' + field + ': ' + str(error)) from None
    for field in EQUIPMENT_FIELDS:
        if field != 'source':
            result[field] = result[field] or None
    return result
