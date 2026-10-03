"""Source-bound education outcomes; program skill selection follows separately."""

from copy import deepcopy


def education_selection(pack, method, education_id=None, die=None):
    if method == 'roll':
        if education_id is not None:
            raise ValueError('A random education roll cannot also choose an outcome')
        roll = die(100)
        if type(roll) is not int or not 1 <= roll <= 100:
            raise ValueError('Education dice must return a whole number from 1 to 100')
        outcome = next(item for item in pack['outcomes'] if item['min'] <= roll <= item['max'])
        return {'id':outcome['id'], 'method':'roll', 'roll':roll}
    if method == 'choose' and any(item['id'] == education_id for item in pack['outcomes']):
        return {'id':education_id, 'method':'choose'}
    raise ValueError('Roll education or choose an available education level')


def validate_education(record, pack):
    if not isinstance(record, dict) or set(record) != {'selection', 'history'}:
        raise ValueError('Invalid education record')
    history = record['history']
    if not isinstance(history, list) or not 1 <= len(history) <= 1000:
        raise ValueError('Education history must contain between 1 and 1000 selections')
    for selection in history:
        if not isinstance(selection, dict):
            raise ValueError('Invalid education history selection')
        method = selection.get('method')
        if method == 'roll':
            expected = education_selection(pack, method, die=lambda sides: selection.get('roll'))
        else:
            expected = education_selection(pack, method, selection.get('id'))
        if selection != expected:
            raise ValueError('Education selection does not match its method or recorded dice')
    if record['selection'] != history[-1]:
        raise ValueError('Education must match the latest retained selection')


def project_education(record, pack):
    if record is not None:
        validate_education(record, pack)
    selection = record['selection'] if record is not None else None
    outcome = next((item for item in pack['outcomes'] if selection and item['id'] == selection['id']), None)
    return deepcopy({'catalog':pack['outcomes'], 'selection':selection, 'outcome':outcome,
                     'history':record['history'] if record else [], 'source':pack['source'],
                     'universal_grants':pack['universal_grants'], 'guidance':pack['guidance'],
                     'rules':{'id':pack['id'], 'version':pack['version']}})
