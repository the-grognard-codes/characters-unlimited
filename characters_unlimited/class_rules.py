"""Resolve a class's reviewed rules while retaining the shared pack identity."""

from copy import deepcopy
from .profile_composition import compose_owned_profile
from .profile_preflight import preflight_owned_profiles
from .class_contributions import class_numeric_contributions
from .equipment_profiles import owned_equipment_rules
from .skill_training import training_rules
from .skill_choices import weapon_prerequisites
from .skill_checks import independent_check_rules
from .required_definitions import required_catalog
from .nonpercentile_skills import training_definition


PROFILE_FIELDS = {'name', 'path_name', 'source', 'pools', 'required', 'selection_rules',
                  'combat', 'class_bonuses', 'resources', 'advancement', 'higher_advancement',
                  'physical_grants', 'fixed_domestic_grants', 'path_guidance', 'skill_effects'}


PROFILE_FIELD_TYPES = {field: (str if field in {'name', 'path_name'} else
                      list if field in {'physical_grants', 'fixed_domestic_grants', 'path_guidance', 'skill_effects'} else dict)
                       for field in PROFILE_FIELDS}


def class_rules(pack, character):
    identifier = character['character_class']
    if 'class_profile_format' in pack:
        result = compose_owned_profile(pack, identifier, PROFILE_FIELD_TYPES)
        for identity, profile in result['class_profiles'].items():
            if any(profile[field].get('class_id') != identity for field in ('class_bonuses', 'advancement')):
                raise ValueError(identity + ' class-specific rules must identify their owner')
        preflight_owned_profiles(result)
        return result
    # Validate the raw legacy owners before an overlay can hide the default declarations.
    training_rules(pack)
    for owner in [pack, *pack.get('class_profiles', {}).values()]:
        required_catalog({**pack, **owner})
    for definition in pack['skills']:
        training_definition(definition, pack['skills'])
        independent_check_rules(definition, pack['skills'])
        if 'weapon_prerequisites' in definition:
            for owner in [pack, *pack.get('class_profiles', {}).values()]:
                weapon_prerequisites(definition, {**pack, **owner})
    # Before profiles, this archive's sole Rifts class was the Vagabond.
    default = pack.get('default_class', 'vagabond')
    if identifier == default:
        class_numeric_contributions(pack)
        return deepcopy(pack)
    profile = pack.get('class_profiles', {}).get(identifier)
    if not isinstance(profile, dict) or set(profile) - PROFILE_FIELDS:
        raise ValueError('The pinned skill rules do not support this character class')
    result = {**deepcopy(pack), **deepcopy(profile)}
    result['skill_effects'] = deepcopy(profile.get('skill_effects', []))
    for field in ('advancement', 'higher_advancement'):
        if field not in profile and isinstance(result.get(field), dict):
            result[field].pop('resource_gains', None)
    if any(result.get(key, {}).get('class_id') != identifier for key in ('class_bonuses','advancement')):
        raise ValueError('Class-specific rules must identify their supported class')
    class_numeric_contributions(result)
    return result


def equipment_class_rules(pack, character):
    """Resolve class starting equipment; unsupported classes retain guarded base rules."""
    if 'class_profile_format' in pack:
        return owned_equipment_rules(pack, character)
    profiles = pack.get('class_profiles', {})
    if not isinstance(profiles, dict):
        raise ValueError('Equipment class profiles must be a mapping')
    profile = profiles.get(character['character_class'])
    if profile is None:
        return deepcopy(pack)
    if (not isinstance(profile, dict) or not profile or
            set(profile) - {'starting_funds', 'starting_gear', 'starting_groups'} or
            any(not isinstance(rules, dict) or rules.get('character_class') != character['character_class']
                for rules in profile.values())):
        raise ValueError('Starting equipment profile must identify its supported class')
    return {**deepcopy(pack), **deepcopy(profile)}
