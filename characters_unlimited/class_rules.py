"""Resolve a class's reviewed rules while retaining the shared pack identity."""

from copy import deepcopy


PROFILE_FIELDS = {'name', 'path_name', 'source', 'pools', 'required', 'selection_rules',
                  'combat', 'class_bonuses', 'resources', 'advancement', 'higher_advancement',
                  'physical_grants', 'fixed_domestic_grants', 'path_guidance'}


def class_rules(pack, character):
    identifier = character['character_class']
    # Before profiles, this archive's sole Rifts class was the Vagabond.
    default = pack.get('default_class', 'vagabond')
    if identifier == default:
        return deepcopy(pack)
    profile = pack.get('class_profiles', {}).get(identifier)
    if not isinstance(profile, dict) or set(profile) - PROFILE_FIELDS:
        raise ValueError('The pinned skill rules do not support this character class')
    result = {**deepcopy(pack), **deepcopy(profile)}
    if any(result.get(key, {}).get('class_id') != identifier for key in ('class_bonuses','advancement')):
        raise ValueError('Class-specific rules must identify their supported class')
    return result


def equipment_class_rules(pack, character):
    """Resolve starting funds; unsupported classes retain the guarded base rules."""
    profiles = pack.get('class_profiles', {})
    if not isinstance(profiles, dict):
        raise ValueError('Equipment class profiles must be a mapping')
    profile = profiles.get(character['character_class'])
    if profile is None:
        return deepcopy(pack)
    if (not isinstance(profile, dict) or set(profile) != {'starting_funds'} or
            not isinstance(profile['starting_funds'], dict) or
            profile['starting_funds'].get('character_class') != character['character_class']):
        raise ValueError('Starting funds profile must identify its supported class')
    return {**deepcopy(pack), **deepcopy(profile)}
