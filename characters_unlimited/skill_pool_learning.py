"""Source-bound pool milestones and retained skill acquisition ages."""

from .advancement import learning_key
from .skill_choices import selection_policy


def pool_awards(pack, pool):
    """Return the complete entitlement schedule for an opted-in named pool."""
    rule = pack['pools'][pool]
    if 'level_awards' not in rule:
        return None
    awards = rule['level_awards']
    higher = pack.get('higher_advancement', {})
    if (not isinstance(awards, list) or not 1 <= len(awards) <= 1000 or
            type(rule.get('count')) is not int or not 0 <= rule['count'] <= 1000 or
            type(higher.get('max_level')) is not int or
            any(key in higher for key in (pool + '_levels', pool + '_per_award', pool + '_award_counts'))):
        raise ValueError('Named pool awards need a bounded initial count and one progression schedule')
    seen = set()
    for award in awards:
        if (not isinstance(award, dict) or set(award) != {'level', 'count', 'source'} or
                type(award['level']) is not int or not 2 <= award['level'] <= higher['max_level'] or
                award['level'] in seen or type(award['count']) is not int or
                not 1 <= award['count'] <= 1000 or
                not isinstance(award['source'], dict) or
                any(not isinstance(award['source'].get(key), str) or
                    not award['source'][key].strip() for key in ('book', 'section'))):
            raise ValueError('Named pool awards need distinct bounded levels, counts and source evidence')
        seen.add(award['level'])
    if rule['count'] + sum(award['count'] for award in awards) > 4000:
        raise ValueError('Named pool awards exceed the bounded learning history')
    return sorted(awards, key=lambda item: item['level'])


def validate_pool_learning(pack):
    for pool, rule in pack.get('pools', {}).items():
        if 'default_learned_level' in rule and (
                type(rule['default_learned_level']) is not int or rule['default_learned_level'] != 1):
            raise ValueError('Initial skill choice pools default to learned level one')
        if 'level_awards' in rule:
            if rule.get('default_learned_level', 1) != 1:
                raise ValueError('Named pool awards require level-one initial choices')
            pool_awards(pack, pool)


def pool_learning_default(pack, pool, current_level):
    validate_pool_learning(pack)
    return pack['pools'][pool].get('default_learned_level', 1 if 'level_awards' in pack['pools'][pool] else current_level)


def scheduled_learning_levels(character, pack, selections):
    """Date new scheduled choices using unoccupied, currently attained source slots."""
    known = {row['id']: row for row in pack['skills']}
    retained = character.get('learning_levels', {})
    result: dict[str, int] = {}
    for pool in pack['pools']:
        awards = pool_awards(pack, pool)
        if awards is None:
            continue
        items = [item for item in selections if item['pool'] == pool]
        slots = [1] * pack['pools'][pool]['count']
        for award in awards:
            if award['level'] <= character['level']:
                slots.extend([award['level']] * award['count'])
        used = [False] * len(slots)
        existing: list[tuple[dict, str, int]] = []
        new: list[tuple[dict, str, int]] = []
        for item in items:
            key = learning_key('skill', item['skill_id'], item['specialty'])
            cost = selection_policy(known[item['skill_id']], pool, pack)['cost']
            (existing if key in retained else new).append((item, key, cost))
        for _, key, cost in sorted(existing, key=lambda entry: retained[entry[1]]):
            for _ in range(cost):
                available = [index for index, slot in enumerate(slots)
                             if not used[index] and slot <= retained[key]]
                if available:
                    used[available[-1]] = True
        for _, key, cost in new:
            available = [index for index, taken in enumerate(used) if not taken]
            chosen = available[:cost]
            for index in chosen:
                used[index] = True
            age = slots[chosen[-1]] if len(chosen) == cost else character['level']
            result.setdefault(key, age)
    return result


def pool_award_guidance(character, pack, selections):
    """Keep early or excess choices visible as honor-system guidance."""
    warnings = []
    for pool, rule in pack['pools'].items():
        awards = pool_awards(pack, pool)
        if awards is None:
            continue
        aged = []
        for item in selections:
            if item['pool'] != pool:
                continue
            key = learning_key('skill', item['skill_id'], item['specialty'])
            age = character.get('learning_levels', {}).get(key, pool_learning_default(pack, pool, character['level']))
            cost = selection_policy(next(row for row in pack['skills'] if row['id'] == item['skill_id']), pool, pack)['cost']
            aged.extend([age] * cost)
        for level in sorted(set(aged)):
            allowance = rule['count'] + sum(award['count'] for award in awards if award['level'] <= level)
            early = sum(age <= level for age in aged) - allowance
            if early > 0:
                warnings.append(f'{pool.title()}: {early} choice(s) recorded before their source award; choices are retained.')
                break
    return warnings
