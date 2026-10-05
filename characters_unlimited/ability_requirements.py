"""Declarative requirement evidence independent of game and option family."""

from copy import deepcopy
from .option_selectors import select_options
from .recorded_formulas import MAX_INTEGER


def compile_ability_requirements(definition, catalogs, attribute_names):
    rows = definition.get('requirements', [])
    if not isinstance(rows, list) or len(rows) > 100:
        raise ValueError('Ability requirements require a bounded list')
    result, seen = [], set()
    kinds = {'minimum_level', 'attribute_minimum', 'selected_options'}
    for row in rows:
        if (not isinstance(row, dict) or not {'id', 'name', 'source'} <= set(row) or
                len(set(row) & kinds) != 1 or set(row) - {'id', 'name', 'source'} - kinds or
                any(not isinstance(row.get(key), str) or not row[key].strip() for key in ('id', 'name')) or
                row['id'] in seen):
            raise ValueError('Ability requirements need distinct identities and one supported condition')
        seen.add(row['id'])
        source = row['source']
        if (not isinstance(source, dict) or any(not isinstance(source.get(key), str) or
                not source[key].strip() for key in ('book', 'section'))):
            raise ValueError('Ability requirements need book and section evidence')
        compiled = deepcopy(row)
        if 'minimum_level' in row:
            if type(row['minimum_level']) is not int or not 1 <= row['minimum_level'] <= 1000:
                raise ValueError('Ability requirements need a supported minimum level')
            compiled['text'] = 'level at least ' + str(row['minimum_level'])
        elif 'attribute_minimum' in row:
            condition = row['attribute_minimum']
            if (not isinstance(condition, dict) or set(condition) != {'attribute', 'value'} or
                    not isinstance(condition['attribute'], str) or condition['attribute'] not in attribute_names or
                    type(condition['value']) is not int or not 0 <= condition['value'] <= MAX_INTEGER):
                raise ValueError('Ability requirements need a known attribute and exact minimum')
            compiled['text'] = condition['attribute'] + ' at least ' + str(condition['value'])
        else:
            condition = row['selected_options']
            if (not isinstance(condition, dict) or set(condition) != {'catalog', 'selector', 'minimum'} or
                    not isinstance(condition['catalog'], str) or condition['catalog'] not in catalogs or
                    type(condition['minimum']) is not int or not 1 <= condition['minimum'] <= 1000):
                raise ValueError('Ability requirements need a known catalog and bounded minimum')
            compiled['option_ids'] = select_options(condition['selector'], catalogs[condition['catalog']])
            compiled['text'] = 'at least ' + str(condition['minimum']) + ' selected option(s) in ' + condition['catalog']
        result.append(compiled)
    return result


def project_ability_requirements(requirements, *, level, attributes, selections):
    if type(level) is not int or not 1 <= level <= 1000:
        raise ValueError('Ability requirements need a supported current level')
    result = []
    for row in requirements:
        if 'minimum_level' in row:
            actual = level
            minimum = row['minimum_level']
        elif 'attribute_minimum' in row:
            condition = row['attribute_minimum']
            actual = attributes[condition['attribute']]
            if type(actual) is not int or not -MAX_INTEGER <= actual <= MAX_INTEGER:
                raise ValueError('Ability requirement attributes must be exact whole numbers')
            minimum = condition['value']
        else:
            condition = row['selected_options']
            chosen = selections[condition['catalog']]
            if (not isinstance(chosen, list) or len(chosen) > 1000 or
                    any(not isinstance(item, str) for item in chosen)):
                raise ValueError('Ability requirements need selected option identities')
            actual = len(set(chosen).intersection(row['option_ids']))
            minimum = condition['minimum']
        result.append({'id': row['id'], 'name': row['name'], 'source': deepcopy(row['source']),
                       'satisfied': actual >= minimum, 'actual': actual,
                       'text': row['name'] + ': ' + row['text'] + '; current ' + str(actual)})
    return result
