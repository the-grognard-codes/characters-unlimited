"""Retained additional resource growth independent of game or class identity."""

from copy import deepcopy
import json
from .recorded_formulas import validate_formula, formula_value, roll_formula


def level_gain_definitions(rules, resources):
    definitions = rules.get('resource_gains', {})
    if (not isinstance(definitions, dict) or len(definitions) > 100 or
            set(definitions) - set(resources)):
        raise ValueError('Level gains must reference generated resource identities')
    for definition in definitions.values():
        if not isinstance(definition, dict) or set(definition) != {'formula', 'source'}:
            raise ValueError('Level gains require a formula and source')
        validate_formula(definition['formula'])
        if definition['formula']['count'] == 0:
            formula_value(definition['formula'], [])
        source = definition['source']
        if (not isinstance(source, dict) or any(not isinstance(source.get(key), str) or
                not source[key].strip() for key in ('book', 'section'))):
            raise ValueError('Level gains need book and section evidence')
    return definitions


def validate_level_resource_gains(record, rules, resources):
    definitions = level_gain_definitions(rules, resources)
    if not definitions:
        if 'resource_gains' in record:
            raise ValueError('Undeclared level resource gains')
        return
    gains = record.get('resource_gains')
    if not isinstance(gains, dict) or set(gains) != set(definitions):
        raise ValueError('Every declared level resource gain needs its recorded contribution')
    for resource, definition in definitions.items():
        receipt = gains[resource]
        if (not isinstance(receipt, dict) or set(receipt) != {'value', 'rolls', 'source'} or
                type(receipt['value']) is not int or
                receipt['value'] != formula_value(definition['formula'], receipt['rolls']) or
                json.dumps(receipt['source'], sort_keys=True, allow_nan=False) !=
                json.dumps(definition['source'], sort_keys=True, allow_nan=False)):
            raise ValueError('Level resource gains must replay their exact pinned formula and source')


def level_gain_fields(rules, resources, die, cached=None):
    definitions = level_gain_definitions(rules, resources)
    if cached is not None:
        validate_level_resource_gains(cached, rules, resources)
        return {'resource_gains': deepcopy(cached['resource_gains'])} if definitions else {}
    gains = {}
    for resource, definition in definitions.items():
        rolls = roll_formula(definition['formula'], die)
        gains[resource] = {'value': formula_value(definition['formula'], rolls),
                           'rolls': rolls, 'source': deepcopy(definition['source'])}
    return {'resource_gains': gains} if definitions else {}
