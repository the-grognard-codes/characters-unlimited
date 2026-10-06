"""Source-bound class psychic paths and their single-reserve composition.

Core declarations own exact path dependencies. The fixed path owns retained
acquisitions; ordinary potential remains an independent, portable source.
"""

from copy import deepcopy
from .ability_paths import compile_paths, project_path, update_path
from .attribute_modifiers import ATTRIBUTE_NAMES


def _bindings(core):
    result = {}
    classes = core.get('classes', [])
    if not isinstance(classes, list) or len(classes) > 1000:
        raise ValueError('Class psychic bindings require a bounded class catalog')
    for definition in classes:
        if not isinstance(definition, dict):
            raise ValueError('Class psychic bindings require class declarations')
        if 'ability_path' not in definition:
            continue
        binding = definition['ability_path']
        if (core.get('game') != 'rifts' or not isinstance(binding, dict) or
                set(binding) != {'id', 'version'} or
                any(not isinstance(binding[key], str) or not binding[key].strip() for key in binding)):
            raise ValueError('Class psychic paths need exact source dependency identities')
        result[definition['id']] = binding
    return result


def preflight_entitlements(core, resolve):
    """Inspect every fixed dependency before any character acquisition dice."""
    context = {'game': core['game'], 'level': 1,
               'attributes': {key: {'value': 0} for key in ATTRIBUTE_NAMES}}
    result = {}
    for identifier, binding in _bindings(core).items():
        pack = resolve(binding['id'], binding['version'])
        if pack.get('format') not in ('ability-paths-v2', 'ability-paths-v3'):
            raise ValueError('Class psychic dependencies require a fixed source path')
        compile_paths(pack, context)
        result[identifier] = pack
    return result


def entitlement_dependencies(core):
    return list(_bindings(core).values())


def entitlement_pack(character, core, resolve):
    return preflight_entitlements(core, resolve).get(character['character_class'])


def acquire_entitlement(character, core, resolve, die):
    pack = entitlement_pack(character, core, resolve)
    if pack is None:
        return {}
    state = update_path(character, pack, None, die, categories=list(pack['categories']))
    return {'class_psionics': state, 'additional_rule_packs': {
        **character.get('additional_rule_packs', {}), pack['id']: pack['version']}}


def project_entitlement(character, core, resolve):
    pack = entitlement_pack(character, core, resolve)
    state = character.get('class_psionics')
    if pack is None:
        if state is not None:
            raise ValueError('This class has no source psychic entitlement')
        return None
    if (state is None or state.get('enabled') is not True or
            character.get('additional_rule_packs', {}).get(pack['id']) != pack['version']):
        raise ValueError('Class psychic entitlement requires its enabled exact source receipt')
    return project_path(character, pack, state)


def update_entitlement(character, core, resolve, die, *, selections=None):
    pack = entitlement_pack(character, core, resolve)
    if pack is None:
        raise ValueError('This class has no source psychic entitlement')
    state = character.get('class_psionics')
    if (state is None or state.get('enabled') is not True or
            character.get('additional_rule_packs', {}).get(pack['id']) != pack['version']):
        raise ValueError('Class psychic entitlement requires its original enabled source receipt')
    return update_path(character, pack, character['class_psionics'], die, selections=selections)


def restore_entitlement(current, restored):
    """Keep acquired dice for replay while restoring the prior power choices."""
    cache = current.get('class_psionics')
    if cache is None:
        return {}
    prior = restored.get('class_psionics')
    if prior is None or prior['pin'] != cache['pin']:
        raise ValueError('Class psychic history must preserve its original dependency')
    state = deepcopy(prior)
    state['gains'] = deepcopy(cache['gains'])
    state['abilities']['acquisitions'] = {
        **deepcopy(cache['abilities']['acquisitions']), **state['abilities']['acquisitions']}
    if 'learning_levels' in state:
        state['learning_levels'] = {**deepcopy(cache['learning_levels']), **state['learning_levels']}
    return {'class_psionics': state, 'additional_rule_packs': {
        **restored.get('additional_rule_packs', {}), state['pin']['id']: state['pin']['version']}}


def compose_psionics(natural, entitlement):
    """Retain both power origins; class status owns overlapping resource values."""
    if entitlement is None:
        return natural
    origins = []
    if natural.get('state') is not None:
        origins.append({'label': 'Natural psionics', 'view': deepcopy(natural)})
    origins.append({'label': 'Class psychic powers', 'view': deepcopy(entitlement)})
    resources = {**deepcopy(natural['resources']), **deepcopy(entitlement['resources'])}
    guidance = [
        'Class psychic status controls the single I.S.P. reserve and saving target. '
        'Natural powers are additional; their retained reserve is not added again.']
    effective = {'name': 'Psychic powers', 'path': entitlement['path'],
                 'state': deepcopy(entitlement['state']), 'fixed': True,
                 'abilities': [*deepcopy(entitlement['abilities']), *deepcopy(natural['abilities'])],
                 'resources': resources, 'save_target': entitlement['save_target'],
                 'guidance': guidance, 'origins': origins}
    return {**natural, 'class_entitlement': entitlement, 'effective': effective}
