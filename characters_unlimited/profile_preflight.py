"""Preflight supported owned-profile components before generation draws."""

from .class_contributions import class_numeric_contributions
from .resources import validate_resource_rules
from .physical import validate_physical_rules
from .skills import optional_pool_groups
from .skill_effects import pack_skill_effects
from .required_definitions import required_catalog
from .combat import validate_combat_choices
from .level_resource_gains import level_gain_definitions
from .retained_acquisitions import validate_acquisition_catalog
from .recorded_formulas import MAX_INTEGER
from .option_selectors import select_options


def _source(source):
    if (not isinstance(source, dict) or any(not isinstance(source.get(key), str) or
            not source[key].strip() for key in ('book', 'section'))):
        raise ValueError('Declarations need book and section evidence')


def _skill_rules(pack):
    select_options({'any_of': [{'ids': []}]}, pack['skills'])
    optional_pool_groups(pack)
    required_catalog(pack)
    pack_skill_effects(pack)
    known = {row['id'] for row in pack['skills']}
    for rule in pack['pools'].values():
        if (not {'count', 'bonus'} <= set(rule) or set(rule) - {'count', 'bonus', 'requirements'} or
                type(rule['bonus']) is not int or abs(rule['bonus']) > MAX_INTEGER):
            raise ValueError('Skill pools need supported count and exact bonus fields')
    if set(pack['selection_rules']) - set(pack['pools']):
        raise ValueError('Category rules must reference declared pools')
    for categories in pack['selection_rules'].values():
        if not isinstance(categories, dict):
            raise ValueError('Category rules require mappings')
        for category, rule in categories.items():
            if (not isinstance(category, str) or not category or not isinstance(rule, dict) or
                not {'allow', 'bonus'} <= set(rule) or set(rule) - {'allow', 'bonus', 'bonuses', 'exclude', 'costs'} or
                    type(rule['bonus']) is not int or abs(rule['bonus']) > MAX_INTEGER):
                raise ValueError('Unsupported category entitlement declaration')
            bonuses = rule.get('bonuses', {})
            if (not isinstance(bonuses, dict) or len(bonuses) > 1000 or
                    any(identifier not in known or
                        next(row for row in pack['skills'] if row['id'] == identifier).get('category', 'domestic') != category or
                        type(amount) is not int or abs(amount) > MAX_INTEGER
                        for identifier, amount in bonuses.items())):
                raise ValueError('Category bonus exceptions need known same-category skills and exact amounts')
            for key in ('allow', 'exclude'):
                values = rule.get(key, [])
                if key == 'allow' and values == 'any':
                    continue
                if (not isinstance(values, list) or len(values) > 1000 or
                        any(not isinstance(value, str) or not value for value in values) or len(set(values)) != len(values)):
                    raise ValueError('Category restrictions need distinct option identities')
    if len(pack['fixed_domestic_grants']) > 1000:
        raise ValueError('Fixed skill grants require a bounded list')
    for grant in pack['fixed_domestic_grants']:
        if (not isinstance(grant, dict) or set(grant) != {'id', 'bonus'} or
                not isinstance(grant['id'], str) or grant['id'] not in known or
                type(grant['bonus']) is not int or abs(grant['bonus']) > MAX_INTEGER):
            raise ValueError('Fixed skill grants need known identities and exact bonuses')


def _progression(rules, resources):
    if (not isinstance(rules, dict) or not {'hp_die', 'max_level', 'xp_ranges', 'source'} <= set(rules) or
            set(rules) - {'hp_die', 'max_level', 'xp_ranges', 'source', 'class_id', 'resource_gains', 'related_levels', 'secondary_levels', 'related_per_award', 'secondary_per_award'} or
            type(rules['hp_die']) is not int or not 1 <= rules['hp_die'] <= 1000 or
            type(rules['max_level']) is not int or not 1 <= rules['max_level'] <= 1000):
        raise ValueError('Unsupported progression declaration')
    _source(rules['source'])
    ranges = rules['xp_ranges']
    if not isinstance(ranges, list) or len(ranges) != rules['max_level']:
        raise ValueError('XP ranges must cover every declared level')
    expected = 0
    for interval in ranges:
        if (not isinstance(interval, list) or len(interval) != 2 or
                any(type(value) is not int or not 0 <= value <= MAX_INTEGER for value in interval) or
                interval[0] != expected or interval[1] < interval[0]):
            raise ValueError('XP ranges must be exact, ordered and contiguous')
        expected = interval[1] + 1
    for key in ('related_levels', 'secondary_levels'):
        levels = rules.get(key, [])
        if (not isinstance(levels, list) or len(levels) > 1000 or
                any(type(level) is not int or not 1 <= level <= rules['max_level'] for level in levels) or
                len(set(levels)) != len(levels)):
            raise ValueError('Skill awards must name distinct supported levels')
    for pool in ('related', 'secondary'):
        amount = rules.get(pool + '_per_award', 1)
        if type(amount) is not int or not 1 <= amount <= 1000:
            raise ValueError('Skill awards require a bounded positive count')
    gains = level_gain_definitions(rules, resources)
    validate_acquisition_catalog({'level-resources': {identifier: row['formula'] for identifier, row in gains.items()}})


def preflight_owned_profiles(pack):
    for identity, profile in pack['class_profiles'].items():
        composed = {**pack, **profile}
        field = 'source'
        try:
            _source(composed['source'])
            field = 'resources'
            resources = validate_resource_rules(composed)
            field = 'skills'
            _skill_rules(composed)
            field = 'physical'
            validate_physical_rules(composed, resources)
            field = 'class_bonuses'
            class_numeric_contributions(composed)
            field = 'combat'
            validate_combat_choices({}, composed)
            for field in ('advancement', 'higher_advancement'):
                _progression(composed[field], resources)
        except (ValueError, TypeError, KeyError, AttributeError) as error:
            raise ValueError(identity + ' ' + field + ': ' + str(error)) from None
