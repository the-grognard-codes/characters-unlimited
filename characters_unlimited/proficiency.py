"""Shared percentile projection for primary and additional source-defined checks."""


def synergy_contributions(definition, available):
    return {synergy['name']: synergy['amount'] for synergy in definition.get('synergies', [])
            if available.intersection(synergy.get('any_of', [synergy.get('skill_id')]))}


def project_proficiency(definition, contributions):
    uncapped = sum(contributions.values())
    checks = []
    for check in definition.get('additional_checks', []):
        check_contributions = {**contributions, 'base': check['base']}
        value = sum(check_contributions.values())
        checks.append({'name': check['name'], 'percentage': min(98, value),
                       'uncapped_percentage': value, 'contributions': check_contributions})
    return {'percentage': min(98, uncapped), 'uncapped_percentage': uncapped,
            'contributions': contributions, 'additional_checks': checks}
