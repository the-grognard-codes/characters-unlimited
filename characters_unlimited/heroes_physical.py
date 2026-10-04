"""Heroes selections adapted to the shared retained Physical effect engine."""

from copy import deepcopy
from .heroes_programs import project_programs
from .heroes_training import resolve_training, training_ids
from .physical import acquire_physical, project_physical, validate_physical


def physical_character(character, pack, education_pack):
    selections = project_programs(character, pack, education_pack)['physical_selections']
    return {**character, 'skill_selections':selections}


def acquire_hero_physical(character, pack, education_pack, die):
    adapted = physical_character(character, pack, education_pack)
    return acquire_physical(adapted, adapted['skill_selections'], pack, die)


def project_hero_physical(character, pack, education_pack):
    physical = project_physical(physical_character(character, pack, education_pack), pack)
    active = resolve_training(character, pack, [row['id'] for row in physical['selected']])
    physical['active_training'] = active
    physical['training_choices'] = [{'id':row['id'],'name':row['name']} for row in physical['selected']
                                    if row['id'] in training_ids(pack)]
    selected = {row['id'] for row in physical['selected']}
    physical['training_receipts'] = [{'id':row['id'],'name':row['name'],'source':deepcopy(row['source']),
                                      'rolls':deepcopy(character['physical_acquisitions'][row['id']]['rolls']),
                                      'selected':row['id'] in selected,'active':row['id'] == active}
                                     for row in pack['skills'] if row['id'] in training_ids(pack)
                                     and row['id'] in character.get('physical_acquisitions', {})]
    if 'training_skill_ids' in pack.get('combat', {}):
        physical['combat'] = {}
        for row in physical['selected']:
            if row['id'] in training_ids(pack):
                row['combat_active'] = row['id'] == active
                if not row['combat_active']:
                    row['effects']['combat'] = {}
            for stat, bonus in row['effects']['combat'].items():
                physical['combat'].setdefault(stat, {})[row['name']] = bonus
    return physical


def validate_hero_physical(character, pack, education_pack):
    adapted = physical_character(character, pack, education_pack)
    validate_physical(adapted, pack)
    resolve_training(character, pack, [row['skill_id'] for row in adapted['skill_selections']])
