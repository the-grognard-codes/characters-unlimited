"""Recorded class contributions, distinct from racial pools and player edits."""

from .generation import roll_attribute, generation_settings


def attribute_value(record):
    if record.get('fixed') is not None:
        return record['fixed']
    calculated = record['base'] + sum(item['value'] for item in record.get('modifiers', []))
    if 'cap' in record:
        calculated = min(calculated, record['cap'])
    return calculated + record.get('adjustment', 0)


def roll_class_modifiers(attributes, selected_class, die):
    for name, formula in selected_class.get('attribute_bonuses', {}).items():
        source = selected_class['attribute_bonus_source']
        result = roll_attribute(formula, generation_settings(), die, source)
        record = attributes[name]
        record['modifiers'] = [{'id': 'class:' + selected_class['id'], 'value': result['base'],
                                'rolls': result['rolls'], 'source': source}]
        record['value'] = attribute_value(record)
