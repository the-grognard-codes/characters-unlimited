"""Reviewed Human Mutant first advancement, retained gains and learning ages."""
from copy import deepcopy
from .level_resource_gains import level_gain_definitions, level_gain_fields, validate_level_resource_gains
from uuid import UUID
from .heroes_programs import project_programs


def remembered_learning(character, skills, education, *, learned_level=None):
    if learned_level is not None and (type(learned_level) is not int or not 1 <= learned_level <= character['level']):
        raise ValueError('Choose a learned level no later than the current level')
    levels = deepcopy(character.get('learning_levels', {}))
    view = project_programs(character, skills, education)
    identifiers = {row['id'] for row in view['skills']}
    identifiers.update(row['skill_id'] for row in view['physical_selections'])
    for identifier in identifiers:
        levels.setdefault(identifier, learned_level or character['level'])
    return levels


def power_gains(character, rules, die, cached=None):
    gains = deepcopy(cached or {})
    for acquisition in character.get('hero_powers', {}).get('acquisitions', []):
        definition = rules['power_hp_gains'].get(acquisition['power'])
        if definition is None or acquisition['id'] in gains:
            continue
        face = die(definition['sides'])
        if type(face) is not int or not 1 <= face <= definition['sides']:
            raise ValueError('Invalid power advancement Hit Point die')
        gains[acquisition['id']] = {'power':acquisition['power'], 'face':face,
                                  'source':deepcopy(definition['source'])}
    return gains


def first_hero_advance(character, rules, method, value, levels, die):
    if character['race'] != rules['race'] or character['character_class'] != rules['character_class']:
        raise ValueError('Reviewed Heroes advancement requires Human Mutant')
    if method not in ('xp', 'level') or type(value) is not int:
        raise ValueError('Choose XP or a whole-number level')
    if method == 'xp':
        target = next((level for level, (low,high) in enumerate(rules['xp_ranges'],1) if low <= value <= high),None)
        if target is None:
            raise ValueError('XP is outside the reviewed Heroes progression range')
        xp = value
    else:
        if not 1 <= value <= rules['max_level']:
            raise ValueError('Level is outside the reviewed Heroes progression range')
        target = value; xp = rules['xp_ranges'][target-1][0]
    if target < character['level']:
        raise ValueError('Undo advancement before selecting a lower level')
    if target == character['level']:
        record = character.get('advancement')
        return {'experience':xp, **({'advancement':{**record,'xp':xp}} if record and record['active'] else {})}
    if 'resources' not in character:
        raise ValueError('Generate starting resources before advancing')
    level_gain_definitions(rules, character['resources'])
    prior = character.get('advancement')
    face = prior['hp_roll'] if prior else die(rules['hp_die'])
    if type(face) is not int or not 1 <= face <= rules['hp_die']:
        raise ValueError('Invalid advancement Hit Point die')
    before = {key:deepcopy(item) for key,item in character.items()
              if key not in ('id','revision','updated_at','advancement','later_advancements')}
    record = {'active':True,'xp':xp,'hp_roll':face,'source':deepcopy(rules['source']), 'before':before,
              'power_hp_rolls':power_gains(character,rules,die,prior.get('power_hp_rolls') if prior else None),
              **level_gain_fields(rules, character['resources'], die, prior)}
    return {'level':2,'experience':xp,'learning_levels':levels,'advancement':record}


def validate_hero_advancement(character, rules, skills, education, *, higher=None, history_frame=False):
    record = character.get('advancement'); levels = character.get('learning_levels')
    if rules is None:
        if record is not None or levels is not None or character['level'] != 1 or 'later_advancements' in character or character.get('experience',0)>1875:
            raise ValueError('Heroes advancement requires its reviewed rule version')
        return
    progression = higher or rules
    if higher is not None and higher['base_rule'] != {'id':rules['id'],'version':rules['version']}:
        raise ValueError('Later Heroes progression requires its exact first-advancement dependency')
    if character['race'] != rules['race'] or character['character_class'] != rules['character_class'] or ('later_advancements' in character and higher is None) or not 1 <= character['level'] <= progression['max_level']:
        raise ValueError('Heroes advancement must match its reviewed path and levels')
    low, high = progression['xp_ranges'][character['level']-1]
    if not low <= character.get('experience',0) <= high:
        raise ValueError('Experience must match a reviewed Heroes level range')
    if record is None:
        if character['level'] != 1 or levels is not None or character.get('later_advancements'):
            raise ValueError('Advancement and learning records are required')
        return
    if (not isinstance(record,dict) or set(record) != ({'active','xp','hp_roll','source','before','power_hp_rolls'} |
        ({'resource_gains'} if rules.get('resource_gains') else set())) or type(record['active']) is not bool or
        (character['level'] < 2 if record['active'] else character['level'] != 1) or type(record['hp_roll']) is not int or not 1 <= record['hp_roll'] <= rules['hp_die'] or
        type(record['xp']) is not int or not rules['xp_ranges'][1][0] <= record['xp'] <= rules['xp_ranges'][1][1] or
        record['source'] != rules['source']):
        raise ValueError('Invalid recorded Heroes advancement')
    validate_level_resource_gains(record, rules, character.get('resources', {}))
    if record['active'] and character['level'] == 2 and character.get('experience') != record['xp']:
        raise ValueError('Experience must match the active advancement')
    before = record['before']
    if (not isinstance(before,dict) or before.get('level') != 1 or set(before).intersection({'id','revision','updated_at','advancement','later_advancements'}) or
        before.get('game') != character['game'] or before.get('race') != character['race'] or before.get('character_class') != character['character_class'] or 'resources' not in before):
        raise ValueError('Invalid pre-advancement snapshot')
    gains = record['power_hp_rolls']
    validate_power_gain_receipts(gains,rules)
    validate_higher_gains(character,rules,higher,history_frame=history_frame)
    if not record['active']:
        if levels is not None:raise ValueError('Undone advancement must restore pre-level learning records')
        return
    if skills is None or education is None or not isinstance(levels,dict) or len(levels)>4000:
        raise ValueError('Heroes advancement requires its skill, education and learning records')
    allowed = {row['id'] for row in skills['skills']}
    if any(not isinstance(key,str) or key not in allowed or type(value) is not int or not 1 <= value <= character['level'] for key,value in levels.items()):
        raise ValueError('Invalid Heroes learned-skill level')
    if remembered_learning(character,skills,education) != levels:
        raise ValueError('Every current Heroes skill must retain its learned level')
    for acquisition in character.get('hero_powers',{}).get('acquisitions',[]):
        if acquisition['power'] in rules['power_hp_gains'] and gains.get(acquisition['id'],{}).get('power') != acquisition['power']:
            raise ValueError('Power acquisition requires its recorded level gain')


def project_hero_advancement(character, rules, higher=None):
    record = character.get('advancement')
    dice = []
    if record:
        dice.append({'level':2,'face':record['hp_roll'],'active':record['active']})
        active = set(character.get('hero_powers',{}).get('active',[]))
        dice.extend({'level':2,'face':gain['face'],'active':record['active'] and identifier in active, 'power':gain['power']}
                    for identifier,gain in record['power_hp_rolls'].items())
        for event in character.get('later_advancements', []):
            attained = record['active'] and event['level'] <= character['level']
            dice.append({'level':event['level'],'face':event['hp_roll'],'active':attained})
            dice.extend({'level':event['level'],'face':gain['face'],'active':attained and identifier in active,'power':gain['power']}
                        for identifier,gain in event['power_hp_rolls'].items())
    rules = higher or rules
    return {'supported':True,'max_level':rules['max_level'],'max_xp':rules['xp_ranges'][-1][1],
            'level':character['level'],'xp':character.get('experience',0),'active':bool(record and record['active']),
            'dice':dice,'guidance':rules['guidance'],'source':deepcopy(rules['source'])}


def advancement_power_resources(character, rules):
    record = character.get('advancement')
    if not record or not record['active']:return []
    active = set(character.get('hero_powers',{}).get('active',[]))
    events = [(2,record), *((event['level'],event) for event in character.get('later_advancements',[]) if event['level'] <= character['level'])]
    return [{'resource':'HP','name':rules['power_hp_gains'][gain['power']]['name']+' level '+str(level),
             'value':gain['face'],'rolls':[gain['face']],'source':deepcopy(gain['source'])}
            for level,event in events for identifier,gain in event['power_hp_rolls'].items() if identifier in active]


def advance_higher_levels(character, rules, higher, method, value, levels, die, companion_pins):
    """Record flat intermediate snapshots and keep cached future gains for replay."""
    if higher['base_rule'] != {'id':rules['id'],'version':rules['version']}:
        raise ValueError('Later Heroes progression requires its exact first-advancement dependency')
    if method not in ('xp','level') or type(value) is not int:
        raise ValueError('Choose XP or a whole-number level')
    target = (next((level for level,(low,high) in enumerate(higher['xp_ranges'],1) if low <= value <= high),None)
              if method == 'xp' else value)
    if target is None or not 1 <= target <= higher['max_level']:
        raise ValueError('Value is outside the reviewed Heroes progression range')
    if target < character['level']:
        raise ValueError('Undo advancement before selecting a lower level')
    xp = value if method == 'xp' else higher['xp_ranges'][target-1][0]
    if target <= 2:
        return first_hero_advance(character,rules,method,value,levels,die)
    if target == character['level']:
        return {'experience':xp}
    level_gain_definitions(rules, character.get('resources', {}))
    level_gain_definitions(higher, character.get('resources', {}))
    candidate = deepcopy(character)
    if candidate['level'] == 1:
        candidate.update(first_hero_advance(candidate,rules,'level',2,levels,die))
    candidate['additional_rule_packs'] = {**candidate.get('additional_rule_packs',{}),**companion_pins}
    candidate['learning_levels'] = levels
    events = deepcopy(candidate.get('later_advancements',[]))
    for level in range(candidate['level']+1,target+1):
        cached = next((event for event in events if event['level']==level),None)
        face = cached['hp_roll'] if cached else die(higher['hp_die'])
        if type(face) is not int or not 1 <= face <= higher['hp_die']:
            raise ValueError('Invalid later advancement Hit Point die')
        before = {key:deepcopy(item) for key,item in candidate.items() if key not in ('id','revision','updated_at','later_advancements')}
        event = {'level':level,'hp_roll':face,'source':deepcopy(higher['source']),'before':before,
                 'power_hp_rolls':power_gains(candidate,rules,die,cached.get('power_hp_rolls') if cached else None),
                 **level_gain_fields(higher, candidate['resources'], die, cached)}
        events = sorted([event, *(item for item in events if item['level']!=level)],key=lambda item:item['level'])
        candidate.update(level=level,experience=higher['xp_ranges'][level-1][0],later_advancements=events)
    candidate['experience'] = xp
    return {key:candidate[key] for key in ('level','experience','learning_levels','advancement','later_advancements')}


def validate_higher_gains(character, rules, higher, *, history_frame=False):
    events = character.get('later_advancements',[])
    if not isinstance(events,list) or len(events)>13 or (events and higher is None):
        raise ValueError('Later Heroes gains require reviewed extension rules')
    seen = []
    for event in events:
        if (not isinstance(event,dict) or set(event)!=({'level','hp_roll','source','before','power_hp_rolls'} |
            ({'resource_gains'} if higher.get('resource_gains') else set())) or
            type(event['level']) is not int or not 3 <= event['level'] <= higher['max_level'] or
            type(event['hp_roll']) is not int or not 1 <= event['hp_roll'] <= higher['hp_die'] or event['source'] != higher['source']):
            raise ValueError('Invalid later Heroes advancement')
        validate_level_resource_gains(event, higher, character.get('resources', {}))
        before = event['before']
        if (not isinstance(before,dict) or before.get('level') != event['level']-1 or
            set(before).intersection({'id','revision','updated_at','later_advancements'}) or
            any(before.get(key)!=character[key] for key in ('game','race','character_class')) or 'resources' not in before or 'advancement' not in before):
            raise ValueError('Invalid later Heroes snapshot')
        gains = event['power_hp_rolls']
        validate_power_gain_receipts(gains,rules)
        if event['level'] <= character['level']:
            for acquisition in character.get('hero_powers',{}).get('acquisitions',[]):
                if acquisition['power'] in rules['power_hp_gains'] and gains.get(acquisition['id'],{}).get('power') != acquisition['power']:
                    raise ValueError('Each attained level requires its power gain')
        seen.append(event['level'])
    if seen != sorted(set(seen)) or (not history_frame and not set(range(3,character['level']+1)).issubset(seen)):
        raise ValueError('Every later Heroes level requires ordered unique gains')


def validate_power_gain_receipts(gains,rules):
    if not isinstance(gains,dict) or len(gains)>1000:
        raise ValueError('Invalid power advancement gains')
    for identifier,gain in gains.items():
        try:
            if not isinstance(identifier,str) or str(UUID(identifier)) != identifier:raise ValueError('Invalid power advancement identity')
        except (ValueError,AttributeError):raise ValueError('Invalid power advancement identity') from None
        if not isinstance(gain,dict) or set(gain) != {'power','face','source'} or not isinstance(gain['power'],str):
            raise ValueError('Invalid power advancement gain')
        definition = rules['power_hp_gains'].get(gain['power'])
        if definition is None or type(gain['face']) is not int or not 1 <= gain['face'] <= definition['sides'] or gain['source'] != definition['source']:
            raise ValueError('Power advancement gain must match its reviewed source')
