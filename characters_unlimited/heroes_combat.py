"""Reviewed Heroes ordinary-human combat, separate from Rifts combat tables."""

from copy import deepcopy
from .combat import total


def project_hero_combat(character, pack, physical):
    rules = pack.get('combat')
    if rules is None:
        return {'supported':False,'training':None,'totals':{},'unarmed':[], 'sources':[],
                'guidance':['Review a rule update to add Heroes Basic combat.']}
    if character['level'] != 1:
        raise ValueError('Heroes combat advancement is not yet supported')
    active = physical['active_training']
    trained = active is not None
    training = next((row['name'] for row in physical['selected'] if row['id'] == active),'No Hand to Hand')
    pp, ps = (character['attributes'][name]['value'] for name in ('PP','PS'))
    pp_supported = 8 <= pp <= rules['pp_max']
    ps_supported = 8 <= ps <= rules['ps_max']
    pp_bonus = rules['pp_bonuses'].get(str(min(pp,30)),0)
    initiative = max(0,(pp-rules['pp_initiative_start'])//rules['pp_initiative_step']+1)
    physical_combat = physical['combat']
    attacks = {'Hero baseline':rules['baseline_attacks'], **physical_combat.get('attacks',{})}
    if not trained:
        attacks['Untrained level 1'] = rules['untrained_level_one_attacks']
    totals = {'attacks':total(attacks),
              'initiative':total({**({'P.P.':initiative} if pp_supported else {}), **physical_combat.get('initiative',{})},missing=not pp_supported),
              'damage':total({**({'Ordinary P.S.':max(0,ps-15)} if ps_supported else {}), **physical_combat.get('damage',{})},missing=not ps_supported)}
    for stat in ('strike','parry','dodge','pull_punch','roll_with_impact','disarm'):
        contributions = dict(physical_combat.get(stat,{}))
        if stat in ('strike','parry','dodge') and pp_supported:
            contributions['P.P.'] = pp_bonus
        totals[stat] = total(contributions,missing=stat in ('strike','parry','dodge') and not pp_supported)
    unarmed = []
    for definition in rules['unarmed']:
        expression = ('2 x ' if definition['power'] else '')+definition['dice']
        bonus = totals['damage']['value']
        damage = expression+(f' + {bonus}' if bonus else '')+' S.D.C.' if bonus is not None else None
        unarmed.append({**deepcopy(definition),'damage':damage})
    guidance = list(rules['guidance'])
    if not pp_supported:
        guidance.append('P.P. below 8 or above 50: affected combat totals remain blank pending reviewed low-attribute or limit rules.')
    if not ps_supported:
        guidance.append('P.S. below 8 or above the ordinary human limit of 40: damage remains blank pending reviewed low-attribute or enhanced-strength rules.')
    if len(physical['training_choices']) > 1:
        guidance.append('Multiple training choices are retained; only the active profile contributes. Choose an active style below. The book permits one Hand to Hand skill; extra choices remain on the honor system.')
    return {'supported':True,'training':training,'active_training':active,
            'training_choices':deepcopy(physical['training_choices']),'training_receipts':deepcopy(physical['training_receipts']),
            'training_selection_supported':'training_skill_ids' in rules,
            'totals':totals,'unarmed':unarmed,'parry_actions':0 if trained else 1,'dodge_actions':1,
            'guidance':guidance,'sources':[deepcopy(rules['source']),deepcopy(rules['attribute_source'])],
            'rules':{'id':pack['id'],'version':pack['version']}}
