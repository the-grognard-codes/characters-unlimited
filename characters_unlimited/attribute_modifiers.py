"""Recorded class contributions, distinct from racial pools and player edits."""

from copy import deepcopy
from .recorded_formulas import validate_formula, formula_value, roll_formula
from .effect_operations import effect_total


ATTRIBUTE_NAMES = ('IQ', 'ME', 'MA', 'PS', 'PP', 'PE', 'PB', 'SPD')


def class_effects(selected_class):
    bonuses = selected_class.get('attribute_bonuses', {})
    typed = selected_class.get('attribute_effects', {})
    if (not isinstance(bonuses, dict) or not isinstance(typed, dict) or
            (set(bonuses) | set(typed)) - set(ATTRIBUTE_NAMES) or set(bonuses).intersection(typed)):
        raise ValueError('Class attribute effects require distinct known attribute targets')
    result = {}
    for name, formula in bonuses.items():
        result[name] = {'operation': 'add', 'formula': formula,
                        'source': selected_class.get('attribute_bonus_source')}
    for name, effect in typed.items():
        if (not isinstance(effect, dict) or set(effect) != {'operation', 'formula', 'source'} or
                effect['operation'] not in ('add', 'minimum')):
            raise ValueError('Unsupported typed class attribute effect')
        result[name] = effect
    for effect in result.values():
        validate_formula(effect['formula'])
        if (not isinstance(effect['source'], dict) or
                not isinstance(effect['source'].get('book'), str) or not effect['source']['book'].strip()):
            raise ValueError('Class attribute effects need source evidence')
    return result


def attribute_value(record):
    if record.get('fixed') is not None:
        return record['fixed']
    modifiers = record.get('modifiers', [])
    effects = [{'operation': item.get('operation',
                'minimum' if item['id'].startswith('power-floor:') else 'add'), 'value': item['value']}
               for item in modifiers]
    calculated = effect_total(record['base'], effects)
    if 'cap' in record:
        calculated = min(calculated, record['cap'])
    return calculated + record.get('adjustment', 0)


def class_attribute_modifier(selected_class, name, rolls):
    effect = class_effects(selected_class)[name]
    result = {'id': 'class:' + selected_class['id'],
              'value': formula_value(effect['formula'], rolls),
              'rolls': deepcopy(rolls), 'source': deepcopy(effect['source'])}
    if name in selected_class.get('attribute_effects', {}):
        result['operation'] = effect['operation']
    return result


def roll_class_modifiers(attributes, selected_class, die):
    for name, effect in class_effects(selected_class).items():
        rolls = roll_formula(effect['formula'], die)
        record = attributes[name]
        record['modifiers'] = [class_attribute_modifier(selected_class, name, rolls)]
        record['value'] = attribute_value(record)
