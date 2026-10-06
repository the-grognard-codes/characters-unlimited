"""Declarative percentile ability paths, retained resources and category guidance."""

from copy import deepcopy
import hashlib

from .ability_selections import select_abilities, project_abilities
from .ability_learning import validate_learning_rules, validate_learning_levels, project_learning
from .json_data import canonical
from .level_resource_gains import level_gain_definitions, level_gain_fields, validate_level_resource_gains
from .retained_acquisitions import validate_acquisition_catalog
from .resources import acquire_resources, validate_resource_rules, validate_resources, project_resources
from .selection_groups import project_group, validate_allowance, validate_group


def _no_die(sides):
    raise ValueError('Path preflight must not acquire dice')


def _source(row):
    source = row.get('source')
    if (not isinstance(source, dict) or any(not isinstance(source.get(key), str) or
            not source[key].strip() for key in ('book', 'section'))):
        raise ValueError('Ability paths need book and section evidence')


def _context(character):
    return {'game': character['game'], 'skill_catalog': [], 'level': character['level'],
            'attributes': {key: value['value'] for key, value in character['attributes'].items()}}


def compile_paths(pack, character):
    fixed = isinstance(pack, dict) and pack.get('format') in ('ability-paths-v2', 'ability-paths-v3')
    origin_field = 'fixed_path' if fixed else 'chance_table'
    if (not isinstance(pack, dict) or set(pack) != {'id', 'version', 'name', 'game', 'source',
            'format', 'categories', 'catalog', origin_field, 'skip_path', 'paths'} or
            pack['format'] not in ('ability-paths-v1', 'ability-paths-v2', 'ability-paths-v3') or pack['game'] != character['game'] or
            any(not isinstance(pack[key], str) or not pack[key].strip() for key in ('id', 'version', 'name'))):
        raise ValueError('Unsupported source-bound ability path catalog')
    _source(pack)
    categories = pack['categories']
    if (not isinstance(categories, list) or not 1 <= len(categories) <= 100 or
            any(not isinstance(item, str) or not item for item in categories) or len(set(categories)) != len(categories)):
        raise ValueError('Ability paths need distinct category identities')
    select_abilities(pack['catalog'], None, [], _no_die, **_context(character))
    for option in pack['catalog']['options']:
        if not option.get('tags') or set(option['tags']) - set(categories):
            raise ValueError('Path abilities must declare supported category memberships')
    if not isinstance(pack['paths'], list) or not 1 <= len(pack['paths']) <= 100:
        raise ValueError('Ability paths need a bounded declaration list')
    paths = {}
    learning = pack['format'] == 'ability-paths-v3'
    for row in pack['paths']:
        if (not isinstance(row, dict) or set(row) != {'id', 'name', 'source', 'save_target',
                'allowances', 'resources', 'growth'} | ({'known_abilities'} if learning else set()) or
                any(not isinstance(row[key], str) or not row[key].strip() for key in ('id', 'name')) or
                row['id'] in paths or type(row['save_target']) is not int or not 1 <= row['save_target'] <= 20):
            raise ValueError('Invalid ability path declaration')
        _source(row)
        allowances = row['allowances']
        if (not isinstance(allowances, dict) or not 1 <= len(allowances) <= 100 or
                any(not isinstance(key, str) or not key for key in allowances)):
            raise ValueError('Ability path modes need named allowances')
        for allowance in allowances.values():
            required = {'count', 'minimum_categories', 'maximum_categories'}
            if (not isinstance(allowance, dict) or not required <= set(allowance) or
                    set(allowance) - (required | ({'costs', 'awards'} if learning else {'costs', 'milestones'} if fixed else set()))):
                raise ValueError('Invalid path category allowance')
            for key in required:
                validate_allowance(allowance[key])
            if not 0 <= allowance['minimum_categories'] <= allowance['maximum_categories'] <= len(categories):
                raise ValueError('Invalid path category range')
            if learning:
                if (allowance['count'] != 0 or allowance['minimum_categories'] != 0 or
                        allowance['maximum_categories'] != len(categories) or 'awards' not in allowance):
                    raise ValueError('Learning paths use explicit source awards, not scalar allowances')
                validate_learning_rules(pack, row, allowance)
            else:
                _selection_allowance(pack, allowance, 1000)
        resources = validate_resource_rules({'resources': row['resources']}) if row['resources'] is not None else {}
        level_gain_definitions({'resource_gains': row['growth']}, resources)
        validate_acquisition_catalog({'growth': {key: value['formula'] for key, value in row['growth'].items()}})
        paths[row['id']] = row
    if fixed:
        if (not isinstance(pack['fixed_path'], str) or pack['fixed_path'] not in paths or
                not isinstance(pack['skip_path'], str) or pack['skip_path'] not in paths):
            raise ValueError('Fixed ability paths need explicit known identities')
        return paths
    table = pack['chance_table']
    if not isinstance(table, list) or not 1 <= len(table) <= 100:
        raise ValueError('Ability paths need a bounded percentile table')
    prior = 0
    for row in table:
        if (not isinstance(row, dict) or set(row) != {'maximum', 'path'} or
                type(row['maximum']) is not int or not prior < row['maximum'] <= 100 or
                not isinstance(row['path'], str) or row['path'] not in paths):
            raise ValueError('Invalid path percentile outcome')
        prior = row['maximum']
    if prior != 100 or not isinstance(pack['skip_path'], str) or pack['skip_path'] not in paths:
        raise ValueError('Ability path table must cover every percentile outcome')
    if paths[pack['skip_path']]['resources'] is not None:
        raise ValueError('Skipped ability paths cannot generate resources')
    return paths


def _path(pack, paths, face):
    if pack['format'] in ('ability-paths-v2', 'ability-paths-v3'):
        if face is not None:
            raise ValueError('Fixed entitlements cannot contain a percentile receipt')
        return paths[pack['fixed_path']]
    if face is None:
        return paths[pack['skip_path']]
    if type(face) is not int or not 1 <= face <= 100:
        raise ValueError('Path potential must retain one valid percentile face')
    return paths[next(row['path'] for row in pack['chance_table'] if face <= row['maximum'])]


def _selection_allowance(pack, allowance, level):
    milestones = allowance.get('milestones', {})
    if (not isinstance(milestones, dict) or len(milestones) > 999 or
            any(not isinstance(key, str) or not key.isascii() or not key.isdigit() or
                str(int(key)) != key or not 2 <= int(key) <= 1000 or
                type(value) is not int or not 0 <= value <= 1000 for key, value in milestones.items())):
        raise ValueError('Ability choice milestones need exact supported levels and counts')
    count = allowance['count'] + sum(value for key, value in milestones.items() if int(key) <= level)
    group = {'count': count, 'option_ids': [row['id'] for row in pack['catalog']['options']]}
    if 'costs' in allowance:
        group['costs'] = allowance['costs']
    validate_group(group)
    return group


def _pin(pack):
    return {'id': pack['id'], 'version': pack['version'],
            'sha256': hashlib.sha256(canonical(pack)).hexdigest()}


def retain_path_growth(events, field, state):
    """Complete newly generated before-frames with the path's recorded gains."""
    for event in events:
        before = event['before']
        prior = before.get(field)
        if prior is not None and any(str(level) not in prior['gains'] for level in range(2, before['level'] + 1)):
            before[field] = {**deepcopy(prior), 'gains': deepcopy(state['gains'])}


def _validate(pack, paths, character, state, *, require_attained=True):
    if (not isinstance(state, dict) or set(state) != {'pin', 'face', 'enabled', 'mode', 'categories',
            'abilities', 'resource_record', 'gains'} |
            ({'learning_levels'} if pack['format'] == 'ability-paths-v3' else set()) or state['pin'] != _pin(pack) or
            type(state['enabled']) is not bool or not isinstance(state['abilities'], dict)):
        raise ValueError('Ability path state must replay exact pinned content')
    path = _path(pack, paths, state['face'])
    if not isinstance(state['mode'], str) or state['mode'] not in path['allowances']:
        raise ValueError('Select a supported ability path mode')
    categories = state['categories']
    if (not isinstance(categories, list) or len(categories) > len(pack['categories']) or
            any(not isinstance(item, str) or item not in pack['categories'] for item in categories) or
            len(set(categories)) != len(categories)):
        raise ValueError('Select distinct known ability categories')
    project_abilities(pack['catalog'], state['abilities'], **_context(character))
    if pack['format'] == 'ability-paths-v3':
        validate_learning_levels(state, path, character['level'])
    record = state['resource_record']
    if path['resources'] is None:
        if record is not None or state['gains']:
            raise ValueError('This ability path has no resource receipts')
    else:
        if not isinstance(record, dict) or set(record) != {'resources', 'resource_attribute_snapshot'}:
            raise ValueError('Path resources require recorded attribute contributions')
        validate_resources(record, {'resources': path['resources']})
    gains = state['gains']
    if (not isinstance(gains, dict) or len(gains) > 999 or
            any(not isinstance(key, str) or not key.isascii() or not key.isdigit() or
                str(int(key)) != key or not 2 <= int(key) <= 1000 for key in gains)):
        raise ValueError('Path growth must retain supported level identities')
    for receipt in gains.values():
        validate_level_resource_gains(receipt, {'resource_gains': path['growth']}, record['resources'])
    if path['resources'] is not None and state['enabled'] and require_attained:
        if any(str(level) not in gains for level in range(2, character['level'] + 1)):
            raise ValueError('Enabled path resources need every attained level contribution')
    return path


def update_path(character, pack, state, die, *, roll=False, enabled=True,
                selections=None, mode=None, categories=None):
    """Roll potential once; retain resources and choices through ordinary edits."""
    paths = compile_paths(pack, character)
    if type(roll) is not bool or type(enabled) is not bool:
        raise ValueError('Path potential and enabled choices must be boolean')
    if roll and pack['format'] in ('ability-paths-v2', 'ability-paths-v3'):
        raise ValueError('Fixed entitlements do not roll psychic potential')
    if state is not None:
        _validate(pack, paths, character, state, require_attained=False)
    previous = deepcopy(state)
    if roll and previous is not None and previous['face'] is not None:
        raise ValueError('Potential has already been rolled; its receipt is retained')
    # Validate all caller-controlled choices before the percentile draw.
    selected = selections if selections is not None else previous['abilities']['selections'] if previous else []
    learning = pack['format'] == 'ability-paths-v3'
    known = _path(pack, paths, None)['known_abilities'] if learning else []
    if learning:
        if not isinstance(selected, list):
            raise ValueError('Ability selections must be distinct known identities')
        # Keep duplicate caller choices visible to the shared validator.
        selected = [*known, *[key for key in selected if key not in known]]
        if previous and any(previous['learning_levels'].get(key, character['level']) > character['level']
                            for key in selected):
            raise ValueError('Selected abilities cannot be learned after the current level')
    select_abilities(pack['catalog'], previous['abilities'] if previous else None,
                     selected, lambda sides: 1, **_context(character))
    chosen_categories = categories if categories is not None else previous['categories'] if previous else []
    if (not isinstance(chosen_categories, list) or len(chosen_categories) > len(pack['categories']) or
            any(not isinstance(item, str) or item not in pack['categories'] for item in chosen_categories) or
            len(set(chosen_categories)) != len(chosen_categories)):
        raise ValueError('Select distinct known ability categories')
    if mode is not None and (not isinstance(mode, str) or
            not any(mode in path['allowances'] for path in paths.values())):
        raise ValueError('Select a supported ability path mode')
    if roll and mode is not None:
        raise ValueError('Roll potential before choosing a mode')
    if not roll and mode is not None and mode not in _path(pack, paths, previous['face'] if previous else None)['allowances']:
        raise ValueError('This potential does not support the selected mode')
    abilities = select_abilities(pack['catalog'], previous['abilities'] if previous else None,
                                selected, die, **_context(character))
    face = die(100) if roll else previous['face'] if previous else None
    path = _path(pack, paths, face)
    chosen_mode = mode if mode is not None else previous['mode'] if previous and not roll else next(iter(path['allowances']))
    if chosen_mode not in path['allowances']:
        raise ValueError('This potential does not support the selected mode')
    resources = previous['resource_record'] if previous else None
    gains = previous['gains'] if previous else {}
    if path['resources'] is not None and resources is None:
        resources = acquire_resources({'attributes': character['attributes']}, {'resources': path['resources']}, die)
    if enabled and resources is not None:
        for level in range(2, character['level'] + 1):
            key = str(level)
            gains[key] = level_gain_fields({'resource_gains': path['growth']}, resources['resources'],
                                           die, gains.get(key))
    result = {'pin': _pin(pack), 'face': face, 'enabled': enabled, 'mode': chosen_mode,
              'categories': list(chosen_categories), 'abilities': abilities,
              'resource_record': resources, 'gains': gains}
    if learning:
        levels = deepcopy(previous['learning_levels']) if previous else {}
        levels.update({key: 1 for key in known})
        for key in selected:
            levels.setdefault(key, character['level'])
        result['learning_levels'] = levels
    project_path(character, pack, result)
    return result


def project_path(character, pack, state):
    paths = compile_paths(pack, character)
    if state is None:
        return {'name': pack['name'], 'state': None, 'catalog': deepcopy(pack['catalog']['options']),
                'categories': list(pack['categories']), 'abilities': [], 'resources': {}, 'save_target': None}
    path = _validate(pack, paths, character, state)
    view = project_abilities(pack['catalog'], state['abilities'], **_context(character))
    allowance = path['allowances'][state['mode']]
    options = [option['id'] for option in pack['catalog']['options']
               if set(option['tags']).intersection(state['categories'])]
    unpartitioned = pack['format'] in ('ability-paths-v2', 'ability-paths-v3') and allowance['minimum_categories'] == 0
    if unpartitioned:
        options = [option['id'] for option in pack['catalog']['options']]
    learning = pack['format'] == 'ability-paths-v3'
    if learning:
        accounting = project_learning(pack, path, allowance, state, character['level'])
        options = [key for key in options if key not in path['known_abilities']]
        selection = {'count': sum(row['count'] for row in accounting['awards']), 'option_ids': options,
                     'costs': deepcopy(allowance.get('costs', {}))}
    else:
        selection = {**_selection_allowance(pack, allowance, character['level']), 'option_ids': options}
    if 'costs' in selection:
        selection['costs'] = {key: value for key, value in selection['costs'].items() if key in options}
    elective = [key for key in state['abilities']['selections']
                if not learning or key not in path['known_abilities']]
    group = project_group(selection, elective)
    category_count = len(state['categories'])
    guidance = [f"{group['remaining']} choices remaining; {category_count} categories selected "
                f"(expected {allowance['minimum_categories']}–{allowance['maximum_categories']})."]
    if unpartitioned:
        guidance = [f"{group['credited']} of {selection['count']} weighted choices used; {group['remaining']} remaining."]
    if group['outside']:
        guidance.append('Choices outside selected categories: ' + ', '.join(group['outside']))
    used_categories = {category for option in pack['catalog']['options']
                       if option['id'] in state['abilities']['selections'] for category in option['tags']}
    unused = [category for category in state['categories'] if category not in used_categories]
    if unused and not unpartitioned:
        guidance.append('Selected categories with no chosen powers: ' + ', '.join(unused))
    if learning:
        guidance = [f"{row['name']}: {row['credited']} of {row['count']} choices used; {row['remaining']} remaining."
                    for row in accounting['awards']]
        if accounting['unallocated']:
            guidance.append('Choices outside source learning awards: ' + ', '.join(accounting['unallocated']))
        definitions = {row['id']: row for row in pack['catalog']['options']}
        for ability in view['abilities']:
            learned = state['learning_levels'][ability['id']]
            ability['learned_level'] = learned
            for requirement in definitions[ability['id']].get('requirements', []):
                if 'minimum_level' in requirement and learned < requirement['minimum_level']:
                    guidance.append(f"{ability['name']} learned at level {learned}; source minimum learning level {requirement['minimum_level']}.")
    resources = {}
    if state['enabled'] and state['resource_record'] is not None:
        events = [{'level': int(key), **receipt} for key, receipt in state['gains'].items()
                  if 2 <= int(key) <= character['level']]
        record = {**state['resource_record'], 'level': character['level']}
        if events:
            first = next(row for row in events if row['level'] == 2)
            record.update(advancement={**first, 'active': True},
                          later_advancements=[row for row in events if row['level'] > 2])
        resources = project_resources(record, {'resources': path['resources']})['resources']
    return {'name': pack['name'], 'path': path['name'], 'state': deepcopy(state),
            'catalog': deepcopy(pack['catalog']['options']), 'categories': list(pack['categories']),
            'modes': list(path['allowances']), 'abilities': view['abilities'] if state['enabled'] and path['resources'] is not None else [],
            'resources': resources, 'save_target': path['save_target'] if state['enabled'] else paths[pack['skip_path']]['save_target'],
            'guidance': guidance, 'source': deepcopy(path['source']),
            **({'known_abilities': list(path['known_abilities']), 'learning_awards': accounting}
               if learning else {}),
            **({'selection_group': group, 'fixed': True, 'choice_costs': deepcopy(allowance.get('costs', {}))}
               if pack['format'] in ('ability-paths-v2', 'ability-paths-v3') else {})}
