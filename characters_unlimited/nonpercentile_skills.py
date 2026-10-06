"""Source-bound ordinary training that has no intrinsic percentile."""


def training_definition(definition, catalog):
    if definition.get('kind') != 'training':
        return False
    allowed = {'id', 'name', 'kind', 'category', 'source', 'description', 'requires_specialty',
               'prerequisites', 'pending_prerequisites', 'catalog_skill_id'}
    if (not {'id', 'name', 'kind', 'source'} <= set(definition) or set(definition) - allowed or
            any(not isinstance(definition.get(key), str) or not definition[key].strip()
                for key in ('id', 'name')) or definition.get('requires_specialty', False) is not False):
        raise ValueError('Ordinary training needs supported identity fields without percentages or Physical effects')
    if ('category' in definition and (not isinstance(definition['category'], str) or not definition['category'].strip())):
        raise ValueError('Training category must be text')
    if ('description' in definition and (not isinstance(definition['description'], str) or
            not definition['description'].strip() or len(definition['description']) > 100000)):
        raise ValueError('Training description must be bounded source text')
    source = definition['source']
    if (not isinstance(source, dict) or any(not isinstance(source.get(key), str) or
            not source[key].strip() for key in ('book', 'section'))):
        raise ValueError('Ordinary training needs source evidence')
    known = {row['id']: row for row in catalog}
    if 'catalog_skill_id' in definition:
        identifier = definition['catalog_skill_id']
        if (not isinstance(identifier, str) or identifier not in known or
                known[identifier].get('kind') != 'training'):
            raise ValueError('Required training references must name ordinary training identities')
    groups = definition.get('prerequisites', [])
    if (not isinstance(groups, list) or len(groups) > 1000 or
            any(not isinstance(group, list) or not 1 <= len(group) <= 1000 or
                any(not isinstance(identifier, str) or identifier not in known for identifier in group)
                or len(set(group)) != len(group) for group in groups)):
        raise ValueError('Training prerequisites must name bounded known alternatives')
    pending = definition.get('pending_prerequisites', [])
    if (not isinstance(pending, list) or len(pending) > 1000 or
            any(not isinstance(text, str) or not text.strip() for text in pending)):
        raise ValueError('Pending training prerequisites must be bounded source notes')
    return True
