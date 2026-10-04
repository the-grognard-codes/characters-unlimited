"""Whole-field profile ownership without implicit class-mechanic inheritance."""

from copy import deepcopy
from typing import Any


def profile_catalogs(pack, field_types):
    catalogs = pack.get('profile_catalogs', {})
    if not isinstance(catalogs, dict) or len(catalogs) > 1000:
        raise ValueError('Profile catalogs require a bounded mapping')
    for identity, catalog in catalogs.items():
        if (not isinstance(identity, str) or not identity or not isinstance(catalog, dict) or
                set(catalog) != {'field', 'value', 'source'} or
                not isinstance(catalog['field'], str) or field_types.get(catalog['field']) is not dict or
                not isinstance(catalog['value'], dict) or 'catalog_ref' in catalog['value']):
            raise ValueError('Invalid shared profile catalog')
        source = catalog['source']
        if (not isinstance(source, dict) or any(not isinstance(source.get(key), str) or
                not source[key].strip() for key in ('book', 'section'))):
            raise ValueError('Shared profile catalogs need book and section evidence')
    return catalogs


def resolve_profile_field(field, value, catalogs):
    if not isinstance(value, dict) or 'catalog_ref' not in value:
        return deepcopy(value)
    if (set(value) != {'catalog_ref', 'values'} or not isinstance(value['catalog_ref'], str) or
            value['catalog_ref'] not in catalogs or not isinstance(value['values'], dict)):
        raise ValueError('Invalid or missing shared profile catalog reference')
    catalog = catalogs[value['catalog_ref']]
    if catalog['field'] != field or set(catalog['value']).intersection(value['values']):
        raise ValueError('Profile references must match their field and preserve catalog-owned keys')
    return {**deepcopy(catalog['value']), **deepcopy(value['values'])}


def compose_owned_profile(pack, identifier, field_types):
    if pack.get('class_profile_format') != 'owned-v1':
        raise ValueError('Unsupported class profile ownership format')
    catalogs = profile_catalogs(pack, field_types)
    profiles = pack.get('class_profiles')
    default = pack.get('default_class')
    if (not isinstance(profiles, dict) or not 1 <= len(profiles) <= 1000 or
            not isinstance(default, str) or default not in profiles):
        raise ValueError('Owned profiles require an explicit default profile')
    resolved: dict[str, dict[str, Any]] = {}
    for identity, profile in profiles.items():
        if not isinstance(identity, str) or not identity or not isinstance(profile, dict):
            raise ValueError('Owned profiles require stable identities and mappings')
        missing = set(field_types) - set(profile)
        unknown = set(profile) - set(field_types)
        if missing or unknown:
            raise ValueError(identity + ' profile fields: missing ' + ', '.join(sorted(missing)) +
                             '; unsupported ' + ', '.join(sorted(unknown)))
        resolved[identity] = {}
        for field, expected_type in field_types.items():
            value = resolve_profile_field(field, profile[field], catalogs)
            if (not isinstance(value, expected_type) or
                    (expected_type is str and not value.strip())):
                raise ValueError(identity + ' profile has invalid ' + field)
            resolved[identity][field] = value
    if identifier not in profiles:
        raise ValueError('The pinned rules do not support this character class')
    shared = {key: deepcopy(value) for key, value in pack.items() if key not in field_types}
    return {**shared, 'class_profiles': resolved, **deepcopy(resolved[identifier])}
