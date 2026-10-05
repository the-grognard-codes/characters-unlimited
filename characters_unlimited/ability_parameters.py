"""Source-bound ability quantities and guidance, independent of game and family."""

from copy import deepcopy
from .recorded_formulas import MAX_INTEGER


def project_ability_parameters(definition, level):
    rows = definition.get('parameters', [])
    if type(level) is not int or not 1 <= level <= 1000:
        raise ValueError('Ability parameters require a supported experience level')
    if not isinstance(rows, list) or len(rows) > 100:
        raise ValueError('Ability parameters require a bounded list')
    seen = set()
    result = []
    for row in rows:
        if (not isinstance(row, dict) or set(row) not in
                ({'id', 'name', 'source', 'text'}, {'id', 'name', 'source', 'quantity'}) or
                any(not isinstance(row.get(key), str) or not row[key].strip() for key in ('id', 'name')) or
                row['id'] in seen):
            raise ValueError('Ability parameters require distinct identities and supported values')
        seen.add(row['id'])
        source = row['source']
        if (not isinstance(source, dict) or any(not isinstance(source.get(key), str) or
                not source[key].strip() for key in ('book', 'section'))):
            raise ValueError('Ability parameters need book and section evidence')
        projected = {'id': row['id'], 'name': row['name'], 'source': deepcopy(source)}
        if 'text' in row:
            if not isinstance(row['text'], str) or not row['text'].strip():
                raise ValueError('Literal ability guidance must be nonempty text')
            text = row['text']
        else:
            quantity = row['quantity']
            if (not isinstance(quantity, dict) or not {'base', 'per_level', 'unit'} <= set(quantity) or
                    set(quantity) - {'base', 'per_level', 'unit', 'level_origin'} or
                    any(type(quantity[key]) is not int or not 0 <= quantity[key] <= MAX_INTEGER
                        for key in ('base', 'per_level')) or
                    type(quantity.get('level_origin', 0)) is not int or quantity.get('level_origin', 0) not in (0, 1) or
                    not isinstance(quantity['unit'], str) or not quantity['unit'].strip()):
                raise ValueError('Unsupported level-scaled ability quantity')
            value = quantity['base'] + quantity['per_level'] * (level - quantity.get('level_origin', 0))
            if not 0 <= value <= MAX_INTEGER:
                raise ValueError('Ability parameter exceeds the exact integer range')
            projected.update(value=value, unit=quantity['unit'])
            text = str(value) + ' ' + quantity['unit']
        projected['text'] = row['name'] + ': ' + text
        result.append(projected)
    return result
