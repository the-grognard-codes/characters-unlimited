"""Source defaults for initial choice pools, preserving recorded acquisition ages."""


def validate_pool_learning(pack):
    for rule in pack.get('pools', {}).values():
        if 'default_learned_level' in rule and (
                type(rule['default_learned_level']) is not int or rule['default_learned_level'] != 1):
            raise ValueError('Initial skill choice pools default to learned level one')


def pool_learning_default(pack, pool, current_level):
    validate_pool_learning(pack)
    return pack['pools'][pool].get('default_learned_level', current_level)
