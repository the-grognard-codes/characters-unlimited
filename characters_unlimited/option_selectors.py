"""Non-executable catalog criteria shared by rule families."""


def _identities(values):
    if (not isinstance(values, list) or len(values) > 1000 or
            any(not isinstance(value, str) or not value for value in values) or
            len(set(values)) != len(values)):
        raise ValueError('Selector criteria need distinct nonempty identities')


def select_options(selector, catalog):
    """Union include clauses; intersect fields within a clause; exclude last."""
    if (not isinstance(selector, dict) or 'any_of' not in selector or
            set(selector) - {'any_of', 'exclude_ids'}):
        raise ValueError('Invalid option selector')
    clauses = selector['any_of']
    if not isinstance(clauses, list) or not 1 <= len(clauses) <= 100:
        raise ValueError('Selectors need between one and 100 include clauses')
    references = set()
    for clause in clauses:
        if (not isinstance(clause, dict) or not clause or
                set(clause) - {'ids', 'categories', 'tags_any'}):
            raise ValueError('Unsupported selector criterion')
        for values in clause.values():
            _identities(values)
        references.update(clause.get('ids', []))
    excluded = selector.get('exclude_ids', [])
    _identities(excluded)
    references.update(excluded)
    if not isinstance(catalog, list) or len(catalog) > 1000:
        raise ValueError('Selectors require a bounded pinned catalog')
    identifiers = []
    for option in catalog:
        if not isinstance(option, dict):
            raise ValueError('Invalid selector catalog option')
        identifiers.append(option.get('id'))
        if not isinstance(option.get('category', ''), str):
            raise ValueError('Selector option categories must be text')
        _identities(option.get('tags', []))
    _identities(identifiers)
    missing = references - set(identifiers)
    if missing:
        raise ValueError('Selector references missing catalog options: ' + ', '.join(sorted(missing)))
    return [option['id'] for option in catalog if option['id'] not in excluded and any(
        ('ids' not in clause or option['id'] in clause['ids']) and
        ('categories' not in clause or option.get('category', '') in clause['categories']) and
        ('tags_any' not in clause or bool(set(option.get('tags', [])).intersection(clause['tags_any'])))
        for clause in clauses)]
