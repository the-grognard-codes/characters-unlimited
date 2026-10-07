"""Shared milestone awards with opt-in source count overrides."""


def earned_skill_choices(rules, pool, level):
    milestones = rules.get(pool + '_levels', [])
    overrides = rules.get(pool + '_award_counts', {})
    if not isinstance(overrides, dict) or len(overrides) > 1000:
        raise ValueError('Skill award counts require a bounded milestone map')
    allowed = {str(milestone) for milestone in milestones}
    for milestone, amount in overrides.items():
        if (milestone not in allowed or type(amount) is not int or not 1 <= amount <= 1000):
            raise ValueError('Skill award counts need supported milestones and exact positive counts')
    default = rules.get(pool + '_per_award', 1)
    return sum(overrides.get(str(milestone), default) for milestone in milestones if milestone <= level)
