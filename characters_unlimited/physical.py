"""Recorded Physical-skill bonuses from reviewed, pinned skill definitions."""

from copy import deepcopy

from .attribute_modifiers import attribute_value


def _definitions(pack):
    return {skill['id']: skill for skill in pack['skills'] if skill.get('kind') == 'physical'}


def _active_ids(selections, definitions):
    return list(dict.fromkeys(item['skill_id'] for item in selections
                              if item['skill_id'] in definitions))


def _formula(formula):
    if not isinstance(formula, dict) or set(formula) != {'count', 'sides', 'bonus'}:
        raise ValueError('Unsupported Physical skill bonus formula')
    count, sides, bonus = formula['count'], formula['sides'], formula['bonus']
    if (type(count) is not int or not 0 <= count <= 1000 or
            type(sides) is not int or sides < 0 or (count and not 1 <= sides <= 1000) or
            type(bonus) is not int):
        raise ValueError('Unsupported Physical skill bonus formula')
    return count, sides, bonus


def _effects(definition):
    for group in ('attributes', 'resources'):
        for name, formula in definition.get(group, {}).items():
            yield group, name, formula


def _roll_key(group, name):
    return ('attribute' if group == 'attributes' else 'resource') + ':' + name


def _validate_acquisitions(acquisitions, definitions):
    if not isinstance(acquisitions, dict) or set(acquisitions) - definitions.keys():
        raise ValueError('Unknown Physical skill acquisition')
    for identifier, acquisition in acquisitions.items():
        if not isinstance(acquisition, dict) or set(acquisition) != {'rolls'} or not isinstance(acquisition['rolls'], dict):
            raise ValueError('Invalid Physical skill acquisition')
        expected = {}
        for group, name, formula in _effects(definitions[identifier]):
            count, sides, _ = _formula(formula)
            if count:
                expected[_roll_key(group, name)] = (count, sides)
        rolls = acquisition['rolls']
        if set(rolls) != expected.keys():
            raise ValueError('Physical skill rolls do not match pinned rules')
        for key, (count, sides) in expected.items():
            faces = rolls[key]
            if (not isinstance(faces, list) or len(faces) != count or
                    any(type(face) is not int or not 1 <= face <= sides for face in faces)):
                raise ValueError('Invalid Physical skill die face')


def _effect_value(formula, acquisition, group, name):
    count, _, bonus = _formula(formula)
    rolls = acquisition['rolls'][_roll_key(group, name)] if count else []
    return sum(rolls) + bonus, rolls


def _expected_modifiers(active, acquisitions, definitions):
    expected: dict[str, dict] = {}
    for identifier in active:
        definition = definitions[identifier]
        for name, formula in definition.get('attributes', {}).items():
            value, rolls = _effect_value(formula, acquisitions[identifier], 'attributes', name)
            expected.setdefault(name, {})['physical:' + identifier] = {
                'id': 'physical:' + identifier, 'value': value, 'rolls': deepcopy(rolls),
                'source': deepcopy(definition['source']),
            }
    return expected


def _physical_modifier(item):
    return isinstance(item, dict) and isinstance(item.get('id'), str) and item['id'].startswith('physical:')


def acquire_physical(character, selections, pack, die):
    """Acquire missing rolls and synchronize active Physical attribute bonuses."""
    definitions = _definitions(pack)
    active = _active_ids(selections, definitions)
    acquisitions = deepcopy(character.get('physical_acquisitions', {}))
    _validate_acquisitions(acquisitions, definitions)
    for identifier in active:
        if identifier in acquisitions:
            continue
        rolls = {}
        for group, name, formula in _effects(definitions[identifier]):
            count, sides, _ = _formula(formula)
            if count:
                faces = []
                for _ in range(count):
                    face = die(sides)
                    if type(face) is not int or not 1 <= face <= sides:
                        raise ValueError('Dice source returned an invalid Physical skill value')
                    faces.append(face)
                rolls[_roll_key(group, name)] = faces
        acquisitions[identifier] = {'rolls': rolls}
    expected = _expected_modifiers(active, acquisitions, definitions)
    attributes = deepcopy(character['attributes'])
    for name, record in attributes.items():
        retained = [item for item in record.get('modifiers', []) if not _physical_modifier(item)]
        additions = list(expected.get(name, {}).values())
        if retained or additions or 'modifiers' in record:
            record['modifiers'] = [*retained, *additions]
        record['value'] = attribute_value(record)
    return {'physical_acquisitions': acquisitions, 'attributes': attributes}


def validate_physical(character, pack):
    """Reject altered acquisitions and Physical modifiers on a saved character."""
    definitions = _definitions(pack)
    active = _active_ids(character.get('skill_selections', []), definitions)
    acquisitions = character.get('physical_acquisitions', {})
    _validate_acquisitions(acquisitions, definitions)
    if any(identifier not in acquisitions for identifier in active):
        raise ValueError('Missing Physical skill acquisition')
    validate_physical_history(character['attributes'], acquisitions, pack)
    expected = _expected_modifiers(active, acquisitions, definitions)
    for name, record in character['attributes'].items():
        actual = [item for item in record.get('modifiers', []) if _physical_modifier(item)]
        required = expected.get(name, {})
        if len(actual) != len(required) or any(item != required.get(item['id']) for item in actual):
            raise ValueError('Physical attribute modifiers do not match pinned rules')
    if set(expected) - character['attributes'].keys():
        raise ValueError('Missing attribute for Physical skill bonus')


def validate_physical_history(attributes, acquisitions, pack):
    """Validate present Physical modifiers in a full or partial attribute snapshot."""
    definitions = _definitions(pack)
    _validate_acquisitions(acquisitions, definitions)
    for name, record in attributes.items():
        seen = set()
        for item in record.get('modifiers', []):
            if not _physical_modifier(item):
                continue
            identifier = item['id'][len('physical:'):]
            if (identifier in seen or identifier not in definitions or
                    identifier not in acquisitions or
                    name not in definitions[identifier].get('attributes', {})):
                raise ValueError('Unknown or duplicate historical Physical modifier')
            seen.add(identifier)
            expected = _expected_modifiers([identifier], acquisitions, definitions)[name][item['id']]
            if item != expected:
                raise ValueError('Historical Physical modifier does not match pinned rules')


def project_physical(character, pack):
    """Project active bonuses without rolling or inventing resource baselines."""
    definitions = _definitions(pack)
    active = _active_ids(character.get('skill_selections', []), definitions)
    acquisitions = character.get('physical_acquisitions', {})
    selected, resources, sources = [], [], []
    combat: dict[str, dict] = {}
    for identifier in active:
        definition = definitions[identifier]
        source = definition['source']
        effects = {'attributes': {}, 'resources': {}, 'combat': dict(definition.get('combat', {}))}
        for group, name, formula in _effects(definition):
            value, rolls = _effect_value(formula, acquisitions[identifier], group, name)
            effects[group][name] = {'value': value, 'rolls': deepcopy(rolls)}
            if group == 'resources':
                resources.append({'skill_id': identifier, 'name': definition['name'],
                                  'resource': name, 'value': value, 'rolls': deepcopy(rolls),
                                  'source': deepcopy(source)})
        for stat, bonus in effects['combat'].items():
            combat.setdefault(stat, {})[definition['name']] = bonus
        selection = next(item for item in character.get('skill_selections', []) if item['skill_id'] == identifier)
        selected.append({**deepcopy(definition), **deepcopy(selection), 'effects': effects})
        if source not in sources:
            sources.append(deepcopy(source))
    return {'selected': selected, 'resources': resources, 'combat': combat, 'sources': sources}
