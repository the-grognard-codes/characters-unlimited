"""Whole-field profile ownership without implicit class-mechanic inheritance."""

from copy import deepcopy


def compose_owned_profile(pack, identifier, field_types):
    if pack.get('class_profile_format') != 'owned-v1':
        raise ValueError('Unsupported class profile ownership format')
    profiles = pack.get('class_profiles')
    default = pack.get('default_class')
    if (not isinstance(profiles, dict) or not 1 <= len(profiles) <= 1000 or
            not isinstance(default, str) or default not in profiles):
        raise ValueError('Owned profiles require an explicit default profile')
    for identity, profile in profiles.items():
        if not isinstance(identity, str) or not identity or not isinstance(profile, dict):
            raise ValueError('Owned profiles require stable identities and mappings')
        missing = set(field_types) - set(profile)
        unknown = set(profile) - set(field_types)
        if missing or unknown:
            raise ValueError(identity + ' profile fields: missing ' + ', '.join(sorted(missing)) +
                             '; unsupported ' + ', '.join(sorted(unknown)))
        for field, expected_type in field_types.items():
            value = profile[field]
            if (not isinstance(value, expected_type) or
                    (expected_type is str and not value.strip())):
                raise ValueError(identity + ' profile has invalid ' + field)
    if identifier not in profiles:
        raise ValueError('The pinned rules do not support this character class')
    shared = {key: deepcopy(value) for key, value in pack.items() if key not in field_types}
    return {**shared, **deepcopy(profiles[identifier])}
