"""Reviewed level-one ordinary-human combat, with missing mechanics left absent."""

from collections import Counter
from typing import Any


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


def project_combat(character, pack):
    rules = pack.get('combat')
    gaps = ['Physical skills, remaining proficiencies, equipment attacks, saving throws, enhanced strength types and combat advancement are pending.']
    if character['rules']['version'] == '1.0.0':
        gaps.insert(0, 'This saved primary rule version has no class attribute bonuses; combat uses the attributes currently displayed. An explicit primary-rule upgrade remains pending.')
    if not rules:
        return {'catalog': None, 'totals': {}, 'melee': [], 'shooting': [], 'unarmed': [], 'warnings': [],
                'gaps': ['Preview a rule update to incorporate reviewed combat training.', *gaps], 'sources': [], 'remaining': {}}
    choices = validate_combat_choices(character.get('combat_choices', {}), pack)
    hand = next(item for item in rules['hand_to_hand'] if item['id'] == choices['hand_to_hand'])
    pp, ps, speed = (character['attributes'][name]['value'] for name in ('PP','PS','SPD'))
    pp_bonus = rules['pp_bonuses'].get(str(min(pp,30)),0)
    low_pp = pp < 8
    if low_pp:
        gaps.append('P.P. below 8: combat penalties and bonus ordering are pending; affected accuracy/defense totals are blank.')
    initiative = min(6,max(0,(pp-28)//3))
    slow = -1 if speed <= 6 else 0
    totals = {'attacks':total({'hand_to_hand':hand['attacks']}),
              'initiative':total({'physical_prowess':initiative,'slow_speed':slow},missing=low_pp)}
    for stat in ('strike','parry','dodge','pull_punch','roll_with_impact','disarm'):
        contributions = {'hand_to_hand':hand.get(stat,0)}
        if stat in ('strike','parry','dodge'): contributions['physical_prowess']=pp_bonus
        if stat=='dodge': contributions['slow_speed']=slow
        totals[stat]=total(contributions,missing=low_pp)
    totals['gun_dodge']=total({'physical_prowess':pp_bonus,'slow_speed':slow},missing=low_pp)
    damage_bonus=max(0,ps-15)
    totals['damage']=total({'normal_strength':damage_bonus},missing=ps < 1)
    unarmed=[]
    for identifier,name,dice,power in [('punch','Punch','1D4',False),('kick','Kick','1D8',False),('power-punch','Power punch','1D4',True)]:
        expression = ('2 × ' if power else '') + dice
        if ps < 1:
            damage='Pending strength interpretation'
        elif ps <= 2:
            damage = ('Pending low-strength power-punch interpretation' if power else '1 S.D.C.' if identifier=='punch' else '1D4 S.D.C.')
        elif ps <= 4:
            damage='½ × (' + expression + ') S.D.C.'
        else:
            damage=expression + (' + ' + str(damage_bonus) if damage_bonus else '') + ' S.D.C.'
        unarmed.append({'id':identifier,'name':name,'damage':damage,'actions':2 if power else 1})
    if ps < 3:
        gaps.append('Low-strength power-punch damage remains pending; normal punch/kick exceptions are shown.')
    melee=[]
    for definition in rules['ancient']:
        if definition['id'] not in choices['ancient']: continue
        melee.append({'id':definition['id'],'name':definition['name'], 'source':definition['source'],
                      'strike':total({**totals['strike']['contributions'],'weapon_proficiency':definition['strike']},missing=low_pp),
                      'parry':total({**totals['parry']['contributions'],'weapon_proficiency':definition['parry']},missing=low_pp)})
    shooting=[]
    for definition in rules['modern']:
        trained=definition['id'] in choices['modern']
        bonus=definition['strike'] if trained else 0
        shooting.append({'id':definition['id'],'name':definition['name'],'trained':trained,'source':definition['source'],
                         'single':total({'weapon_proficiency':bonus},missing=low_pp),
                         'aimed':total({'weapon_proficiency':bonus,'aimed':2},missing=low_pp or not trained,actions=2),
                         'burst':total({'weapon_proficiency_halved':bonus//2} if trained else {'untrained':-3},missing=low_pp),
                         'wild':total({'weapon_proficiency':bonus,'shooting_wild':-6},missing=low_pp)})
    warnings=[hand['name']+': unverified prerequisite — '+requirement+'. Choice retained.' for requirement in hand.get('unverified_requirements',[])]
    remaining={}
    for family in ('ancient','modern'):
        allowed=rules['required_proficiencies'][family]
        eligible=[identifier for identifier in choices[family] if allowed=='any' or identifier in allowed]
        remaining[family]=1-len(eligible)
        if len(eligible) != len(choices[family]):
            guidance = 'choose an eligible energy weapon.' if remaining[family] > 0 else 'required slot is filled; extra training is retained.'
            warnings.append(f'{family.title()}: retained proficiency does not satisfy the required O.C.C. slot; {guidance}')
    for family in remaining:
        if remaining[family]<0: warnings.append(f'{family.title()} proficiencies: {-remaining[family]} selection(s) over the allowance; retained.')
        if any(count>1 for count in Counter(choices[family]).values()): warnings.append(f'{family.title()}: duplicate proficiency choices are retained without multiplying their bonuses.')
    attribute_source = {'book':'Rifts - Ultimate Edition','pages':[281,283,284]}
    for name,result in totals.items():
        result['sources'] = [hand['source']] if name=='attacks' else [attribute_source] if name in ('damage','initiative','gun_dodge') else [hand['source'],attribute_source]
    for item in melee:
        for stat in ('strike','parry'): item[stat]['sources'] = [hand['source'],attribute_source,item['source']]
    for item in shooting:
        for context in ('single','aimed','burst','wild'): item[context]['sources'] = [item['source'],{'book':'Rifts - Ultimate Edition','pages':[361]}]
    notes = ['Shooting contexts are training examples; actual weapon modes, burst lengths, ammunition and capacity remain pending.',
             'Gun shooting excludes P.P., hand-to-hand strike and strength damage bonuses. Untrained shooters cannot make aimed shots.',
             'Gun dodge requires seeing the attacker and knowing the shot is coming; subtract 10 within 10 feet or 5 within 50 feet.',
             'Power punch uses two actions and doubles base dice before adding the normal-human strength bonus.',
             'Paired Weapons is granted by Assassin training; simultaneous action resolution remains pending.' if hand.get('paired_weapons') else 'Other special hand-to-hand moves remain pending.']
    return {'catalog':rules,'choices':choices,'totals':totals,'melee':melee,'shooting':shooting,'unarmed':unarmed,
            'remaining':remaining,'warnings':warnings,'gaps':gaps,'notes':notes,'sources':[rules['source']], 'related_cost':hand['cost']}


def compare_combat_views(before, after):
    def index(view):
        result: dict[tuple[Any, ...], dict[str, Any]] = {('total',name): {'name':name.replace('_',' ').title(), 'value':value['value']} for name,value in view['totals'].items()}
        for group,stats in [('melee',('strike','parry')),('shooting',('single','aimed','burst','wild'))]:
            for item in view[group]:
                for stat in stats:
                    result[(group,item['id'],stat)]={'name':item['name']+' — '+stat, 'value':item[stat]['value']}
        for item in view['unarmed']:
            result[('unarmed',item['id'])]={'name':item['name']+' damage', 'value':item['damage']}
        return result
    previous,following=index(before),index(after)
    return [{'name':following.get(key,previous.get(key))['name'],
             'before':previous.get(key,{}).get('value'), 'after':following.get(key,{}).get('value')}
            for key in dict.fromkeys([*following,*previous])]
