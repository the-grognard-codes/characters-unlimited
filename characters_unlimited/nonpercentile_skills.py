"""Source-bound ordinary training that has no intrinsic percentile."""

from copy import deepcopy


def training_definition(definition, catalog):
    if definition.get('kind') != 'training':
        return False
    allowed = {'id', 'name', 'kind', 'category', 'source', 'description', 'requires_specialty',
               'prerequisites', 'pending_prerequisites', 'catalog_skill_id', 'proficiency_reference'}
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
    reference = definition.get('proficiency_reference')
    if 'proficiency_reference' in definition:
        if not isinstance(reference, dict) or set(reference) != {'options', 'source'}:
            raise ValueError('Referenced training proficiency needs options and source evidence')
        options = reference['options']
        if (not isinstance(options, list) or not 1 <= len(options) <= 1000 or
                any(not isinstance(key, str) or key not in known for key in options) or
                len(set(options)) != len(options)):
            raise ValueError('Referenced proficiency needs distinct known percentage skills')
        for key in options:
            target = known[key]
            if (target.get('kind') == 'training' or
                    target.get('requires_specialty', key == 'instrument') is not False or
                    any(type(target.get(field)) is not int or target[field] < 0
                        for field in ('base', 'per_level'))):
                raise ValueError('Training may reference only nonspecialty percentage skills')
        evidence = reference['source']
        if (not isinstance(evidence, dict) or any(not isinstance(evidence.get(key), str) or
                not evidence[key].strip() for key in ('book', 'section'))):
            raise ValueError('Referenced proficiency needs book and section evidence')
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


def project_training_references(grants, selected):
    """Borrow a learned primary once, without creating another numeric contribution."""
    available = [row for row in [*grants, *selected] if row.get('kind') != 'training'
                 and type(row.get('percentage')) is int]
    def project(row):
        reference = row.get('proficiency_reference')
        if row.get('kind') != 'training' or reference is None:
            return row
        options = set(reference['options'])
        candidates = [source for source in available
                      if source.get('catalog_skill_id', source['id']) in options]
        if not candidates:
            return row
        chosen = min(candidates, key=lambda source: (-source['percentage'],
            -source['uncapped_percentage'], source['id']))
        return {**row, 'percentage': chosen['percentage'],
                'uncapped_percentage': chosen['uncapped_percentage'], 'per_level': chosen['per_level'],
                'contributions': {'referenced_proficiency': chosen['uncapped_percentage']},
                'proficiency_origin': {'id': chosen['id'], 'name': chosen['name'],
                                       'source': deepcopy(reference['source'])},
                'description': row.get('description', '') + ' Uses current primary proficiency from ' + chosen['name'] + '.'}
    return [project(row) for row in grants], [project(row) for row in selected]
