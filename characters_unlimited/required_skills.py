"""Declarative O.C.C. percentile grants and required choice groups."""

from .skill_choices import learned_selection_ids, learned_selection_pools, specialty_key
from .proficiency import synergy_contributions, project_proficiency
from .advancement import learning_age
from .required_definitions import required_catalog, required_selection_group
from .required_selections import validate_required_choices, selected_required_definitions
from .skill_effects import pack_skill_effects, matching_skill_effects
from .skill_attribute_bonuses import attribute_contributions
from .skill_training import training_rules, required_training_definition, recorded_training_level


def project_required_skills(character, pack, intelligence, *, skill_grants=None):
    aliases = training_rules(pack)
    skill_effects = pack_skill_effects(pack)
    rules = required_catalog(pack)
    if rules is None:
        return {'grants': [], 'remaining': {}, 'warnings': [], 'catalog': None}
    definitions, remaining, warnings = selected_required_definitions(character, pack)
    definitions = [(required_training_definition(definition, pack, aliases), specialty)
                   for definition, specialty in definitions]
    available = {definition['id'] for definition, _ in definitions}
    available.update(learned_selection_ids(character.get('skill_selections', []), pack))
    available.update(skill_grants or {})
    selection_pools = learned_selection_pools(character.get('skill_selections', []), pack)
    grants = []
    seen = set()
    for definition, specialty in definitions:
        identity = (definition['id'], specialty_key(specialty))
        if identity in seen:
            warnings.append(f"{definition['name']}: duplicate O.C.C. grant retained without another proficiency bonus.")
            continue
        seen.add(identity)
        if definition.get('kind') == 'physical' and 'base' not in definition:
            continue  # Physical receipts are projected once through automatic grants.
        if definition.get('kind') == 'training':
            grants.append({**definition, 'specialty':specialty, 'quality':'trained'})
            continue
        contributions = {'base': definition['base'], 'class': definition['class_bonus'], 'intelligence': intelligence}
        training = (skill_grants or {}).get(definition['id']) if not specialty else None
        if training:
            contributions['class'] = max(definition['class_bonus'], training['ordinary_bonus'])
            if training['origins']:
                contributions['Skill grant training'] = max(0, training['bonus'] - contributions['class'])
        learned = (recorded_training_level(character, definition['id'], aliases, default=1)
                   if aliases is not None and not specialty else None)
        if training and aliases is not None:
            learned = training['learned_level']
        if character['level'] > 1:
            age = character['level'] - learned + 1 if learned is not None else learning_age(character, 'skill', definition['id'], specialty)
            contributions['advancement'] = (age - 1) * definition['per_level']
        if 'class_ability' in definition:
            contributions['class_ability'] = definition['class_ability']
        contributions.update(synergy_contributions(definition, available))
        contributions.update(attribute_contributions(definition, character['attributes']))
        grants.append({**definition, 'specialty': specialty, **({'learned_level': learned} if learned is not None and 'catalog_skill_id' in definition else {}), **({'grant_origins': training['origins']} if training and training['origins'] else {}), **project_proficiency(definition, contributions, effect_contributions=matching_skill_effects(definition['id'], skill_effects), exact=aliases is not None or any(row.get('granted_skills') for row in pack['skills']), growth_steps=age-1 if character['level'] > 1 else 0, available=available, selection_pools=selection_pools), 'quality': 'trained'})
    return {'grants': grants, 'remaining': remaining, 'warnings': warnings, 'catalog': rules}
