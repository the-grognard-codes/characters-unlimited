"""Recorded class contributions, distinct from racial pools and player edits."""

from copy import deepcopy
from .recorded_formulas import formula_value, roll_formula


def attribute_value(record):
    if record.get('fixed') is not None:
        return record['fixed']
    modifiers = record.get('modifiers', [])
    calculated = record['base'] + sum(item['value'] for item in modifiers if not item['id'].startswith('power-floor:'))
    calculated = max([calculated, *(item['value'] for item in modifiers if item['id'].startswith('power-floor:'))])
    if 'cap' in record:
        calculated = min(calculated, record['cap'])
    return calculated + record.get('adjustment', 0)


def class_attribute_modifier(selected_class, name, rolls):
    return {'id': 'class:' + selected_class['id'],
            'value': formula_value(selected_class['attribute_bonuses'][name], rolls),
            'rolls': deepcopy(rolls), 'source': deepcopy(selected_class['attribute_bonus_source'])}


def roll_class_modifiers(attributes, selected_class, die):
    for name, formula in selected_class.get('attribute_bonuses', {}).items():
        rolls = roll_formula(formula, die)
        record = attributes[name]
        record['modifiers'] = [class_attribute_modifier(selected_class, name, rolls)]
        record['value'] = attribute_value(record)
