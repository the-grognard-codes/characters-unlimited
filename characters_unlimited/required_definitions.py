"""Required percentile group schema and immutable legacy adaptation."""

from copy import deepcopy
import re
from .selection_groups import validate_group
from .skill_checks import independent_check_rules
from .nonpercentile_skills import training_definition


def required_selection_group(group):
    result = {'count': group['count'], 'option_ids': [item['id'] for item in group['options']],
              'costs': group.get('selection_costs', {})}
    validate_group(result)
    return result


def required_catalog(pack):
    rules = pack.get('required')
    if not rules:
        return None
    if 'format' not in rules:
        # Adapt immutable older packs without changing their saved definitions.
        grants = deepcopy(rules['grants'])
        for definition in grants:
            if definition['id'] == 'native-language':
                definition['specialty_from'] = 'native_language'
        rules = {'format':2, 'grants':grants, 'groups':[
            {'id':'native_language','name':'Native language','kind':'text','count':1},
            {'id':'other_languages','name':'Other languages','kind':'text-list',
             **deepcopy(rules['other_languages']), 'different_from':['native_language']},
            {'id':'pilot','name':'Pilot skill','kind':'select',**deepcopy(rules['pilot'])},
            {'id':'repair','name':'Repair or horsemanship','kind':'select',**deepcopy(rules['repair'])}]}
    else:
        rules = deepcopy(rules)
    if (type(rules.get('format')) is not int or rules['format'] != 2 or
            not isinstance(rules.get('grants'), list) or len(rules['grants']) > 1000 or
            not isinstance(rules.get('groups'), list) or len(rules['groups']) > 100):
        raise ValueError('Invalid required skill group rules')
    identifiers = set()
    for group in rules['groups']:
        if (not isinstance(group, dict) or not isinstance(group.get('id'), str) or
                re.fullmatch(r'[a-z][a-z0-9_-]*', group['id']) is None or group['id'] in identifiers or
                group.get('kind') not in ('text','text-list','select') or
                not isinstance(group.get('name'), str) or not group['name'] or
                type(group.get('count')) is not int or not 1 <= group['count'] <= 1000 or
                (group['kind'] == 'text' and group['count'] != 1)):
            raise ValueError('Invalid required skill choice group')
        identifiers.add(group['id'])
        if group['kind'] == 'select':
            options = group.get('options')
            if (not isinstance(options, list) or not 0 < len(options) <= 1000 or
                    any(not isinstance(item,dict) or not isinstance(item.get('id'),str) or not item['id'] for item in options) or
                    len({item['id'] for item in options}) != len(options)):
                raise ValueError('Invalid required skill group options')
            required_selection_group(group)
        if group['kind'] == 'text-list' and not isinstance(group.get('skill'),dict):
            raise ValueError('Text skill choices need a skill definition')
    for group in rules['groups']:
        exclusions = group.get('different_from', [])
        if (not isinstance(exclusions,list) or any(not isinstance(key,str) or key not in identifiers or key == group['id'] for key in exclusions)):
            raise ValueError('Required choice exclusions must name another group')
    for definition in rules['grants']:
        if (not isinstance(definition,dict) or
                ('specialty_from' in definition and definition['specialty_from'] not in identifiers)):
            raise ValueError('Invalid required skill grant specialty')
    definitions = [*rules['grants'], *[option for group in rules['groups'] for option in group.get('options', [])],
                   *[group['skill'] for group in rules['groups'] if 'skill' in group]]
    known = {row['id']: row for row in pack.get('skills', [])}
    for definition in definitions:
        if definition.get('kind') == 'physical' and 'base' not in definition:
            if definition != known.get(definition.get('id')):
                raise ValueError('Required Physical choices must preserve an exact nonpercentile catalog definition')
        training_definition(definition, pack.get('skills', []))
        independent_check_rules(definition, pack.get('skills', []))
    return rules
