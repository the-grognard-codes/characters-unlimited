"""Recorded Physical-skill bonuses from reviewed, pinned skill definitions."""

from copy import deepcopy
import json

from .attribute_modifiers import attribute_value
from .grants import resolve_grants
from .recorded_formulas import validate_formula, formula_value
from .retained_acquisitions import validate_cached_acquisitions, acquire_selected


# Activity decimals travel through JSON and browser numbers. Larger manual
# attributes remain saved, but are not safely representable in this projection.
MAX_ACTIVITY_ATTRIBUTE = 9_007_199_254_740_991


def validate_physical_upgrade(character, previous, target, *, entire_definition=False):
    """Preserve receipts; Rifts still previews non-acquisition activity changes."""
    before = _definitions(previous)
    after = _definitions(target)
    fields = ('kind', 'attributes', 'resources', 'combat', 'source')
    for identifier in character.get('physical_acquisitions', {}):
        old = before.get(identifier, {})
        new = after.get(identifier, {})
        encoded = lambda row: json.dumps(row if entire_definition else {key:row.get(key) for key in fields}, sort_keys=True,
                                        ensure_ascii=False, allow_nan=False)
        if not old or not new or encoded(old) != encoded(new):
            raise ValueError('This update changes recorded Physical bonus rules. Acquisition/history migration is not yet supported; current rules remain intact.')


def _definitions(pack):
    return {skill['id']: skill for skill in pack['skills'] if skill.get('kind') == 'physical'}


def _grant_ids(pack, definitions):
    return resolve_grants(pack.get('physical_grants', []), list(definitions.values()))


def _active_ids(selections, definitions, grants=()):
    return list(dict.fromkeys([*grants, *(item['skill_id'] for item in selections
                              if item['skill_id'] in definitions)]))


def _formula(formula):
    if (not isinstance(formula, dict) or not {'count', 'sides', 'bonus'} <= set(formula) or
            set(formula) - {'count', 'sides', 'bonus', 'multiplier'}):
        raise ValueError('Unsupported Physical skill bonus formula')
    result = {('constant' if key == 'bonus' else key):value for key,value in formula.items()}
    validate_formula(result)
    return result


def _effects(definition):
    for group in ('attributes', 'resources'):
        for name, formula in definition.get(group, {}).items():
            yield group, name, formula


def _roll_key(group, name):
    return ('attribute' if group == 'attributes' else 'resource') + ':' + name


def _acquisition_catalog(definitions):
    return {identifier: {_roll_key(group, name): _formula(formula)
                        for group, name, formula in _effects(definition)}
            for identifier, definition in definitions.items()}


def _validate_acquisitions(acquisitions, definitions):
    validate_cached_acquisitions(_acquisition_catalog(definitions), acquisitions, record_constants=False)


def _effect_value(formula, acquisition, group, name):
    numeric = _formula(formula)
    rolls = acquisition['rolls'][_roll_key(group, name)] if numeric['count'] else []
    return formula_value(numeric, rolls), rolls


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
    active = _active_ids(selections, definitions, _grant_ids(pack, definitions))
    acquisitions = acquire_selected(_acquisition_catalog(definitions),
        character.get('physical_acquisitions', {}), active, die, record_constants=False)
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
    active = _active_ids(character.get('skill_selections', []), definitions,
                         _grant_ids(pack, definitions))
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
    grants = _grant_ids(pack, definitions)
    active = _active_ids(character.get('skill_selections', []), definitions, grants)
    acquisitions = character.get('physical_acquisitions', {})
    _validate_acquisitions(acquisitions, definitions)
    if any(identifier not in acquisitions for identifier in active):
        raise ValueError('Missing Physical skill acquisition')
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
        selection = next((item for item in character.get('skill_selections', [])
                          if item['skill_id'] == identifier), {'skill_id': identifier})
        projected = {**deepcopy(definition), **deepcopy(selection), 'effects': effects}
        if identifier in grants:
            projected['grant'] = True
        if 'activities' in definition:
            projected['activities'] = (_swimming_activities(character, definition['activities'])
                if set(definition['activities']) == {'swimming'} else _running_activities(character, definition['activities']))
        selected.append(projected)
        if source not in sources:
            sources.append(deepcopy(source))
    return {'selected': selected, 'resources': resources, 'combat': combat, 'sources': sources}


def _swimming_activities(character, rules):
    swimming = rules['swimming']
    fields = {'yards_per_ps', 'meters_per_ps', 'minutes_per_pe'}
    if (not isinstance(swimming, dict) or set(swimming) != fields
            or any(type(value) is not int or not 1 <= value <= 1000 for value in swimming.values())):
        raise ValueError('Invalid Swimming activity rules')
    ps, pe = character['attributes']['PS']['value'], character['attributes']['PE']['value']
    ps_supported = 0 < ps <= MAX_ACTIVITY_ATTRIBUTE/max(swimming['yards_per_ps'], swimming['meters_per_ps'])
    pe_supported = 0 < pe <= MAX_ACTIVITY_ATTRIBUTE/swimming['minutes_per_pe']
    return [{'id':'surface-swimming', 'name':'Surface swimming',
             'yards_per_melee':ps*swimming['yards_per_ps'] if ps_supported else None,
             'meters_per_melee':ps*swimming['meters_per_ps'] if ps_supported else None,
             'minutes':pe*swimming['minutes_per_pe'] if pe_supported else None,
             'guidance':'Routine pace until fatigue; distance uses current effective P.S., duration uses current effective P.E.' if ps_supported and pe_supported
                        else 'Positive effective P.S. and P.E. within the supported numeric range are needed for Swimming limits.'}]


def _running_activities(character, rules):
    if not isinstance(rules, dict) or set(rules) != {'running'}:
        raise ValueError('Unsupported Physical activity rules')
    running = rules['running']
    fields = {'half_speed_miles_per_pe','half_speed_kilometers_per_pe','maximum_speed_distance_divisor'}
    if (not isinstance(running, dict) or set(running) != fields
            or any(type(value) not in (int,float) or not 0 < value <= 1000
                   for value in running.values())):
        raise ValueError('Invalid Running activity rules')
    pe = character['attributes']['PE']['value']
    speed = character['attributes']['SPD']['value']
    supported = 0 < pe <= MAX_ACTIVITY_ATTRIBUTE and 0 < speed <= MAX_ACTIVITY_ATTRIBUTE
    return [{'id':identifier, 'name':name,
             'speed_attribute':speed * fraction if supported else None,
             'miles':pe * running['half_speed_miles_per_pe'] / divisor if supported else None,
             'kilometers':pe * running['half_speed_kilometers_per_pe'] / divisor if supported else None,
             'guidance':'Running routine limit from current effective P.E. and Spd.' if supported
                        else 'Positive effective P.E. and Spd within the supported numeric range are needed to calculate Running limits.'}
            for identifier,name,fraction,divisor in (
                ('half-speed','Running at half speed',0.5,1),
                ('maximum-speed','Running at maximum speed',1,running['maximum_speed_distance_divisor']))]
