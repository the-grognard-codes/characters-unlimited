"""Retained Mutant outcome dice and source-bound starting power allowances."""

from copy import deepcopy


def select_budget(pack, method, outcome_id=None, die=None):
    roll = None
    if method == 'roll':
        if outcome_id is not None:
            raise ValueError('A power outcome roll cannot also choose an outcome')
        roll = die(100)
        if type(roll) is not int or not 1 <= roll <= 100:
            raise ValueError('Power outcome dice must return a whole number from 1 to 100')
        outcome = next(row for row in pack['outcomes'] if row.get('min', 101) <= roll <= row.get('max', 0))
    elif method == 'choose':
        outcome = next((row for row in pack['outcomes'] if row['id'] == outcome_id), None)
        if outcome is None:
            raise ValueError('Choose an available Mutant power outcome')
    else:
        raise ValueError('Roll or choose a Mutant power outcome')
    rolls = []
    for budget in outcome['budgets']:
        if budget.get('die'):
            face = die(budget['die'])
            if type(face) is not int or not 1 <= face <= budget['die']:
                raise ValueError('Power count dice must return a whole number within the die range')
            rolls.append(face)
    selection = {'id':outcome['id'], 'method':method, 'rolls':rolls}
    if roll is not None:
        selection['roll'] = roll
    return selection


def validate_budget(record, pack):
    if not isinstance(record, dict) or set(record) != {'selection', 'history'}:
        raise ValueError('Invalid Mutant power budget record')
    history = record['history']
    if not isinstance(history, list) or not 1 <= len(history) <= 1000:
        raise ValueError('Power budget history must contain between 1 and 1000 selections')
    for selection in history:
        if not isinstance(selection, dict) or not isinstance(selection.get('rolls'), list):
            raise ValueError('Invalid power budget history selection')
        dice = iter(([selection.get('roll')] if selection.get('method') == 'roll' else []) + selection['rolls'])
        try:
            expected = select_budget(pack, selection.get('method'),
                                     selection.get('id') if selection.get('method') == 'choose' else None,
                                     lambda sides: next(dice))
        except StopIteration:
            raise ValueError('Missing power count dice') from None
        if selection != expected:
            raise ValueError('Power outcome must match its recorded method and dice')
    if record['selection'] != history[-1]:
        raise ValueError('Power budget must match its latest history selection')


def project_budget(record, pack):
    if record is not None:
        validate_budget(record, pack)
    selection = record['selection'] if record else None
    outcome = next((row for row in pack['outcomes'] if selection and row['id'] == selection['id']), None)
    budgets = []
    if outcome:
        assert selection is not None
        dice = iter(selection['rolls'])
        for row in outcome['budgets']:
            budgets.append({'name':row['name'], 'count':row['count'] + (next(dice) if row.get('die') else 0)})
    return deepcopy({'catalog':pack['outcomes'], 'selection':selection, 'outcome':outcome,
                     'budgets':budgets, 'history':record['history'] if record else [],
                     'source':pack['source'], 'guidance':[
                         note.replace('Selecting individual powers and calculating their effects remain pending.',
                                      'Individual power availability and effects are listed separately; other powers remain pending.')
                         for note in [*pack['guidance'], *(outcome.get('guidance', []) if outcome else [])]],
                     'rules':{'id':pack['id'], 'version':pack['version']}})
