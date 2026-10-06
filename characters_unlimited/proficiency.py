"""Shared percentile projection for primary and additional source-defined checks."""

from .recorded_formulas import MAX_INTEGER
from .skill_checks import selected_check_definition


def synergy_contributions(definition, available):
    return {synergy['name']: synergy['amount'] for synergy in definition.get('synergies', [])
            if available.intersection(synergy.get('any_of', [synergy.get('skill_id')]))}


def project_proficiency(definition, contributions, *, level_steps=0, effect_contributions=None, exact=False, growth_steps=None, available=()):
    independent = 'proficiency_rules' in definition
    if independent and (type(growth_steps) is not int or not 0 <= growth_steps <= 1000):
        raise ValueError("Independent checks need supported acquired-level growth")
    definition = selected_check_definition(definition, available)
    effects = effect_contributions or []
    contributions = dict(contributions)
    for effect in effects:
        label = 'Effect: ' + effect['name']
        contributions[label] = contributions.get(label, 0) + effect['value']
    if level_steps:
        contributions = {**contributions, 'experience':definition['per_level']*level_steps}
    uncapped = sum(contributions.values())
    guarded = independent or exact or effects or definition.get('attribute_bonuses') or 'Skill grant training' in contributions
    if guarded and abs(uncapped) > MAX_INTEGER:
        raise ValueError('Skill effect total exceeds the exact integer range')
    checks = []
    normal_checks = {'primary': {'percentage': min(98, uncapped), 'per_level': definition['per_level']}}
    for check in definition.get('additional_checks', []):
        if 'context_of' in check:
            reference = normal_checks[check['context_of']]
            normal = reference['percentage']
            multiplier = check.get('multiplier', 1)
            modifier = check.get('modifier', 0)
            check_contributions = {'normal_proficiency': normal * multiplier, 'context_modifier': modifier}
            value = sum(check_contributions.values())
            projected = {'name': check['name'], 'percentage': min(value,check['maximum']) if 'maximum' in check else value, 'uncapped_percentage': value,
                         'contributions': check_contributions, 'context_of': check['context_of'],
                         'normal_percentage': normal, 'multiplier': multiplier,
                         'per_level': reference['per_level'] * multiplier}
        else:
            check_contributions = {**contributions, 'base': check['base']}
            if independent:
                if 'advancement' in check_contributions or growth_steps:
                    check_contributions['advancement'] = check['per_level'] * growth_steps
            elif level_steps:
                check_contributions['experience'] = check.get('per_level',definition['per_level'])*level_steps
            value = sum(check_contributions.values())
            projected = {'name': check['name'], 'percentage': min(98, value),
                         'uncapped_percentage': value, 'contributions': check_contributions, 'per_level': check.get('per_level',definition['per_level'])}
        if guarded and abs(projected['uncapped_percentage']) > MAX_INTEGER:
            raise ValueError('Skill effect check total exceeds the exact integer range')
        checks.append(projected)
        normal_checks[check['name']] = projected
    return {**({'effect_contributions': effects} if effects else {}), 'percentage': min(98, uncapped), 'uncapped_percentage': uncapped,
            'contributions': contributions, 'additional_checks': checks}
