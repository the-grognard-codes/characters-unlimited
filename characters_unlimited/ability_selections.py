"""Game-neutral ability choices with source-bound, retained acquisitions.

Adapters own archive pins and character persistence. This boundary owns ordinary
selection accounting, descriptive projections and additive skill contributions.
"""

from copy import deepcopy
import hashlib

from .ability_parameters import project_ability_parameters
from .ability_requirements import compile_ability_requirements, project_ability_requirements
from .option_selectors import select_options
from .portability import canonical
from .recorded_formulas import formula_value, MAX_INTEGER
from .retained_acquisitions import acquire_selected, validate_cached_acquisitions
from .selection_groups import validate_group, project_group
from .skill_effects import compile_skill_effects


def _source(source):
    if (not isinstance(source, dict) or any(not isinstance(source.get(key), str) or
            not source[key].strip() for key in ('book', 'section'))):
        raise ValueError('Ability selections need book and section evidence')


def _rows(rows, label):
    if not isinstance(rows, list) or len(rows) > 1000:
        raise ValueError(label + ' require a bounded list')
    seen = set()
    for row in rows:
        if (not isinstance(row, dict) or any(not isinstance(row.get(key), str) or
                not row[key].strip() for key in ('id', 'name')) or row['id'] in seen):
            raise ValueError(label + ' require distinct identities and names')
        seen.add(row['id'])
        _source(row.get('source'))


def _compile(pack, game, skill_catalog, attribute_names):
    if (not isinstance(attribute_names, dict) or any(not isinstance(key, str) or not key.strip() or
            type(value) is not int or abs(value) > MAX_INTEGER
            for key, value in attribute_names.items())):
        raise ValueError('Ability context needs exact named attribute values')
    if (not isinstance(pack, dict) or set(pack) !=
            {'id', 'version', 'game', 'format', 'options', 'groups'} or
            any(not isinstance(pack[key], str) or not pack[key].strip()
                for key in ('id', 'version', 'game')) or pack['game'] != game or
            game not in ('rifts', 'heroes-unlimited') or pack['format'] != 'abilities-v1'):
        raise ValueError('Ability catalog needs a supported game and format')
    options, groups = pack['options'], pack['groups']
    _rows(options, 'Ability options')
    _rows(groups, 'Ability groups')
    # Even unused external catalogs and option metadata are checked by selectors.
    select_options({'any_of': [{'ids': []}]}, skill_catalog)
    select_options({'any_of': [{'ids': []}]}, options)
    catalogs = {'abilities': options, 'skills': skill_catalog}
    compiled_options, formulas = {}, {}
    for option in options:
        if (not {'id', 'name', 'source', 'description'} <= set(option) or
                set(option) - {'id', 'name', 'source', 'description', 'category', 'tags',
                    'parameters', 'requirements', 'acquisition_formulas', 'skill_effects'} or
                not isinstance(option['description'], str) or not option['description'].strip()):
            raise ValueError('Ability options need supported descriptive declarations')
        # Upper supported level catches unsafe per-level quantities before any dice.
        project_ability_parameters(option, 1)
        project_ability_parameters(option, 1000)
        requirements = compile_ability_requirements(option, catalogs, attribute_names)
        effects = compile_skill_effects(option.get('skill_effects', []), skill_catalog)
        formulas[option['id']] = option.get('acquisition_formulas', {})
        compiled_options[option['id']] = {'definition': option, 'requirements': requirements,
                                          'skill_effects': effects}
    validate_cached_acquisitions(formulas, {})
    compiled_groups = []
    for group in groups:
        if (not {'id', 'name', 'source', 'count', 'selector'} <= set(group) or
                set(group) - {'id', 'name', 'source', 'count', 'selector', 'costs'}):
            raise ValueError('Ability groups need supported selector allowances')
        allowance = {'count': group['count'],
                     'option_ids': select_options(group['selector'], options)}
        if 'costs' in group:
            allowance['costs'] = group['costs']
        validate_group(allowance)
        compiled_groups.append({'definition': group, 'allowance': allowance})
    pin = {'id': pack['id'], 'version': pack['version'], 'game': game,
           'sha256': hashlib.sha256(canonical({'pack': pack, 'skills': skill_catalog})).hexdigest()}
    return compiled_options, compiled_groups, formulas, pin


def _validate_state(state, formulas, pin):
    if state is None:
        return {'pin': deepcopy(pin), 'selections': [], 'acquisitions': {}}
    if (not isinstance(state, dict) or set(state) != {'pin', 'selections', 'acquisitions'} or
            state['pin'] != pin):
        raise ValueError('Ability state must match its exact game and catalog content')
    selections = state['selections']
    _validate_selections(selections, formulas)
    validate_cached_acquisitions(formulas, state['acquisitions'])
    if set(selections) - set(state['acquisitions']):
        raise ValueError('Selected abilities need retained acquisition receipts')
    return deepcopy(state)


def _validate_selections(selections, formulas):
    if (not isinstance(selections, list) or len(selections) > 1000 or
            any(not isinstance(item, str) or item not in formulas for item in selections) or
            len(set(selections)) != len(selections)):
        raise ValueError('Ability selections must be distinct known identities')


def _project(options, groups, selections, level, attributes, skill_catalog, skill_selections):
    if type(level) is not int or not 1 <= level <= 1000:
        raise ValueError('Ability selections need a supported current level')
    _validate_selections(skill_selections, {row['id']: {} for row in skill_catalog})
    active, effects = [], []
    selected_catalogs = {'abilities': selections, 'skills': skill_selections}
    for identifier in selections:
        compiled = options[identifier]
        definition = compiled['definition']
        requirements = project_ability_requirements(compiled['requirements'], level=level,
            attributes=attributes, selections=selected_catalogs)
        active.append({'id': identifier, 'name': definition['name'],
            'description': definition['description'], 'source': deepcopy(definition['source']),
            'parameters': project_ability_parameters(definition, level), 'requirements': requirements})
        # Option namespace prevents identically named effects from different powers colliding.
        for effect in compiled['skill_effects']:
            effects.append({**deepcopy(effect), 'id': canonical([identifier, effect['id']]).decode('utf-8')})
    for skill in skill_catalog:
        total = sum(effect['amount'] for effect in effects if skill['id'] in effect['skill_ids'])
        if abs(total) > MAX_INTEGER:
            raise ValueError('Combined ability skill bonuses exceed the exact integer range')
    allowances = [{'id': group['definition']['id'], 'name': group['definition']['name'],
        'source': deepcopy(group['definition']['source']),
        **project_group(group['allowance'], selections)} for group in groups]
    return {'abilities': active, 'groups': allowances, 'skill_effects': effects}


def select_abilities(pack, state, selections, die, *, game, skill_catalog, level, attributes,
                     skill_selections=None):
    """Return new state; never mutate inputs or reroll removed/reselected options."""
    options, groups, formulas, pin = _compile(pack, game, skill_catalog, attributes)
    previous = _validate_state(state, formulas, pin)
    _validate_selections(selections, formulas)
    # Honor-system guidance and projected bounds are checked before acquisition.
    _project(options, groups, selections, level, attributes, skill_catalog,
             [] if skill_selections is None else skill_selections)
    acquired = acquire_selected(formulas, previous['acquisitions'], selections, die)
    return {'pin': pin, 'selections': list(selections), 'acquisitions': acquired}


def project_abilities(pack, state, *, game, skill_catalog, level, attributes, skill_selections=None):
    """Replay exact receipts and project common data for adapters, UI and sheets."""
    options, groups, formulas, pin = _compile(pack, game, skill_catalog, attributes)
    current = _validate_state(state, formulas, pin)
    result = _project(options, groups, current['selections'], level, attributes, skill_catalog,
                      [] if skill_selections is None else skill_selections)
    for option in result['abilities']:
        identifier = option['id']
        option['acquired_values'] = {key: formula_value(formula,
            current['acquisitions'][identifier]['rolls'][key])
            for key, formula in formulas[identifier].items()}
    return result
