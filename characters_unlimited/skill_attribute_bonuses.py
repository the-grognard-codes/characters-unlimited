"""Source-bound attribute contributions to ordinary skill percentages."""

from .attribute_modifiers import ATTRIBUTE_NAMES
from .recorded_formulas import MAX_INTEGER


def needs_numeric_skill_projection(pack):
    return bool(pack.get('skill_effects') or
                any(skill.get('attribute_bonuses') or skill.get('granted_skills') for skill in pack.get('skills', [])))


def attribute_bonus_rules(definition):
    rules = definition.get('attribute_bonuses', [])
    if not isinstance(rules, list) or len(rules) > 16:
        raise ValueError('Skill attribute bonuses require a bounded list')
    names = set()
    for rule in rules:
        if not isinstance(rule, dict):
            raise ValueError('Skill attribute bonus must be a declaration')
        fields = {'name', 'attribute', 'operation', 'threshold', 'amount', 'source'}
        if rule.get('operation') == 'above':
            fields.add('step')
        if (set(rule) != fields or rule.get('operation') not in ('above', 'at_most') or
                not isinstance(rule.get('name'), str) or not rule['name'].strip() or
                rule['name'] in names or rule.get('attribute') not in ATTRIBUTE_NAMES or
                any(type(rule.get(key)) is not int or abs(rule[key]) > MAX_INTEGER
                    for key in ('threshold', 'amount')) or
                ('step' in rule and (type(rule['step']) is not int or not 1 <= rule['step'] <= MAX_INTEGER))):
            raise ValueError('Unsupported skill attribute bonus declaration')
        source = rule['source']
        if (not isinstance(source, dict) or
                any(not isinstance(source.get(key), str) or not source[key].strip()
                    for key in ('book', 'section'))):
            raise ValueError('Skill attribute bonuses need source evidence')
        names.add(rule['name'])
    return rules


def attribute_contributions(definition, attributes):
    result = {}
    for rule in attribute_bonus_rules(definition):
        value = attributes[rule['attribute']]['value']
        if rule['operation'] == 'above':
            steps = (max(0, value - rule['threshold']) + rule['step'] - 1) // rule['step']
            amount = steps * rule['amount']
        else:
            amount = rule['amount'] if value <= rule['threshold'] else 0
        if abs(amount) > MAX_INTEGER:
            raise ValueError('Skill attribute bonus exceeds the exact integer range')
        result['Attribute: ' + rule['name']] = amount
    return result
