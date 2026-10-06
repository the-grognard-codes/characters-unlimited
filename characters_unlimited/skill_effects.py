"""Declarative acquired-skill percentile effects shared by rule families."""

from copy import deepcopy
from .option_selectors import select_options
from .required_definitions import required_catalog
from .recorded_formulas import MAX_INTEGER


def skill_effect_catalog(pack):
    catalog = list(pack['skills'])
    required = required_catalog(pack)
    if required:
        catalog.extend(required['grants'])
        for group in required['groups']:
            catalog.extend(group.get('options', []))
            if 'skill' in group:
                catalog.append(group['skill'])
    unique: dict[str, dict] = {}
    for row in catalog:
        unique.setdefault(row['id'], row)
    return list(unique.values())


def compile_skill_effects(effects, catalog):
    if not isinstance(effects, list) or len(effects) > 100:
        raise ValueError('Skill effects require a bounded declaration list')
    result, identifiers = [], set()
    for effect in effects:
        if (not isinstance(effect, dict) or
                not {'id', 'name', 'operation', 'amount', 'selector', 'source'} <= set(effect) or
                set(effect) - {'id', 'name', 'operation', 'amount', 'selector', 'source', 'selection_pool'} or
                any(not isinstance(effect[key], str) or not effect[key].strip() for key in ('id', 'name')) or
                effect['id'] in identifiers or effect['operation'] != 'add' or
                type(effect['amount']) is not int or abs(effect['amount']) > MAX_INTEGER):
            raise ValueError('Unsupported additive skill effect declaration')
        if 'selection_pool' in effect and effect['selection_pool'] not in ('domestic', 'related', 'secondary'):
            raise ValueError('Skill effects must select a supported acquisition pool')
        source = effect['source']
        if (not isinstance(source, dict) or any(not isinstance(source.get(key), str) or
                not source[key].strip() for key in ('book', 'section'))):
            raise ValueError('Skill effects need book and section evidence')
        identifiers.add(effect['id'])
        result.append({**deepcopy(effect), 'skill_ids': select_options(effect['selector'], catalog)})
    return result


def pack_skill_effects(pack):
    return compile_skill_effects(pack.get('skill_effects', []), skill_effect_catalog(pack))


def matching_skill_effects(identifier, effects, *, selection_pool=None):
    return [{'id': effect['id'], 'name': effect['name'], 'value': effect['amount'],
             'source': deepcopy(effect['source'])}
            for effect in effects if identifier in effect['skill_ids'] and
            ('selection_pool' not in effect or effect['selection_pool'] == selection_pool)]
