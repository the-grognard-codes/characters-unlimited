"""Shared percentile projection for primary and additional source-defined checks."""


def synergy_contributions(definition, available):
    return {synergy['name']: synergy['amount'] for synergy in definition.get('synergies', [])
            if available.intersection(synergy.get('any_of', [synergy.get('skill_id')]))}


def project_proficiency(definition, contributions):
    uncapped = sum(contributions.values())
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
            value = sum(check_contributions.values())
            projected = {'name': check['name'], 'percentage': min(98, value),
                         'uncapped_percentage': value, 'contributions': check_contributions, 'per_level': check.get('per_level',definition['per_level'])}
        checks.append(projected)
        normal_checks[check['name']] = projected
    return {'percentage': min(98, uncapped), 'uncapped_percentage': uncapped,
            'contributions': contributions, 'additional_checks': checks}
