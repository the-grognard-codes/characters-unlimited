"""Heroes selections adapted to the shared retained Physical effect engine."""

from .heroes_programs import project_programs
from .physical import acquire_physical, project_physical, validate_physical


def physical_character(character, pack, education_pack):
    selections = project_programs(character, pack, education_pack)['physical_selections']
    return {**character, 'skill_selections':selections}


def acquire_hero_physical(character, pack, education_pack, die):
    adapted = physical_character(character, pack, education_pack)
    return acquire_physical(adapted, adapted['skill_selections'], pack, die)


def project_hero_physical(character, pack, education_pack):
    return project_physical(physical_character(character, pack, education_pack), pack)


def validate_hero_physical(character, pack, education_pack):
    validate_physical(physical_character(character, pack, education_pack), pack)
