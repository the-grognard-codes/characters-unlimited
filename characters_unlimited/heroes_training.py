"""Resolve one Heroes training profile without stacking acquired styles."""


def training_ids(pack):
    rules = pack.get('combat', {})
    return rules.get('training_skill_ids', [rules['basic_skill_id']] if rules else [])


def resolve_training(character, pack, selected_ids):
    known = training_ids(pack)
    if 'hero_combat_training' in character:
        choice = character['hero_combat_training']
        if 'training_skill_ids' not in pack.get('combat', {}):
            raise ValueError('Explicit Heroes training needs its accepted rule version')
        if choice is not None and (not isinstance(choice, str) or choice not in known
                or choice not in character.get('physical_acquisitions', {})):
            raise ValueError('Active Heroes training must retain a known acquired style')
        return choice if choice in selected_ids else None
    available = set(selected_ids).intersection(known)
    return next(iter(available)) if len(available) == 1 else None
