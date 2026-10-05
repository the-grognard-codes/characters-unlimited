"""Source-bound race/class pairings shared by creation and exact save replay."""

from .generation import racial_formulas, racial_sources
from .attribute_modifiers import class_effects


def _source(source):
    if (not isinstance(source, dict) or any(not isinstance(source.get(key), str) or
            not source[key].strip() for key in ('book', 'section'))):
        raise ValueError('Creation profiles need book and section evidence')


def _options(rows, kind):
    if not isinstance(rows, list) or not 1 <= len(rows) <= 1000:
        raise ValueError('Creation ' + kind + ' require a bounded nonempty list')
    result = {}
    for row in rows:
        if (not isinstance(row, dict) or any(not isinstance(row.get(key), str) or
                not row[key].strip() for key in ('id', 'name')) or row['id'] in result):
            raise ValueError('Creation ' + kind + ' need distinct identities and names')
        result[row['id']] = row
    return result


def creation_classes(pack):
    """Compile every declared pairing and core formula without drawing dice.

    Legacy packs retain their existing race/class cross product. The ordered
    class list in each explicit profile supplies that race's default choice.
    """
    if 'creation_profile_format' not in pack and 'creation_profiles' not in pack:
        return None
    if pack.get('creation_profile_format') != 'paired-v1':
        raise ValueError('Unsupported creation profile format')
    races = _options(pack.get('races'), 'races')
    classes = _options(pack.get('classes'), 'classes')
    rows = pack.get('creation_profiles')
    if not isinstance(rows, list) or len(rows) != len(races):
        raise ValueError('Creation profiles must declare every race exactly once')
    result = {}
    reachable = set()
    for row in rows:
        if (not isinstance(row, dict) or set(row) != {'race', 'classes', 'source'} or
                not isinstance(row['race'], str) or row['race'] not in races or row['race'] in result or
                not isinstance(row['classes'], list) or not 1 <= len(row['classes']) <= len(classes) or
                any(not isinstance(identity, str) or identity not in classes for identity in row['classes']) or
                len(set(row['classes'])) != len(row['classes'])):
            raise ValueError('Creation profiles need distinct known race/class pairings')
        _source(row['source'])
        result[row['race']] = list(row['classes'])
        reachable.update(row['classes'])
    if reachable != set(classes):
        raise ValueError('Every declared class needs a compatible race')
    for identity, race in races.items():
        try:
            racial_formulas(race)
            racial_sources(race, pack.get('source'))
        except (ValueError, TypeError, KeyError, AttributeError) as error:
            raise ValueError(identity + ' racial attributes: ' + str(error)) from None
    for identity, selected_class in classes.items():
        try:
            _source(selected_class.get('source', pack.get('source')))
            if (not isinstance(selected_class.get('automation_gaps'), list) or
                    any(not isinstance(note, str) for note in selected_class['automation_gaps'])):
                raise ValueError('Class guidance must be a list of descriptions')
            for effect in class_effects(selected_class).values():
                _source(effect['source'])
        except (ValueError, TypeError, KeyError, AttributeError) as error:
            raise ValueError(identity + ' class attributes: ' + str(error)) from None
    return result


def creation_pair(pack, race, character_class=None):
    choices = creation_classes(pack)
    if character_class is None:
        character_class = choices.get(race, [None])[0] if choices is not None else pack['classes'][0]['id']
    if choices is not None and character_class not in choices.get(race, []):
        raise ValueError('Choose a compatible race and class from the selected game')
    selected_race = next((row for row in pack['races'] if row['id'] == race), None)
    selected_class = next((row for row in pack['classes'] if row['id'] == character_class), None)
    if selected_race is None or selected_class is None:
        raise ValueError('Select an available race and class from the selected game')
    return selected_race, selected_class
