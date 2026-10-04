"""Resolve declarative grants without choosing acquisition timing or effects."""

from .option_selectors import select_options


def resolve_grants(grants, catalog):
    if not isinstance(grants, list) or len(grants) > 1000:
        raise ValueError('Fixed grants require a bounded declaration list')
    identities = []
    for grant in grants:
        if isinstance(grant, str):
            identities.append(grant)
        elif not isinstance(grant, dict) or set(grant) != {'selector'}:
            raise ValueError('Fixed grants require identities or selector declarations')
    explicit = list(dict.fromkeys(identities))
    select_options({'any_of': [{'ids': explicit}]}, catalog)
    resolved: list[str] = []
    for grant in grants:
        resolved.extend([grant] if isinstance(grant, str) else select_options(grant['selector'], catalog))
    return list(dict.fromkeys(resolved))
