"""Reconcile alternative ordinary skill training and retained catalog identities."""

from typing import Any
from .advancement import learning_key
from .recorded_formulas import MAX_INTEGER
from .required_definitions import required_catalog
from .skill_choices import needs_specialty, selection_policy


def required_definitions(pack):
    rules=required_catalog(pack)
    if rules is None:
        return []
    return [*rules['grants'], *[row for group in rules['groups'] for row in
        (group.get('options',[]) if group['kind']=='select' else [group['skill']] if 'skill' in group else [])]]


def training_rules(pack):
    declaration=pack.get('required_skill_training')
    profiles=[pack,*pack.get('class_profiles',{}).values()]
    definitions=[row for profile in profiles for row in required_definitions({**pack, **profile})]
    if declaration is None:
        if any('catalog_skill_id' in row for row in definitions):
            raise ValueError('Required catalog references need a reviewed training declaration')
        return None
    if (not isinstance(declaration,dict) or set(declaration)!={'format','source'} or
            type(declaration['format']) is not int or declaration['format']!=1):
        raise ValueError('Invalid required skill training declaration')
    source=declaration['source']
    if (not isinstance(source,dict) or any(not isinstance(source.get(key),str) or not source[key].strip()
            for key in ('book','section'))):
        raise ValueError('Required skill training needs source evidence')
    known={row['id']:row for row in pack['skills']}
    aliases: dict[str,list[str]]={}
    for definition in definitions:
        identifier=definition.get('catalog_skill_id',definition.get('id'))
        explicit='catalog_skill_id' in definition
        if explicit and (not isinstance(identifier,str) or identifier not in known or
                         not isinstance(definition.get('id'),str) or not definition['id']):
            raise ValueError('Required catalog references must name known skill identities')
        target=known.get(identifier) if isinstance(identifier,str) else None
        ordinary=target is not None and not needs_specialty(target) and target.get('kind')!='physical'
        if explicit and not ordinary:
            raise ValueError('Required catalog references support ordinary percentile skills without specialties')
        if target is None or not ordinary:
            continue
        if (any(type(definition.get(key)) is not int or type(target.get(key)) is not int or
                definition[key]!=target[key] or not 0<=definition[key]<=MAX_INTEGER for key in ('base','per_level')) or
                type(definition.get('class_bonus')) is not int or abs(definition['class_bonus'])>MAX_INTEGER):
            raise ValueError('Required training must match its catalog base and progression with an exact class bonus')
        if explicit:
            evidence=definition.get('source')
            if (not isinstance(evidence,dict) or any(not isinstance(evidence.get(key),str) or not evidence[key].strip()
                    for key in ('book','section'))):
                raise ValueError('Required catalog references need source evidence')
            aliases.setdefault(identifier,[]).append(definition['id'])
    return aliases


def recorded_training_level(character, identifier, aliases, *, default):
    levels=character.get('learning_levels',{})
    recorded=[levels[learning_key('skill',key)] for key in (identifier,*aliases.get(identifier,[]))
              if learning_key('skill',key) in levels]
    return min(recorded) if recorded else default


def required_training_definition(definition, pack, aliases):
    if aliases is None or 'catalog_skill_id' not in definition:
        return definition
    identifier=definition.get('catalog_skill_id',definition['id'])
    target=next((row for row in pack['skills'] if row['id']==identifier),None)
    if target is None or needs_specialty(target) or target.get('kind')=='physical':
        return definition
    return {**target,**definition,'id':identifier}


def resolve_skill_training(character, pack, required, fixed, selections, derived, aliases):
    if aliases is None:
        return derived
    known={row['id']:row for row in pack['skills']}
    result: dict[str,Any]={}
    acquisitions=[{'id':row['id'],'bonus':row['contributions']['class'],'default':1}
                  for row in required if not row.get('specialty')]
    acquisitions.extend({'id':row['id'],'bonus':row['bonus'],'default':1} for row in fixed)
    acquisitions.extend({'id':item['skill_id'],'bonus':selection_policy(known[item['skill_id']],item['pool'],pack)['bonus'],
                         'default':character['level']} for item in selections if not needs_specialty(known[item['skill_id']]))
    for acquisition in acquisitions:
        identifier=acquisition['id']
        definition=known.get(identifier)
        if definition is None or definition.get('kind')=='physical' or needs_specialty(definition):
            continue
        learned=recorded_training_level(character,identifier,aliases,default=acquisition['default'])
        row=result.setdefault(identifier,{'ordinary_bonus':acquisition['bonus'],'learned_level':learned,'origins':[]})
        row['ordinary_bonus']=max(row['ordinary_bonus'],acquisition['bonus'])
        row['learned_level']=min(row['learned_level'],learned)
    for identifier,automatic in derived.items():
        row=result.setdefault(identifier,{'ordinary_bonus':automatic['ordinary_bonus'],
                                         'learned_level':automatic['learned_level'],'origins':[]})
        row['ordinary_bonus']=max(row['ordinary_bonus'],automatic['ordinary_bonus'])
        row['learned_level']=min(row['learned_level'],automatic['learned_level'])
        row.update(bonus=automatic['bonus'],origins=automatic['origins'])
    for row in result.values():
        row.setdefault('bonus',row['ordinary_bonus'])
    for grant in required:
        if grant['id'] in result and not grant.get('specialty') and 'class_ability' in grant['contributions']:
            result[grant['id']]['class_ability']=grant['contributions']['class_ability']
    return result
