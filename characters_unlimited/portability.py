"""Portable save validation. Bundles contain data and never execute rule prose."""


import json
from .json_data import canonical, MAX_BYTES
from .ability_paths import project_path
from copy import deepcopy
from datetime import datetime, timezone
from uuid import UUID, uuid4
from .saving_bonuses import project_saving_bonuses
from .skill_attribute_bonuses import needs_numeric_skill_projection
from .heroes_powers import power_numeric_contributions, project_power_saves
from .creation_profiles import creation_pair
from .generation import roll_attribute, generation_settings, racial_formula, racial_sources
from .attribute_modifiers import attribute_value, class_attribute_modifier, class_effects, ATTRIBUTE_NAMES as ATTRIBUTES
from .education import validate_education
from .heroes_power_budget import validate_budget
from .heroes_powers import validate_powers, validate_power_attributes, power_resource_contributions, power_parameter_views, power_requirement_definitions, power_formula_catalog
from .heroes_programs import validate_program_selections, validate_secondary_selections
from .physical import validate_physical, validate_physical_history
from .heroes_physical import validate_hero_physical, project_hero_physical
from .heroes_kicks import validate_hero_kicks
from .resources import validate_resources, project_resources
from .skills import validate_selections, project_skills
from .heroes_programs import project_programs
from .equipment import validate_inventory
from .starting_funds import validate_starting_funds
from .starting_gear import validate_starting_gear
from .starting_choices import validate_starting_choices
from .starting_groups import validate_starting_groups
from .advancement import validate_advancement, validate_later_advancements, remember_learning
from .heroes_advancement import validate_hero_advancement, remembered_learning, advancement_power_resources
from .required_skills import validate_required_choices
from .combat import validate_combat_choices
from .class_rules import class_rules, equipment_class_rules

def integer(value):
    return type(value) is int and abs(value) <= 9_007_199_254_740_991


def validate_attributes(attributes, race):
    if not isinstance(attributes, dict) or set(attributes) - set(ATTRIBUTES):
        raise ValueError('Invalid attribute names')
    for name, value in attributes.items():
        formula = racial_formula(race, name)
        if not isinstance(value, dict) or value.get("cap") != formula.get("cap") or ("cap" in value and not integer(value["cap"])):
            raise ValueError("Attribute ceiling must match the pinned racial rule")
        if not isinstance(value, dict) or not integer(value.get('base')) or not integer(value.get('value')):
            raise ValueError('Attribute values must be supported whole numbers')
        if not integer(value.get('adjustment', 0)) or (value.get('fixed') is not None and not integer(value['fixed'])):
            raise ValueError('Invalid manual attribute value')
        for key in ('rolls', 'bonus_rolls', 'original_rolls', 'kept', 'discarded'):
            rolls = value.get(key, None if key in ('rolls', 'bonus_rolls') else [])
            if not isinstance(rolls, list) or len(rolls) > 10000 or any(not integer(die) for die in rolls):
                raise ValueError('Invalid attribute dice')
        explanation = value.get('explanation')
        source = explanation.get('source') if isinstance(explanation, dict) else None
        if not isinstance(source, dict) or any(not isinstance(source.get(key), str) for key in ('book', 'section')):
            raise ValueError('Attribute source information is missing')
        if 'generation' in value:
            validate_generation(value['generation'])
        rerolls = value.get('rerolls', [])
        if not isinstance(rerolls, list):
            raise ValueError('Invalid reroll history')
        for reroll in rerolls:
            if not isinstance(reroll, dict) or not integer(reroll.get('index')) or not isinstance(reroll.get('rolls'), list) or any(not integer(die) for die in reroll['rolls']):
                raise ValueError('Invalid reroll history')
        modifiers = value.get('modifiers', [])
        if not isinstance(modifiers, list) or len(modifiers) > 100:
            raise ValueError('Invalid attribute modifiers')
        for modifier in modifiers:
            if not isinstance(modifier, dict) or set(modifier) not in ({'id', 'value', 'rolls', 'source'}, {'id', 'value', 'rolls', 'source', 'operation'}) or not isinstance(modifier['id'], str) or not integer(modifier['value']):
                raise ValueError('Invalid attribute modifier')
            if 'operation' in modifier and modifier['operation'] not in ('add', 'minimum'):
                raise ValueError('Unsupported attribute modifier operation')
            if not isinstance(modifier['rolls'], list) or any(not integer(roll) for roll in modifier['rolls']) or not isinstance(modifier['source'], dict):
                raise ValueError('Invalid attribute modifier rolls or source')
        expected_value = attribute_value(value)
        if value['value'] != expected_value:
            raise ValueError('Attribute value does not match its fixed value or adjusted base')
        validate_recorded_roll(value, formula)


def validate_recorded_roll(value, formula):
    # Replay the exact accepted racial formula rather than inferring rules from dice.
    settings = value.get('generation', {'reroll_ones': False, 'extra_die': False})
    originals = value.get('original_rolls', value['rolls'])
    if len(originals) != formula['count'] + int(settings['extra_die'] and formula['count'] > 0):
        raise ValueError('Recorded dice do not match the racial attribute pool')
    rerolls = {item['index']: item['rolls'] for item in value.get('rerolls', [])}
    if len(rerolls) != len(value.get('rerolls', [])) or set(rerolls) - set(range(len(originals))):
        raise ValueError('Invalid reroll positions')
    sequence = []
    for index, original in enumerate(originals):
        attempts = rerolls.get(index, [original])
        if not attempts or attempts[0] != original:
            raise ValueError('Reroll attempts do not match the original die')
        sequence.extend(attempts)
    sequence.extend(value['bonus_rolls'])
    dice = iter(sequence)
    expected = roll_attribute(formula, settings, lambda sides: next(dice, 0), value['explanation']['source'])
    if next(dice, None) is not None:
        raise ValueError('Recorded dice contain unexplained extra rolls')
    for key in ('base', 'rolls', 'bonus_rolls'):
        if value[key] != expected[key]:
            raise ValueError(f'Recorded {key} does not match the generation rules')
    for key in ('original_rolls', 'kept', 'discarded', 'rerolls'):
        if key in value and value[key] != expected[key]:
            raise ValueError(f'Recorded {key} does not match the generation rules')


def validate_generation(value):
    if not isinstance(value, dict) or set(value) != {'reroll_ones', 'extra_die'} or any(type(option) is not bool for option in value.values()):
        raise ValueError('Invalid generation options')


def validate_character(character, core):
    if not isinstance(character, dict) or type(character.get('format_version')) is not int or character['format_version'] != 1:
        raise ValueError('Unsupported character format version')
    if character.get('game') != core['game'] or not any(r['id'] == character.get('race') for r in core['races']) or not any(c['id'] == character.get('character_class') for c in core['classes']):
        raise ValueError('This application version cannot reopen that game or character option')
    creation_pair(core, character['race'], character['character_class'])
    try:
        UUID(character['id'])
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise ValueError('Invalid character identity') from error
    for key in ('name', 'notes'):
        if not isinstance(character.get(key), str):
            raise ValueError(f'{key} must be text')
    if type(character.get('level')) is not int or not 1 <= character['level'] <= 15:
        raise ValueError('Unsupported character level')
    if 'experience' in character and (type(character['experience']) is not int or character['experience'] < 0):
        raise ValueError('Experience must match a reviewed level range')
    for key in ('completion', 'automation_gaps'):
        if not isinstance(character.get(key), list) or any(not isinstance(item, str) for item in character[key]):
            raise ValueError(f'Invalid {key}')
    attributes = character.get('attributes')
    if not isinstance(attributes, dict):
        raise ValueError('Attribute records are missing')
    race = next(r for r in core["races"] if r["id"] == character["race"])
    validate_attributes(attributes, race)
    if set(attributes) != set(ATTRIBUTES):
        raise ValueError('The character must retain all eight attribute records')
    if 'generation' in character:
        validate_generation(character['generation'])
    history = character.get('roll_history', [])
    if not isinstance(history, list):
        raise ValueError('Invalid roll history')
    for event in history:
        if not isinstance(event, dict) or not isinstance(event.get('kind'), str):
            raise ValueError('Invalid roll history entry')
        if event.get('at') is not None:
            try:
                datetime.fromisoformat(event['at'])
            except (TypeError, ValueError) as error:
                raise ValueError('Invalid roll history date') from error
        validate_attributes(event.get('attributes'), race)
        if 'generation' in event:
            validate_generation(event['generation'])


def pinned_packs(character, packs, *, include_history=True):
    primary = character.get('rules')
    additional = character.get('additional_rule_packs', {})
    if not isinstance(primary, dict) or not isinstance(additional, dict):
        raise ValueError('Rule version pins are missing')
    pins = {**additional}
    if not isinstance(primary.get('id'), str) or not isinstance(primary.get('version'), str):
        raise ValueError('Invalid primary rule version')
    if primary['id'] in pins and pins[primary['id']] != primary['version']:
        raise ValueError('Conflicting rule version pins')
    pins[primary['id']] = primary['version']
    result = []
    for identifier, version in pins.items():
        match = next((pack for pack in packs if pack['id'] == identifier and pack['version'] == version), None)
        if match is None:
            raise ValueError(f'Unsupported rule version: {identifier} {version}')
        result.append(deepcopy(match))
    if include_history:
        snapshots: list = []
        if isinstance(character.get('advancement'), dict):
            initial = character['advancement'].get('before')
            if not isinstance(initial, dict) or 'advancement' in initial or 'later_advancements' in initial:
                raise ValueError('Invalid flat initial advancement snapshot')
            snapshots.append(initial)
        events = character.get('later_advancements', [])
        if not isinstance(events, list) or len(events) > 13:
            raise ValueError('Invalid later advancement history')
        snapshots.extend(event.get('before') if isinstance(event, dict) else None for event in events)
        for before in snapshots:
            if not isinstance(before, dict):
                raise ValueError('Missing advancement snapshot')
            if 'later_advancements' in before:
                raise ValueError('Later advancement snapshots must stay flat')
            for pack in pinned_packs(before, packs):
                if not any(item['id'] == pack['id'] and item['version'] == pack['version'] for item in result):
                    result.append(pack)
    return result


def export_bundle(character, packs):
    canonical(character)
    expected = pinned_packs(character, packs)
    core = primary_pack(character, expected)
    validate_character(character, core)
    validate_sources(character, expected)
    bundle = {'format': 'characters-unlimited', 'bundle_version': 1,
              'character': deepcopy(character), 'rule_packs': pinned_packs(character, packs)}
    canonical(bundle)
    return bundle


def import_bundle(bundle, packs):
    canonical(bundle)
    if not isinstance(bundle, dict) or bundle.get('format') != 'characters-unlimited' or type(bundle.get('bundle_version')) is not int or bundle['bundle_version'] != 1:
        raise ValueError('Unsupported portable bundle format')
    character = bundle.get('character')
    if not isinstance(character, dict):
        raise ValueError('The character record is missing')
    expected = pinned_packs(character, packs)
    core = primary_pack(character, expected)
    validate_character(character, core)
    validate_sources(character, expected)
    if character['game'] == 'rifts' and 'rifts-domestic-skills' not in character.get('additional_rule_packs', {}):
        raise ValueError('The skill projection must retain its rule version pin')
    supplied = bundle.get('rule_packs')
    if not isinstance(supplied, list) or len(supplied) != len(expected):
        raise ValueError('The exact pinned rule definitions must be included')
    for pack in expected:
        if not any(canonical(candidate) == canonical(pack) for candidate in supplied):
            raise ValueError(f"Missing or altered rule definitions: {pack['id']} {pack['version']}")
    return fresh_copy(character)


def primary_pack(character, packs):
    primary = character['rules']
    core = next((pack for pack in packs if pack['id'] == primary['id'] and pack['version'] == primary['version']), None)
    expected_id = {'rifts': 'rifts-core', 'heroes-unlimited': 'heroes-core'}.get(character.get('game'))
    if core is None or core['id'] != expected_id or core.get('game') != character.get('game') or any(pack.get('game') != character['game'] for pack in packs):
        raise ValueError('The pinned rule definitions must match the selected game')
    return core


def validate_sources(character, packs, *, history_frame=False):
    core = primary_pack(character, packs)
    psychic_snapshot = None
    if 'psionics' in character:
        version = character.get('additional_rule_packs', {}).get('rifts-natural-psionics')
        psychic_pack = next((row for row in packs if row['id'] == 'rifts-natural-psionics' and row['version'] == version), None)
        if character['game'] != 'rifts' or psychic_pack is None:
            raise ValueError('Natural psionics must retain their exact Rifts rule pin')
        project_path(character, psychic_pack, character['psionics'])
        record = character['psionics']['resource_record']
        if record is not None:
            psychic_snapshot = record['resource_attribute_snapshot']
            race = next(row for row in core['races'] if row['id'] == character['race'])
            validate_attributes(psychic_snapshot, race)
    def current_hero_pack(identifier):
        version = character.get('additional_rule_packs',{}).get(identifier)
        return next((item for item in packs if item['id']==identifier and item['version']==version),None)
    power_pack = current_hero_pack('heroes-super-abilities')
    if power_pack is not None:
        power_parameter_views(power_pack, character['level'])
        power_requirement_definitions(power_pack)
        power_formula_catalog(power_pack)
        power_numeric_contributions(power_pack)
    if 'hero_powers' in character:
        if character['game'] != 'heroes-unlimited' or power_pack is None or character['character_class'] != power_pack['character_class']:
            raise ValueError('Heroes powers must retain their accepted rule version pin')
        validate_powers(character['hero_powers'], power_pack)
        active = character['hero_powers']['active']
        selected = {row['power'] for row in character['hero_powers']['acquisitions'] if row['id'] in active}
        project_power_saves(character, power_pack, [row for row in power_pack['powers'] if row['id'] in selected])
    if 'equipment' in character or 'starting_funds' in character or 'starting_gear' in character or 'starting_choices' in character or 'starting_equipment_groups' in character:
        equipment_pack = next((item for item in packs if item['id']=='rifts-equipment'),None)
        if character['game'] != 'rifts' or equipment_pack is None:
            raise ValueError('Rifts equipment must retain its accepted rule version pin')
        if 'equipment' not in character:
            raise ValueError('Starting funds require their recorded equipment inventory')
        equipment_pack = equipment_class_rules(equipment_pack, character)
        validate_inventory(character['equipment'],equipment_pack)
        validate_starting_funds(character,equipment_pack)
        validate_starting_gear(character,equipment_pack)
        validate_starting_choices(character,equipment_pack)
        validate_starting_groups(character,equipment_pack)
    skill_pack = next((item for item in packs if item['id']=='rifts-domestic-skills'),None)
    if skill_pack is not None:
        skill_pack = class_rules(skill_pack, character)
        project_saving_bonuses(character, skill_pack)
    resource_pack = skill_pack
    if character['game'] == 'heroes-unlimited':
        resource_pack = current_hero_pack('heroes-resources')
        if resource_pack is not None and (character['character_class'] != resource_pack['character_class'] or
                                         character['race'] != resource_pack['race']):
            raise ValueError('Heroes resources must match their reviewed race and power category')
    validate_resources(character,resource_pack or {})
    if skill_pack is not None:
        validate_advancement(character, skill_pack)
        validate_later_advancements(character, skill_pack, history_frame=history_frame)
        validate_selections(character.get('skill_selections',[]),skill_pack)
        if 'required_skill_choices' in character:
            validate_required_choices(character['required_skill_choices'], skill_pack)
        if 'combat_choices' in character:
            validate_combat_choices(character['combat_choices'], skill_pack)
        validate_physical(character,skill_pack)
        if needs_numeric_skill_projection(skill_pack):
            project_skills(character, skill_pack)
        for event in character.get('roll_history', []):
            validate_physical_history(event['attributes'],character.get('physical_acquisitions',{}),skill_pack)
    elif 'physical_acquisitions' in character and character['game'] != 'heroes-unlimited':
        raise ValueError('Physical skill acquisitions must retain their Rifts rule version')
    elif character['game'] == 'heroes-unlimited':
        pins = character.get('additional_rule_packs',{})
        validate_hero_advancement(character, next((item for item in packs if item['id']=='heroes-advancement' and item['version']==pins.get(item['id'])),None),
            current_hero_pack('heroes-program-skills'),
            current_hero_pack('heroes-education'),
            higher=next((item for item in packs if item['id']=='heroes-higher-advancement' and item['version']==pins.get(item['id'])),None),history_frame=history_frame)
    elif 'advancement' in character or 'later_advancements' in character or 'learning_levels' in character or character['level'] != 1:
        raise ValueError('Advancement must retain its Rifts rule version')
    if 'advancement' in character:
        before = {**character['advancement']['before'], 'id': character['id'],
                  'revision': 0, 'updated_at': character['updated_at']}
        historical = pinned_packs(before, packs, include_history=False)
        validate_character(before, primary_pack(before, historical))
        validate_sources(before, historical)
        if character['advancement']['active'] and character['game'] == 'heroes-unlimited':
            old_skills = next((item for item in historical if item['id']=='heroes-program-skills'),None)
            old_education = next((item for item in historical if item['id']=='heroes-education'),None)
            old_skills = old_skills or next(item for item in packs if item['id']=='heroes-program-skills')
            old_education = old_education or next(item for item in packs if item['id']=='heroes-education')
            if old_skills is not None and old_education is not None:
                initial = remembered_learning(before,old_skills,old_education)
                if any(character['learning_levels'].get(key) != 1 for key in initial):
                    raise ValueError('Pre-level Heroes skills must retain their learned level')
        if character['advancement']['active'] and character['game'] == 'rifts':
            old_skill_pack = class_rules(next(item for item in historical if item['id'] == 'rifts-domestic-skills'), before)
            initial = remember_learning(before, project_skills(before, old_skill_pack),
                validate_combat_choices(before.get('combat_choices', {}), old_skill_pack))
            levels = character['learning_levels']
            if any(levels.get(key) != 1 for key in initial):
                raise ValueError('Pre-level skills must retain their recorded learning level')
            expected = remember_learning(character, project_skills(character, skill_pack),
                validate_combat_choices(character.get('combat_choices', {}), skill_pack))
            if levels != expected:
                raise ValueError('Every current skill must retain its learned-level record')
    for event in character.get('later_advancements', []):
        before = {**event['before'], 'id': character['id'], 'revision': 0,
                  'updated_at': character['updated_at']}
        historical = pinned_packs(before, packs)
        if character['game']=='heroes-unlimited':
            historical_higher = next((item for item in historical if item['id']=='heroes-higher-advancement' and
                item['version']==before.get('additional_rule_packs',{}).get(item['id'])),None)
            if historical_higher is None:
                raise ValueError('Later Heroes snapshot must retain its exact extension pin')
            expected_source = historical_higher['source']
        else:
            old_skill_pack = class_rules(next(item for item in historical if item['id'] == 'rifts-domestic-skills'), before)
            expected_source = old_skill_pack.get('higher_advancement',{}).get('source')
        if canonical(event['source']) != canonical(expected_source):
            raise ValueError('Later advancement source must match its pinned rules')
        validate_character(before, primary_pack(before, historical))
        validate_sources(before, historical, history_frame=True)
    if 'power_budget' in character:
        pack = current_hero_pack('heroes-mutant-power-budget')
        if character['game'] != 'heroes-unlimited' or pack is None or character['character_class'] != pack['character_class']:
            raise ValueError('Mutant power budgets must retain their accepted rule version pin')
        validate_budget(character['power_budget'], pack)
    if 'education' in character:
        pack = current_hero_pack('heroes-education')
        if character['game'] != 'heroes-unlimited' or pack is None:
            raise ValueError('Heroes education must retain its accepted rule version pin')
        validate_education(character['education'], pack)
    if 'hero_program_selections' in character:
        pack = current_hero_pack('heroes-program-skills')
        if character['game'] != 'heroes-unlimited' or pack is None or 'education' not in character:
            raise ValueError('Heroes programs must retain education and their accepted rule version pin')
        validate_program_selections(character['hero_program_selections'], pack)
    if 'hero_secondary_selections' in character:
        pack = current_hero_pack('heroes-program-skills')
        if character['game']!='heroes-unlimited' or pack is None or 'education' not in character:
            raise ValueError('Heroes Secondary skills must retain education and their accepted rule version pin')
        validate_secondary_selections(character['hero_secondary_selections'],pack)
    if 'hero_combat_training' in character and character['game'] != 'heroes-unlimited':
        raise ValueError('Heroes combat training cannot cross game boundaries')
    physical_pack = skill_pack
    if character['game'] == 'heroes-unlimited':
        physical_pack = current_hero_pack('heroes-program-skills')
        education_pack = current_hero_pack('heroes-education')
        if physical_pack is not None and education_pack is not None:
            validate_hero_physical(character, physical_pack, education_pack)
            for event in character.get('roll_history', []):
                validate_physical_history(event['attributes'],character.get('physical_acquisitions',{}),physical_pack)
        elif 'physical_acquisitions' in character or 'hero_combat_training' in character:
            raise ValueError('Heroes Physical acquisitions must retain their skill and education rule pins')
    if character['game'] == 'heroes-unlimited':
        typed_powers = power_pack is not None and any(power.get('skill_effects') for power in power_pack['powers'])
        typed_skills = physical_pack is not None and physical_pack.get('skill_effects')
        if typed_powers or typed_skills:
            education_pack = current_hero_pack('heroes-education')
            if physical_pack is None or education_pack is None:
                raise ValueError('Typed skill effects require their exact skill and education pins')
            project_programs(character, physical_pack, education_pack, power_pack)
    validate_hero_kicks(character,current_hero_pack('heroes-combat-moves'))
    resource_snapshot = character.get('resource_attribute_snapshot')
    if resource_snapshot is not None:
        race = next(item for item in core['races'] if item['id']==character['race'])
        validate_attributes(resource_snapshot,race)
        if physical_pack is not None:
            validate_physical_history(resource_snapshot,character.get('physical_acquisitions',{}),physical_pack)
    validate_power_attributes(character, power_pack)
    if psychic_snapshot is not None and physical_pack is not None:
        validate_physical_history(psychic_snapshot, character.get('physical_acquisitions', {}), physical_pack)
    records = [character['attributes'], *(event['attributes'] for event in character.get('roll_history', [])),
               *([resource_snapshot] if resource_snapshot is not None else []),
               *([psychic_snapshot] if psychic_snapshot is not None else [])]
    selected_class = next(item for item in core['classes'] if item['id'] == character['character_class'])
    effects = class_effects(selected_class)
    race = next(item for item in core['races'] if item['id'] == character['race'])
    sources = racial_sources(race, core['source'])
    for attributes in records:
        for name, value in attributes.items():
            if canonical(value['explanation']['source']) != canonical(sources[name]):
                raise ValueError('Generated attribute sources must match the pinned rule definition')
            effect = effects.get(name)
            modifiers = []
            for modifier in value.get('modifiers',[]):
                if modifier['id'].startswith(('power-floor:','power-add:')):
                    continue  # Validated against retained source-bound acquisitions above.
                elif modifier['id'].startswith('physical:'):
                    definition = next((item for item in physical_pack['skills'] if item['id']==modifier['id'].removeprefix('physical:')),None) if physical_pack else None
                    if definition is None or canonical(modifier['source']) != canonical(definition['source']):
                        raise ValueError('Physical modifier sources must match their pinned rules')
                else:
                    modifiers.append(modifier)
            if effect is None:
                if modifiers:
                    raise ValueError('Attribute modifiers are unavailable in this pinned rule version')
                continue
            if len(modifiers) != 1:
                raise ValueError('The recorded class attribute contribution is required exactly once')
            modifier = modifiers[0]
            expected = class_attribute_modifier(selected_class, name, modifier['rolls'])
            if canonical(modifier) != canonical(expected):
                raise ValueError('Recorded class attribute contribution does not match the pinned rules')

    growth_records = [character.get('advancement', {}), *character.get('later_advancements', [])]
    if (resource_pack is not None and character.get('advancement', {}).get('active') and
            any(record.get('resource_gains') for record in growth_records)):
        physical_resources = power_resources = None
        if character['game'] == 'heroes-unlimited':
            physical_resources = project_hero_physical(character, physical_pack, current_hero_pack('heroes-education'))['resources']
            power_resources = [*power_resource_contributions(character, power_pack),
                               *advancement_power_resources(character, current_hero_pack('heroes-advancement'))]
        project_resources(character, resource_pack, physical_resources=physical_resources, power_resources=power_resources)


def fresh_copy(character):
    result = deepcopy(character)
    result['copied_from'] = character['id']
    result['id'] = str(uuid4())
    result['revision'] = 0
    result['updated_at'] = datetime.now(timezone.utc).isoformat()
    return result
