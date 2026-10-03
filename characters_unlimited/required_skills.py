"""Reviewed Vagabond grants and required choices, independent of browser state."""

from typing import Any
from .skill_choices import learned_selection_ids, specialty_key as language_key
from .proficiency import synergy_contributions, project_proficiency
from .advancement import learning_age

def validate_required_choices(choices, pack):
    if 'required' not in pack:
        raise ValueError('Preview a skill-rule update before selecting these required choices')
    if not isinstance(choices, dict) or set(choices) - {'native_language', 'other_languages', 'pilot', 'repair'}:
        raise ValueError('Provide the required skill choices')
    result: dict[str, Any] = {}
    for name in ('native_language', 'pilot', 'repair'):
        value = choices.get(name, '')
        if not isinstance(value, str):
            raise ValueError('Required skill choices must be text')
        value = value.strip()
        if name != 'native_language' and value and value not in {item['id'] for item in pack['required'][name]['options']}:
            raise ValueError('Select an available required skill choice')
        result[name] = value
    languages = choices.get('other_languages', [])
    if not isinstance(languages, list) or len(languages) > 1000 or any(not isinstance(language, str) for language in languages):
        raise ValueError('Provide at most 1000 language choices as text')
    result['other_languages'] = [language.strip() for language in languages]
    return result


def project_required_skills(character, pack, intelligence):
    rules = pack.get('required')
    if not rules:
        return {'grants': [], 'remaining': {}, 'warnings': [], 'catalog': None}
    choices = validate_required_choices(character.get('required_skill_choices', {}), pack)
    warnings = []
    native = language_key(choices['native_language'])
    unique = set()
    learned_languages = []
    for language in choices['other_languages']:
        key = language_key(language)
        if not key:
            warnings.append('Name every Language: Other choice.')
        elif key == native:
            warnings.append('Language: Other must differ from the native tongue; the retained choice does not fill another language slot.')
        elif key in unique:
            warnings.append('Choose distinct other languages; duplicate labels are retained without another slot or bonus.')
        else:
            unique.add(key)
            learned_languages.append(language)
    definitions = [(definition, choices['native_language'] if definition['id'] == 'native-language' else '') for definition in rules['grants']]
    definitions.extend((rules['other_languages']['skill'], language) for language in learned_languages)
    for name in ('pilot', 'repair'):
        if choices[name]:
            definitions.append((next(item for item in rules[name]['options'] if item['id'] == choices[name]), ''))
    available = {definition['id'] for definition, _ in definitions}
    available.update(learned_selection_ids(character.get('skill_selections', []), pack))
    grants = []
    for definition, specialty in definitions:
        contributions = {'base': definition['base'], 'class': definition['class_bonus'], 'intelligence': intelligence}
        if character['level'] > 1:
            contributions['advancement'] = (learning_age(character, 'skill', definition['id'], specialty) - 1) * definition['per_level']
        if 'class_ability' in definition:
            contributions['class_ability'] = definition['class_ability']
        contributions.update(synergy_contributions(definition, available))
        grants.append({**definition, 'specialty': specialty, **project_proficiency(definition, contributions), 'quality': 'trained'})
    remaining = {'native_language': int(not native), 'other_languages': rules['other_languages']['count'] - len(unique),
                 'pilot': int(not choices['pilot']), 'repair': int(not choices['repair'])}
    if remaining['other_languages'] < 0:
        warnings.append(f"Other languages: {-remaining['other_languages']} selection(s) over the allowance.")
    return {'grants': grants, 'remaining': remaining, 'warnings': warnings, 'catalog': rules}
