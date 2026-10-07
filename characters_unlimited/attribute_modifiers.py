"""Recorded class contributions, distinct from racial pools and player edits."""

from copy import deepcopy
from .recorded_formulas import validate_formula, formula_value, roll_formula
from .effect_operations import effect_total


ATTRIBUTE_NAMES = ('IQ', 'ME', 'MA', 'PS', 'PP', 'PE', 'PB', 'SPD')


def class_minima(selected_class):
    minima = selected_class.get('attribute_minima', {})
    if not isinstance(minima, dict) or set(minima) - set(ATTRIBUTE_NAMES):
        raise ValueError('Class minima require known attribute targets')
    for minimum in minima.values():
        if (not isinstance(minimum, dict) or set(minimum) != {'value', 'source'} or
                type(minimum['value']) is not int or not 1 <= minimum['value'] <= 1000):
            raise ValueError('Class minima require bounded positive integer values')
        source = minimum['source']
        if (not isinstance(source, dict) or any(not isinstance(source.get(key), str) or
                not source[key].strip() for key in ('book', 'section'))):
            raise ValueError('Class minima require book and section evidence')
    return minima


def class_effects(selected_class):
    class_minima(selected_class)
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


def class_minimum_modifier(selected_class, name):
    minimum = class_minima(selected_class)[name]
    return {'id': 'class-minimum:' + selected_class['id'], 'value': minimum['value'],
            'rolls': [], 'operation': 'minimum', 'source': deepcopy(minimum['source'])}


def roll_class_modifiers(attributes, selected_class, die):
    effects = class_effects(selected_class)
    for name, effect in effects.items():
        rolls = roll_formula(effect['formula'], die)
        record = attributes[name]
        record['modifiers'] = [class_attribute_modifier(selected_class, name, rolls)]
        record['value'] = attribute_value(record)
    for name in class_minima(selected_class):
        record = attributes[name]
        if name not in effects:
            record['modifiers'] = []
        record['modifiers'].append(class_minimum_modifier(selected_class, name))
        record['value'] = attribute_value(record)
