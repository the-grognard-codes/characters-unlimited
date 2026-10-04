"""Reviewed level-one ordinary-human combat, with missing mechanics left absent."""

from collections import Counter
from copy import deepcopy
from .saving_bonuses import project_saving_bonuses
from .physical import project_physical
from typing import Any
from .advancement import learning_age


def validate_combat_choices(choices, pack):
    rules = pack.get('combat')
    if not rules:
        raise ValueError('Preview a rule update before selecting combat training')
    if not isinstance(choices, dict) or set(choices) - {'hand_to_hand', 'ancient', 'modern'}:
        raise ValueError('Provide combat training choices')
    hand = choices.get('hand_to_hand', rules['default_hand_to_hand'])
    if not isinstance(hand, str) or hand not in {item['id'] for item in rules['hand_to_hand']}:
        raise ValueError('Select an available hand-to-hand skill')
    result: dict[str, Any] = {'hand_to_hand': hand}
    for family in ('ancient', 'modern'):
        selected = choices.get(family, [])
        available = {item['id'] for item in rules[family]}
        if not isinstance(selected, list) or len(selected) > 1000 or any(not isinstance(item, str) or item not in available for item in selected):
            raise ValueError('Select available weapon proficiencies')
        result[family] = list(selected)
    return result


def combat_skill_cost(character, pack):
    if 'combat' not in pack:
        return 0
    choices = validate_combat_choices(character.get('combat_choices', {}), pack)
    return next(item['cost'] for item in pack['combat']['hand_to_hand'] if item['id'] == choices['hand_to_hand'])


def total(contributions, *, missing=False, actions=1):
    return {'value': None if missing else sum(contributions.values()), 'contributions': contributions, 'actions': actions}


def progressed(definition, age):
    """Accumulate only the training levels this character has actually learned."""
    effective = dict(definition)
    if 'conditions' in definition:
        effective['conditions'] = deepcopy(definition['conditions'])
    moves: list[dict[str, Any]] = deepcopy(definition.get('moves', []))
    notes: list[str] = [f"{definition['name']}: {note}" for note in definition.get('move_notes', [])]
    if 'progression' in definition:
        for step in definition['progression']:
            if step['level'] > age:
                continue
            for stat, gain in step['bonuses'].items():
                effective[stat] = effective.get(stat, 0) + gain
            moves.extend(step['moves'])
            notes.extend(f"{definition['name']}, training level {step['level']}: {note}"
                         for note in step['notes'])
            if step.get('conditions'):
                effective.setdefault('conditions', {}).update(deepcopy(step['conditions']))
    elif age > 1:
        for stat, gain in definition.get('level_two', {}).items():
            effective[stat] = effective.get(stat, 0) + gain
        moves.extend({**move, 'power_eligible': True} for move in definition.get('level_two_moves', []))
    return effective, moves, notes


def project_combat(character, pack):
    saving_bonuses, saving_notes = project_saving_bonuses(character, pack)
    class_rules = pack.get('class_bonuses',{})
    class_bonuses = ({'perception':{'value':class_rules['perception'],
        'contributions':{'O.C.C.':class_rules['perception']},'sources':[class_rules['source']]}}
        if character['character_class'] == class_rules.get('class_id') else {})
    rules = pack.get('combat')
    gaps = ['Other Physical skills, remaining proficiencies, equipment attacks, other saving modifiers and targets, enhanced strength types and combat advancement are pending.']
    if 'advancement' in pack:
        if pack.get('higher_advancement', {}).get('max_level', 2) > 2:
            gaps[0] = 'Other Physical skills, remaining proficiencies, other saving modifiers and targets, enhanced strength types and other character paths remain pending. Reviewed class advancement ends at level fifteen.'
        else:
            gaps[0] = 'Other Physical skills, remaining proficiencies, other saving modifiers and targets, enhanced strength types and progression after level two remain pending.'
    if character['rules']['version'] == '1.0.0':
        gaps.insert(0, 'This saved primary rule version has no class attribute bonuses; combat uses the attributes currently displayed. An explicit primary-rule upgrade remains pending.')
    if not rules:
        return {'catalog': None, 'totals': {}, 'melee': [], 'shooting': [], 'unarmed': [], 'warnings': [],
                'gaps': ['Preview a rule update to incorporate reviewed combat training.', *gaps], 'sources': [], 'remaining': {}}
    choices = validate_combat_choices(character.get('combat_choices', {}), pack)
    hand = next(item for item in rules['hand_to_hand'] if item['id'] == choices['hand_to_hand'])
    hand, learned_moves, progression_notes = progressed(hand, learning_age(character, 'hand', hand['id']))
    pp, ps, speed = (character['attributes'][name]['value'] for name in ('PP','PS','SPD'))
    pp_bonus = rules['pp_bonuses'].get(str(min(pp,30)),0)
    low_pp = pp < 8
    if low_pp:
        gaps.append('P.P. below 8: combat penalties and bonus ordering are pending; affected accuracy/defense totals are blank.')
    initiative = min(6,max(0,(pp-28)//3))
    slow = -1 if speed <= 6 else 0
    physical = project_physical(character,pack)
    totals = {'attacks':total({'hand_to_hand':hand['attacks'],
                              **physical['combat'].get('attacks',{})}),
              'initiative':total({'physical_prowess':initiative,'slow_speed':slow, **({'hand_to_hand':hand['initiative']} if 'initiative' in hand else {})},missing=low_pp)}
    for stat in ('strike','parry','dodge','pull_punch','roll_with_impact','disarm'):
        contributions = {'hand_to_hand':hand.get(stat,0)}
        contributions.update(physical['combat'].get(stat,{}))
        if stat in ('strike','parry','dodge'): contributions['physical_prowess']=pp_bonus
        if stat=='dodge': contributions['slow_speed']=slow
        totals[stat]=total(contributions,missing=low_pp)
    if 'entangle' in hand:
        totals['entangle'] = total({'hand_to_hand': hand['entangle']}, missing=low_pp)
    if 'thrown_strike' in hand:
        totals['thrown_strike'] = total({'hand_to_hand': hand['thrown_strike'], 'physical_prowess': pp_bonus}, missing=low_pp)
    totals['gun_dodge']=total({'physical_prowess':pp_bonus,'slow_speed':slow},missing=low_pp)
    damage_bonus=max(0,ps-15)
    physical_damage = {'normal_strength': damage_bonus}
    if (ps >= 8 or 3 <= ps <= 4) and hand.get('damage'):
        physical_damage['hand_to_hand'] = hand['damage']
    totals['damage']=total(physical_damage,missing=ps < 1)
    unarmed=[]
    attacks = [('punch','Punch','1D4',False,1,'punch'),('kick','Kick','1D8',False,1,'kick'),('power-punch','Power punch','1D4',True,2,'punch')]
    if hand.get('power_kick', False):
        attacks.append(('power-kick','Power kick','1D8',True,2,'kick'))
    for move in learned_moves:
        category = move.get('damage_type', 'kick' if 'kick' in move['id'] else 'punch')
        attacks.append((move['id'], move['name'], move.get('dice'), False, move.get('actions', 1), category))
        if move.get('dice') and move.get('power_eligible', False):
            attacks.append(('power-' + move['id'], 'Power ' + move['name'].lower(), move['dice'], True, 2, category))
    for identifier,name,dice,power,actions,category in attacks:
        if dice is None:
            unarmed.append({'id':identifier,'name':name,'damage':None,'actions':actions})
            continue
        expression = ('2 × ' if power else '') + dice
        if ps < 1:
            damage='Pending strength interpretation'
        elif ps <= 2:
            damage = ('Pending low-strength maneuver interpretation' if category == 'maneuver' else
                      ('Pending low-strength power-kick interpretation' if category == 'kick' else
                       'Pending low-strength power-punch interpretation') if power else
                      '1D4 S.D.C.' if category == 'kick' else '1 S.D.C.')
        elif ps <= 4:
            bonus = totals['damage']['value'] or 0
            damage='½ × (' + expression + (' + ' + str(bonus) if bonus else '') + ') S.D.C.'
        else:
            bonus = totals['damage']['value'] or 0
            damage=expression + (' + ' + str(bonus) if bonus else '') + ' S.D.C.'
        unarmed.append({'id':identifier,'name':name,'damage':damage,'actions':actions})
    if ps < 3:
        gaps.append('Low-strength power-punch and power-kick damage remains pending; normal punch/kick exceptions are shown.'
                    if hand.get('power_kick', False) else
                    'Low-strength power-punch damage remains pending; normal punch/kick exceptions are shown.')
    melee=[]
    for definition in rules['ancient']:
        if definition['id'] not in choices['ancient']: continue
        definition, _, _ = progressed(definition, learning_age(character, 'weapon', definition['id']))
        melee.append({'id':definition['id'],'name':definition['name'], 'source':definition['source'],
                      'strike':total({**totals['strike']['contributions'],'weapon_proficiency':definition['strike']},missing=low_pp),
                      'parry':total({**totals['parry']['contributions'],'weapon_proficiency':definition['parry']},missing=low_pp),
                      'thrown':total({'physical_prowess':pp_bonus,'hand_to_hand':hand.get('thrown_strike',0),
                                     'weapon_proficiency':definition.get('thrown',0)},missing=low_pp)})
    shooting=[]
    for definition in rules['modern']:
        trained=definition['id'] in choices['modern']
        definition, _, _ = progressed(definition, learning_age(character, 'weapon', definition['id']))
        bonus=definition['strike'] if trained else 0
        gun_bonus = hand.get('gun_strike', 0)
        gun_contribution = {'hand_to_hand_guns':gun_bonus} if gun_bonus else {}
        shooting.append({'id':definition['id'],'name':definition['name'],'trained':trained,'source':definition['source'],
                         'single':total({'weapon_proficiency':bonus,**gun_contribution},missing=low_pp),
                         'aimed':total({'weapon_proficiency':bonus,**gun_contribution,'aimed':2},missing=low_pp or not trained,actions=2),
                         'burst':total({'weapon_proficiency_halved':bonus//2,**gun_contribution} if trained else {'untrained':-3,**gun_contribution},missing=low_pp),
                         'wild':total({'weapon_proficiency':bonus,**gun_contribution,'shooting_wild':-6},missing=low_pp)})
    warnings=[hand['name']+': unverified prerequisite — '+requirement+'. Choice retained.' for requirement in hand.get('unverified_requirements',[])]
    remaining={}
    eligible_count = 0
    for family in ('ancient','modern'):
        allowed=rules['required_proficiencies'][family]
        eligible={identifier for identifier in choices[family] if allowed=='any' or identifier in allowed}
        eligible_count += len(eligible)
        if 'combined_proficiency_count' not in rules:
            remaining[family]=1-sum(identifier in eligible for identifier in choices[family])
        if any(identifier not in eligible for identifier in choices[family]):
            guidance = 'choose an eligible energy weapon.' if remaining.get(family, 1) > 0 else 'required slot is filled; extra training is retained.'
            warnings.append(f'{family.title()}: retained proficiency does not satisfy the required O.C.C. slot; {guidance}')
        if any(count>1 for count in Counter(choices[family]).values()):
            warnings.append(f'{family.title()}: duplicate proficiency choices are retained without multiplying their bonuses.')
    if 'combined_proficiency_count' in rules:
        remaining['proficiencies'] = rules['combined_proficiency_count'] - eligible_count
    for family, count in remaining.items():
        if count<0: warnings.append(f'{family.title()}: {-count} selection(s) over the allowance; retained.')
    attribute_source = {'book':'Rifts - Ultimate Edition','pages':[281,283,284]}
    for name,result in totals.items():
        if name == 'attacks':
            result['sources'] = [hand['source']]
        elif name == 'gun_dodge':
            result['sources'] = [attribute_source]
        elif name in ('damage', 'initiative'):
            result['sources'] = [attribute_source]
            if hand.get(name) and (name != 'damage' or ps >= 8 or 3 <= ps <= 4):
                result['sources'].append(hand['source'])
        else:
            result['sources'] = [hand['source'], attribute_source]
        result['sources'].extend(item['source'] for item in physical['selected'] if name in item.get('combat',{}))
    for item in melee:
        for stat in ('strike','parry','thrown'): item[stat]['sources'] = [hand['source'],attribute_source,item['source']]
        for stat in ('strike','parry','thrown'):
            item[stat]['sources'].extend(skill['source'] for skill in physical['selected'] if stat in skill.get('combat',{}))
    for item in shooting:
        for context in ('single','aimed','burst','wild'):
            item[context]['sources'] = [item['source'],{'book':'Rifts - Ultimate Edition','pages':[361]}]
            if hand.get('gun_strike'):
                item[context]['sources'].append(hand['source'])
    notes = ['Shooting contexts are training examples; actual weapon modes, burst lengths, ammunition and capacity remain pending.',
             'Gun shooting excludes P.P., general hand-to-hand strike and strength damage bonuses. Assassin’s explicit gun-strike gains apply separately from W.P.; bursts halve only the W.P. contribution. Untrained shooters cannot make aimed shots.',
             'Gun dodge requires seeing the attacker and knowing the shot is coming; subtract 10 within 10 feet or 5 within 50 feet. Athletics and hand-to-hand dodge bonuses do not apply to gunfire or energy blasts (p. 361).',
             'Power punch uses two actions and doubles base dice before adding the normal-human strength bonus.',
             'Paired Weapons is granted by Assassin training; simultaneous action resolution remains pending.' if hand.get('paired_weapons') else 'Other special hand-to-hand moves remain pending.',
             *progression_notes]
    return {'catalog':rules,'choices':choices,'totals':totals,'class_bonuses':class_bonuses,'melee':melee,'shooting':shooting,'unarmed':unarmed,
            'conditions':deepcopy(hand.get('conditions', {})),
            'saving_bonuses':saving_bonuses,'saving_notes':saving_notes,
            'remaining':remaining,'warnings':warnings,'gaps':gaps,'notes':notes,'sources':[rules['source']], 'related_cost':hand['cost']}


def compare_combat_views(before, after):
    def index(view):
        result: dict[tuple[Any, ...], dict[str, Any]] = {('total',name): {'name':name.replace('_',' ').title(), 'value':value['value']} for name,value in view['totals'].items()}
        for group,stats in [('melee',('strike','parry','thrown')),('shooting',('single','aimed','burst','wild'))]:
            for item in view[group]:
                for stat in stats:
                    result[(group,item['id'],stat)]={'name':item['name']+' — '+stat, 'value':item[stat]['value']}
        for item in view['unarmed']:
            result[('unarmed',item['id'])]={'name':item['name']+' damage', 'value':item['damage']}
        for identifier, condition in view.get('conditions', {}).items():
            low, high = condition['natural_min'], condition['natural_max']
            value = f'Natural {low}' + (f'–{high}' if low != high else '')
            result[('condition',identifier)] = {'name':identifier.replace('_',' ').title() + ' natural roll', 'value':value}
        for identifier, bonus in view.get('saving_bonuses', {}).items():
            result[('saving', identifier)] = {'name': bonus['name'] + ' (reviewed bonus)' + bonus['unit'],
                                             'value': bonus['value']}
        for identifier,bonus in view.get('class_bonuses',{}).items():
            result[('class',identifier)]={'name':identifier.title()+' (O.C.C. bonus)','value':bonus['value']}
        return result
    previous,following=index(before),index(after)
    return [{'name':following.get(key,previous.get(key))['name'],
             'before':previous.get(key,{}).get('value'), 'after':following.get(key,{}).get('value')}
            for key in dict.fromkeys([*following,*previous])]
