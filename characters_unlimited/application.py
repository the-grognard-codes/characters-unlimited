"""Player-facing character workflows; all derived results enter through this seam."""

import secrets
import hashlib
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .storage import CharacterStore, SaveConflict
from .coverage import SourceInventory
from .generation import generation_settings, roll_attribute, racial_formulas, racial_sources
from .skills import validate_selections, project_skills, compare_skill_views
from .portability import export_bundle, import_bundle, fresh_copy, pinned_packs, canonical
from .rules import RuleArchive
from .class_rules import class_rules, equipment_class_rules
from .required_skills import validate_required_choices
from .combat import validate_combat_choices, project_combat, compare_combat_views
from .attribute_modifiers import attribute_value, roll_class_modifiers, class_effects, ATTRIBUTE_NAMES as ATTRIBUTES
from .education import education_selection, validate_education, project_education
from .heroes_power_budget import select_budget, validate_budget, project_budget
from .heroes_powers import select_powers, project_powers, power_resource_contributions
from .heroes_programs import validate_program_selections, validate_secondary_selections, project_programs
from .physical import acquire_physical, validate_physical_upgrade
from .heroes_physical import acquire_hero_physical, project_hero_physical, preserve_training_choice
from .heroes_combat import project_hero_combat
from .heroes_kicks import validate_kick_selections
from .resources import acquire_resources, project_resources, update_resource
from .equipment import validate_inventory, purchase_inventory, split_inventory, reload_inventory, project_equipment, compare_equipment_views
from .starting_funds import acquire_starting_funds
from .starting_gear import acquire_starting_gear
from .starting_choices import acquire_starting_choices
from .starting_groups import acquire_starting_group, validate_starting_group_upgrade
from .advancement import first_advance, remember_learning, learning_key, project_advancement
from .heroes_advancement import first_hero_advance, advance_higher_levels, remembered_learning, power_gains, project_hero_advancement, advancement_power_resources

def require_revision(revision):
    if type(revision) is not int or revision < 0:
        raise ValueError("A nonnegative saved revision is required")
    return revision


class CharacterApplication:
    def __init__(self, directory: str | Path, die=None, rule_archive=None):
        self.die = die or (lambda sides: secrets.randbelow(sides) + 1)
        self.rule_archive = rule_archive if rule_archive is not None else RuleArchive.load()
        self.pack = self.rule_archive.active('rifts-core')
        self.heroes_pack = self.rule_archive.active('heroes-core')
        self.skill_pack = self.rule_archive.active('rifts-domestic-skills')
        self.store = CharacterStore(directory)

    def catalog(self):
        return {"games": [{"id": "rifts", "name": "Rifts Ultimate Edition"}, {"id": "heroes-unlimited", "name": self.heroes_pack["name"]}], "packs": [deepcopy(self.pack), deepcopy(self.heroes_pack)],
                "heroes_starting_max_level":(self._hero_higher_pack({},available=True) or self.rule_archive.active('heroes-advancement'))['max_level']}

    def coverage(self):
        return SourceInventory.load()

    def create(self, name="", race="human", character_class=None, notes="", generation=None, game="rifts", level=1):
        pack = {"rifts": self.pack, "heroes-unlimited": self.heroes_pack}.get(game)
        if pack is None:
            raise ValueError("Select an available game")
        if character_class is None:
            character_class = pack["classes"][0]["id"]
        racial_rules = next((item for item in pack["races"] if item["id"] == race), None)
        selected_class = next((item for item in pack["classes"] if item["id"] == character_class), None)
        if racial_rules is None or selected_class is None:
            raise ValueError("Select an available race and class from the selected game")
        skill_pack = class_rules(self.skill_pack, {'character_class':character_class}) if game == 'rifts' else None
        maximum = (skill_pack.get('higher_advancement', {}).get('max_level', 2) if skill_pack else
                   (self._hero_higher_pack({},available=True) or self.rule_archive.active('heroes-advancement'))['max_level'])
        if type(level) is not int or not 1 <= level <= maximum:
            raise ValueError('Choose a reviewed starting level')
        if not isinstance(name, str) or not isinstance(notes, str):
            raise ValueError("Name and notes must be text")
        settings = generation_settings(generation)
        class_effects(selected_class)
        formulas = racial_formulas(racial_rules, settings)
        sources = racial_sources(racial_rules, pack["source"])
        character = {
            "id": str(uuid4()), "format_version": 1, "game": game,
            "name": name, "notes": notes, "race": race, "character_class": character_class,
            "rules": {"id": pack["id"], "version": pack["version"]},
            "additional_rule_packs": {self.skill_pack['id']: self.skill_pack['version']} if game == 'rifts' else {},
            "level": 1, "revision": 0, "attributes": {}, "generation": settings,
            "completion": ["Skills are not yet complete", "Equipment and resources are not yet complete"],
            "automation_gaps": selected_class["automation_gaps"],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        for attribute in ATTRIBUTES:
            formula = formulas[attribute]
            character["attributes"][attribute] = roll_attribute(formula, settings, self.die, sources[attribute])
        roll_class_modifiers(character['attributes'], selected_class, self.die)
        if skill_pack and skill_pack.get('physical_grants'):
            character.update(acquire_physical(character, [], skill_pack, self.die))
        character["roll_history"] = [{"kind": "initial", "at": character["updated_at"], "generation": settings, "attributes": deepcopy(character["attributes"])}]
        if level > 1:
            if game == 'heroes-unlimited':
                resource_pack = self.character_resource_pack(character)
                character.update(acquire_resources(character, resource_pack, self.die))
                character['additional_rule_packs'][resource_pack['id']] = resource_pack['version']
                character.update(self._hero_advance_changes(character, 'level', level))
                export_bundle(character, self.rule_archive.definitions())
                self.store.put(character)
                return character
            assert skill_pack is not None
            character.update(acquire_resources(character, skill_pack, self.die))
            choices = validate_combat_choices({}, skill_pack)
            levels = remember_learning(character, project_skills(character, skill_pack), choices)
            character.update(first_advance(character, skill_pack, 'level', level, levels, self.die))
            export_bundle(character, self.rule_archive.definitions())
        self.store.put(character)
        return character

    def get(self, identifier):
        character = self.store.get(identifier)
        # Earlier builds already projected this exact domestic pack without a pin.
        if character['game'] == 'rifts':
            character.setdefault('additional_rule_packs', {}).setdefault('rifts-domestic-skills', '1.0.0')
        pinned_packs(character, self.rule_archive.definitions())
        return character

    def list(self):
        return self.store.list()

    def skill_view(self, identifier):
        character = self.get(identifier)
        pack = self.character_skill_pack(character)
        return {**project_skills(character, pack), 'combat': project_combat(character, pack),
                'resources':project_resources(character,pack), 'advancement':project_advancement(character, pack)}

    def combat_view(self, identifier):
        character = self.get(identifier)
        return project_combat(character, self.character_skill_pack(character))

    def advance(self, identifier, *, revision, method, value):
        require_revision(revision)
        character = self.get(identifier)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before advancing.')
        if character['game'] == 'heroes-unlimited':
            changes = self._hero_advance_changes(character, method, value)
        else:
            pack = self.character_skill_pack(character)
            choices = validate_combat_choices(character.get('combat_choices', {}), pack)
            levels = remember_learning(character, project_skills(character, pack), choices)
            changes = first_advance(character, pack, method, value, levels, self.die)
        export_bundle({**character, **changes}, self.rule_archive.definitions())
        return self.store.update(identifier, changes, revision)

    def _hero_advance_changes(self, character, method, value):
        rules = self._character_heroes_pack(character, 'heroes-advancement')
        skills = self._character_heroes_pack(character, 'heroes-program-skills')
        education = self.character_education_pack(character)
        if 'training_skill_ids' not in skills.get('combat', {}):
            raise ValueError('Review a rule update before Heroes advancement')
        levels = remembered_learning(character, skills, education)
        higher = self._hero_higher_pack(character, available=True)
        use_higher = higher and (character['level']>2 or
            (method=='level' and type(value) is int and value>2) or
            (method=='xp' and type(value) is int and value>rules['xp_ranges'][-1][1]))
        candidate = deepcopy(character)
        if use_higher:
            candidate['additional_rule_packs'] = {**candidate.get('additional_rule_packs',{}),higher['id']:higher['version']}
            changes = advance_higher_levels(candidate,rules,higher,method,value,levels,self.die,
                {rules['id']:rules['version'],skills['id']:skills['version'],education['id']:education['version']})
        else:
            changes = first_hero_advance(character, rules, method, value, levels, self.die)
        pins = {**character.get('additional_rule_packs', {}), rules['id']:rules['version']}
        if use_higher:pins[higher['id']] = higher['version']
        if changes.get('level',character['level']) >= 2:
            pins.update({skills['id']:skills['version'], education['id']:education['version']})
        return {**changes, 'additional_rule_packs':pins}

    def _hero_higher_pack(self, character, *, available=False):
        identifier = 'heroes-higher-advancement'
        version = character.get('additional_rule_packs',{}).get(identifier)
        if version is not None:return self.rule_archive.resolve(identifier,version)
        if available and identifier in self.rule_archive.active_versions():return self.rule_archive.active(identifier)
        return None

    def _hero_learning_changes(self, character, changes, *, learned_level=None):
        if learned_level is not None and (type(learned_level) is not int or not 1 <= learned_level <= character['level']):
            raise ValueError('Choose a learned level no later than the current level')
        if character['level'] == 1:
            return changes
        candidate = {**character, **changes}
        levels = remembered_learning(candidate, self._character_heroes_pack(candidate,'heroes-program-skills'),
                                     self.character_education_pack(candidate), learned_level=learned_level)
        return {**changes, 'learning_levels':levels}

    def undo_advancement(self, identifier, *, revision):
        require_revision(revision)
        character = self.get(identifier)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before undoing advancement.')
        record = character.get('advancement')
        if not record or not record['active']:
            raise ValueError('There is no active advancement to undo')
        if character['level'] > 2:
            event = next(item for item in character['later_advancements'] if item['level'] == character['level'])
            restored = {**deepcopy(event['before']), 'id': identifier,
                        'revision': revision, 'updated_at': character['updated_at']}
        else:
            restored = {**deepcopy(record['before']), 'id': identifier,
                        'revision': revision, 'updated_at': character['updated_at'],
                        'advancement': {**deepcopy(record), 'active': False}}
        if 'later_advancements' in character:
            restored['later_advancements'] = deepcopy(character['later_advancements'])
        if character['game'] == 'heroes-unlimited':
            restored['additional_rule_packs'] = {**restored.get('additional_rule_packs',{}),
                'heroes-advancement':character['additional_rule_packs']['heroes-advancement']}
            if 'heroes-higher-advancement' in character['additional_rule_packs']:
                restored['additional_rule_packs']['heroes-higher-advancement'] = character['additional_rule_packs']['heroes-higher-advancement']
                restored['advancement']['power_hp_rolls'] = {**character['advancement']['power_hp_rolls'],
                    **restored['advancement']['power_hp_rolls']}
        recovery = fresh_copy(character)
        recovery['recovery_of'] = identifier
        export_bundle(restored, self.rule_archive.definitions())
        export_bundle(recovery, self.rule_archive.definitions())
        return self.store.restore(identifier, restored, recovery, revision)

    def _learning_changes(self, character, changes, pack):
        if character['level'] == 1:
            return changes
        candidate = {**character, **changes}
        choices = validate_combat_choices(candidate.get('combat_choices', {}), pack)
        return {**changes, 'learning_levels': remember_learning(candidate, project_skills(candidate, pack), choices)}

    def character_equipment_pack(self, character):
        if character['game'] != 'rifts':
            raise ValueError('Heroes Unlimited equipment remains unfinished')
        version = character.get('additional_rule_packs',{}).get('rifts-equipment')
        pack = (self.rule_archive.resolve('rifts-equipment',version) if version is not None
                else self.rule_archive.active('rifts-equipment'))
        return equipment_class_rules(pack, character)

    def equipment_view(self, identifier):
        character = self.get(identifier)
        return project_equipment(character,self.character_equipment_pack(character),
                                 project_combat(character,self.character_skill_pack(character)))

    def set_equipment(self, identifier, *, revision, inventory):
        require_revision(revision)
        character = self.get(identifier)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before editing equipment.')
        pack = self.character_equipment_pack(character)
        inventory = validate_inventory(inventory,pack)
        pins = {**character.get('additional_rule_packs',{}),pack['id']:pack['version']}
        return self.store.update(identifier,{'equipment':inventory,'additional_rule_packs':pins},revision)

    def purchase_equipment(self, identifier, *, revision, item_id, quantity=1, unit_cost=None):
        require_revision(revision)
        character = self.get(identifier)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before purchasing equipment.')
        pack = self.character_equipment_pack(character)
        inventory = purchase_inventory(character.get('equipment',{'credits':0,'items':[]}),
                                       pack,item_id,quantity,str(uuid4()),unit_cost=unit_cost)
        pins = {**character.get('additional_rule_packs',{}),pack['id']:pack['version']}
        return self.store.update(identifier,{'equipment':inventory,'additional_rule_packs':pins},revision)

    def split_equipment(self, identifier, *, revision, possession_id):
        require_revision(revision)
        character = self.get(identifier)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before splitting a possession.')
        pack = self.character_equipment_pack(character)
        inventory = split_inventory(character.get('equipment', {'credits': 0, 'items': []}),
                                    pack, possession_id, str(uuid4()))
        return self.store.update(identifier, {'equipment': inventory}, revision)

    def reload_weapon(self, identifier, *, revision, weapon_possession_id, clip_possession_id):
        require_revision(revision)
        character = self.get(identifier)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before reloading.')
        pack = self.character_equipment_pack(character)
        inventory = reload_inventory(character.get('equipment', {'credits': 0, 'items': []}),
                                     pack, weapon_possession_id, clip_possession_id)
        return self.store.update(identifier, {'equipment': inventory}, revision)

    def character_education_pack(self, character):
        return self._character_heroes_pack(character, 'heroes-education')

    def character_power_budget_pack(self, character):
        pack = self._character_heroes_pack(character, 'heroes-mutant-power-budget')
        if character['character_class'] != pack['character_class']:
            raise ValueError('Power outcome budgets are available for Heroes Unlimited Mutants')
        return pack

    def power_budget_view(self, identifier):
        character = self.get(identifier)
        return project_budget(character.get('power_budget'), self.character_power_budget_pack(character))

    def character_hero_powers_pack(self, character):
        pack = self._character_heroes_pack(character, 'heroes-super-abilities')
        if character['character_class'] != pack['character_class']:
            raise ValueError('Reviewed super abilities are available for Heroes Unlimited Mutants')
        return pack

    def hero_powers_view(self, identifier):
        character = self.get(identifier)
        return project_powers(character, self.character_hero_powers_pack(character), self.character_power_budget_pack(character),self._hero_higher_pack(character))

    def select_hero_powers(self, identifier, *, revision, selections):
        require_revision(revision)
        character = self.get(identifier)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before selecting powers.')
        pack = self.character_hero_powers_pack(character)
        changes = select_powers(character, selections, pack, self.die)
        changes['additional_rule_packs'] = {**character.get('additional_rule_packs', {}), pack['id']:pack['version']}
        if character['level'] > 1:
            record = deepcopy(character['advancement'])
            record['power_hp_rolls'] = power_gains({**character, **changes},
                self._character_heroes_pack(character,'heroes-advancement'),self.die,record['power_hp_rolls'])
            changes['advancement'] = record
            if character.get('later_advancements'):
                events = deepcopy(character['later_advancements'])
                for event in events:
                    if event['level'] <= character['level']:
                        event['power_hp_rolls'] = power_gains({**character,**changes},
                            self._character_heroes_pack(character,'heroes-advancement'),self.die,event['power_hp_rolls'])
                changes['later_advancements'] = events
        export_bundle({**character, **changes},self.rule_archive.definitions())
        return self.store.update(identifier, changes, revision)

    def select_power_budget(self, identifier, *, revision, method, outcome_id=None):
        require_revision(revision)
        character = self.get(identifier)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before selecting a power outcome.')
        pack = self.character_power_budget_pack(character)
        selection = select_budget(pack, method, outcome_id, self.die)
        record = {'selection':selection, 'history':[*character.get('power_budget', {}).get('history', []), selection]}
        validate_budget(record, pack)
        pins = {**character.get('additional_rule_packs', {}), pack['id']:pack['version']}
        return self.store.update(identifier, {'power_budget':record, 'additional_rule_packs':pins}, revision)

    def education_view(self, identifier):
        character = self.get(identifier)
        return project_education(character.get('education'), self.character_education_pack(character))

    def select_education(self, identifier, *, revision, method, education_id=None):
        require_revision(revision)
        character = self.get(identifier)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before selecting education.')
        pack = self.character_education_pack(character)
        selection = education_selection(pack, method, education_id, self.die)
        history = [*character.get('education', {}).get('history', []), selection]
        record = {'selection':selection, 'history':history}
        validate_education(record, pack)
        pins = {**character.get('additional_rule_packs', {}), pack['id']:pack['version']}
        return self.store.update(identifier, {'education':record, 'additional_rule_packs':pins}, revision)

    def select_combat(self, identifier, *, revision, choices, learned_level=None):
        require_revision(revision)
        character = self.get(identifier)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before selecting combat training.')
        if learned_level is not None and (type(learned_level) is not int or not 1 <= learned_level <= character['level']):
            raise ValueError('Choose a learned level no later than the current level')
        pack = self.character_skill_pack(character)
        choices = validate_combat_choices(choices, pack)
        changes = self._learning_changes(character, {'combat_choices': choices}, pack)
        if character['level'] > 1 and learned_level is not None:
            keys = [learning_key('hand', choices['hand_to_hand'])]
            keys.extend(learning_key('weapon', identifier) for family in ('ancient','modern') for identifier in choices[family])
            for key in keys:
                if key not in character.get('learning_levels', {}):
                    changes['learning_levels'][key] = learned_level
        return self.store.update(identifier, changes, revision)

    def _character_heroes_pack(self, character, identifier):
        if character['game'] != 'heroes-unlimited':
            raise ValueError('Education and scholastic programs are available for Heroes Unlimited characters')
        version = character.get('additional_rule_packs', {}).get(identifier)
        return (self.rule_archive.resolve(identifier, version) if version is not None
                else self.rule_archive.active(identifier))

    def hero_program_view(self, identifier):
        character = self.get(identifier)
        return {**self._project_hero_programs(character),
                'pinned':'heroes-program-skills' in character.get('additional_rule_packs', {})}

    def _project_hero_programs(self, character):
        pack = self._character_heroes_pack(character, 'heroes-program-skills')
        education = self.character_education_pack(character)
        power_pack = self.character_hero_powers_pack(character)
        powers = project_powers(character,power_pack,self.character_power_budget_pack(character),self._hero_higher_pack(character))
        physical = project_hero_physical(character, pack, education,power_view=powers)
        if character['level'] > 1:
            for row in physical['selected']:
                row['guidance'] = [note.replace('Heroes advancement remains unfinished; later training bonuses and maneuvers are not yet active.',
                    'Reviewed training bonuses through learned level 2 apply in combat; later training bonuses and maneuvers remain unfinished.') for note in row.get('guidance',[])]
                row['guidance'] = [note.replace('Later bonuses and maneuvers await Heroes advancement; current characters support level 1 only.',
                    'Reviewed training bonuses through learned level 2 apply in combat; later bonuses and maneuvers remain unfinished.') for note in row['guidance']]
        progression = self._character_heroes_pack(character,'heroes-advancement')
        higher = self._hero_higher_pack(character)
        if higher:
            for row in physical['selected']:
                if row['id'] in higher['training_progression']:
                    row['guidance'] = [note.replace('Reviewed training bonuses through learned level 2 apply in combat; later training bonuses and maneuvers remain unfinished.',
                        'Reviewed numeric training bonuses through learned level 15 apply in combat; earned conditional maneuvers appear as guidance, while later attack choices remain unfinished.').replace(
                        'Reviewed training bonuses through learned level 2 apply in combat; later bonuses and maneuvers remain unfinished.',
                        'Reviewed numeric training bonuses through learned level 15 apply in combat; earned conditional maneuvers appear as guidance, while later attack choices remain unfinished.') for note in row['guidance']]
        programs = project_programs(character, pack, education, power_pack)
        if higher:
            extra = sum(amount for level,amount in higher['secondary_awards'].items() if int(level)<=character['level'])
            programs['secondary']['allowance'] += extra
            programs['secondary']['remaining'] += extra
            programs['warnings'] = [note for note in programs['warnings'] if not note.startswith('Secondary selections exceed the education allowance')]
            if programs['secondary']['remaining'] < 0:
                programs['warnings'].append(f"Secondary selections exceed the education and progression allowance by {-programs['secondary']['remaining']}. Choices retained.")
            programs['secondary']['guidance'].append(higher['guidance'])
        if character['level'] > 1:
            programs['guidance'] = [note.replace('and advancement remain unfinished.', 'and later advancement remain unfinished.') for note in programs['guidance']]
        return {**programs,
                'physical':physical, 'combat':project_hero_combat(character,pack,physical,progression=progression,higher=higher,moves=self._hero_moves_pack(character,available=True)),
                'advancement':project_hero_advancement(character,progression,self._hero_higher_pack(character,available=True))}

    def select_hero_programs(self, identifier, *, revision, selections, learned_level=None):
        require_revision(revision)
        character = self.get(identifier)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before selecting programs.')
        pack = self._character_heroes_pack(character, 'heroes-program-skills')
        selections = validate_program_selections(selections, pack)
        if 'education' not in character:
            raise ValueError('Choose education before saving scholastic programs')
        pins = {**character.get('additional_rule_packs', {}), pack['id']:pack['version']}
        changes = {'hero_program_selections':selections, 'additional_rule_packs':pins}
        changes.update(preserve_training_choice(character,pack,self.character_education_pack(character)))
        changes.update(acquire_hero_physical({**character, **changes}, pack,
                                           self.character_education_pack(character), self.die))
        changes = self._hero_learning_changes(character,changes,learned_level=learned_level)
        export_bundle({**character, **changes},self.rule_archive.definitions())
        return self.store.update(identifier, changes, revision)

    def character_skill_pack(self, character):
        if character['game'] != 'rifts':
            raise ValueError('Heroes Unlimited education and skill rules remain unfinished')
        return class_rules(self.rule_archive.resolve('rifts-domestic-skills', character['additional_rule_packs']['rifts-domestic-skills']), character)

    def select_hero_secondary(self, identifier, *, revision, selections, learned_level=None):
        require_revision(revision)
        character = self.get(identifier)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before selecting Secondary skills.')
        pack = self._character_heroes_pack(character,'heroes-program-skills')
        selections = validate_secondary_selections(selections,pack)
        if 'education' not in character:
            raise ValueError('Choose education before saving Secondary skills')
        pins = {**character.get('additional_rule_packs',{}),pack['id']:pack['version']}
        changes = {'hero_secondary_selections':selections,'additional_rule_packs':pins}
        changes.update(preserve_training_choice(character,pack,self.character_education_pack(character)))
        changes.update(acquire_hero_physical({**character, **changes}, pack,
                                           self.character_education_pack(character), self.die))
        changes = self._hero_learning_changes(character,changes,learned_level=learned_level)
        export_bundle({**character, **changes},self.rule_archive.definitions())
        return self.store.update(identifier,changes,revision)

    def select_hero_training(self, identifier, *, revision, training_id):
        require_revision(revision)
        character = self.get(identifier)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before selecting combat training.')
        pack = self._character_heroes_pack(character,'heroes-program-skills')
        if 'training_skill_ids' not in pack.get('combat', {}):
            raise ValueError('Review a rule update before choosing an active training profile')
        physical = project_hero_physical(character,pack,self.character_education_pack(character))
        available = {row['id'] for row in physical['training_choices']}
        if training_id is not None and (not isinstance(training_id,str) or training_id not in available):
            raise ValueError('Choose an acquired and currently selected training style')
        return self.store.update(identifier,{'hero_combat_training':training_id},revision)

    def _hero_moves_pack(self, character, *, available=False):
        version = character.get('additional_rule_packs',{}).get('heroes-combat-moves')
        if version is not None:return self.rule_archive.resolve('heroes-combat-moves',version)
        if available and 'heroes-combat-moves' in self.rule_archive.active_versions():return self.rule_archive.active('heroes-combat-moves')
        return None

    def select_hero_kicks(self, identifier, *, revision, training_id, selections):
        require_revision(revision)
        character = self.get(identifier)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before selecting kicks.')
        pack = self._hero_moves_pack(character) or self.rule_archive.active('heroes-combat-moves')
        if character['game'] != 'heroes-unlimited' or not isinstance(training_id,str) or training_id not in pack['styles'] or training_id not in character.get('physical_acquisitions',{}):
            raise ValueError('Choose a retained Heroes training acquisition')
        selections = validate_kick_selections(selections,pack)
        records = deepcopy(character.get('hero_kick_choices',{}))
        records[training_id] = {'selections':selections,'source':deepcopy(pack['source'])}
        changes = {'hero_kick_choices':records,'additional_rule_packs':{**character.get('additional_rule_packs',{}),pack['id']:pack['version']}}
        export_bundle({**character,**changes},self.rule_archive.definitions())
        return self.store.update(identifier,changes,revision)

    def export_character(self, identifier):
        return export_bundle(self.get(identifier), self.rule_archive.definitions())

    def export_pdf(self, identifier):
        from .pdf_export import export_rifts_sheet

        character = self.get(identifier)
        if character['game'] != 'rifts':
            from .heroes_pdf import export_heroes_sheet
            core = self.rule_archive.resolve(character['rules']['id'], character['rules']['version'])
            return export_heroes_sheet(character, core,
                project_education(character.get('education'), self.character_education_pack(character)),
                self._project_hero_programs(character),
                project_budget(character.get('power_budget'), self.character_power_budget_pack(character)),
                project_powers(character, self.character_hero_powers_pack(character), self.character_power_budget_pack(character),self._hero_higher_pack(character)),
                self._project_character_resources(character))
        core = self.rule_archive.resolve(character['rules']['id'], character['rules']['version'])
        pack = self.character_skill_pack(character)
        combat = project_combat(character,pack)
        return export_rifts_sheet(character, core, {**project_skills(character, pack),
            'resources':project_resources(character,pack),
            'equipment':project_equipment(character,self.character_equipment_pack(character),combat)
                        if 'equipment' in character else None}, combat)

    def import_character(self, bundle):
        character = import_bundle(bundle, self.rule_archive.definitions())
        if 'skill_selections' in character:
            character['skill_selections'] = validate_selections(character['skill_selections'], self.character_skill_pack(character))
        if 'required_skill_choices' in character:
            character['required_skill_choices'] = validate_required_choices(character['required_skill_choices'], self.character_skill_pack(character))
        if 'combat_choices' in character:
            character['combat_choices'] = validate_combat_choices(character['combat_choices'], self.character_skill_pack(character))
        self.store.put(character)
        return character

    def duplicate(self, identifier):
        character = fresh_copy(self.get(identifier))
        character['name'] = (character['name'] or 'Unnamed adventurer') + ' (copy)'
        self.store.put(character)
        return character

    def backup(self):
        path = self.store.backup()
        return {'path': str(path.resolve()), 'filename': path.name}

    def preview_rule_upgrade(self, identifier):
        character = self.get(identifier)
        if character['game'] == 'heroes-unlimited':
            previous = self._character_heroes_pack(character, 'heroes-program-skills')
            target = self.rule_archive.active('heroes-program-skills')
            validate_physical_upgrade(character, previous, target, entire_definition=True)
            education = self.character_education_pack(character)
            powers = self.character_hero_powers_pack(character)
            before = project_programs(character, previous, education, powers)
            after = project_programs(character, target, education, powers)
            preview = {'skills':compare_skill_views({'grants':before['skills'], 'selected':[]},
                                                  {'grants':after['skills'], 'selected':[]}),
                       'combat':[], 'before_remaining':{}, 'after_remaining':{},
                       'before_required_remaining':{}, 'after_required_remaining':{},
                       'gaps':[*after['warnings'], *after['guidance']],
                       'sources':[f"{target['source']['book']}, printed pp. "
                                  + ', '.join(map(str, target['source']['pages']))
                                  + ' / PDF pp. ' + ', '.join(map(str, target['source']['pdf_pages']))],
                       'scope':'Heroes scholastic program skills. Education and attributes keep their saved rules.'}
            before_combat = project_hero_combat(character,previous,project_hero_physical(character,previous,education),progression=self._character_heroes_pack(character,'heroes-advancement'),higher=self._hero_higher_pack(character))
            after_combat = project_hero_combat(character,target,project_hero_physical(character,target,education),progression=self._character_heroes_pack(character,'heroes-advancement'),higher=self._hero_higher_pack(character))
            for name,result in after_combat['totals'].items():
                old_value = before_combat['totals'].get(name,{}).get('value')
                if old_value != result['value']:
                    preview['combat'].append({'name':'Heroes '+name.replace('_',' '),'before':old_value,'after':result['value']})
            for key,label in (('training','Heroes training'),('parry_actions','Heroes parry actions')):
                if before_combat.get(key) != after_combat.get(key):
                    preview['combat'].append({'name':label,'before':before_combat.get(key),'after':after_combat.get(key)})
            if after_combat['supported']:
                preview['scope'] += f" Reviewed Heroes ordinary combat through level {character['level']} is included; later advancement remains pending."
        else:
            previous = self.character_skill_pack(character)
            target = class_rules(self.rule_archive.active('rifts-domestic-skills'), character)
            if 'advancement' in character and canonical(previous.get('advancement')) != canonical(target.get('advancement')):
                raise ValueError('This update changes recorded advancement rules. History migration is not yet supported; current rules remain intact.')
            if character.get('later_advancements') and canonical(previous.get('higher_advancement')) != canonical(target.get('higher_advancement')):
                raise ValueError('This update changes recorded later advancement rules. History migration is not yet supported; current rules remain intact.')
            if 'resources' in character and canonical(previous.get('resources',{}).get('definitions')) != canonical(target.get('resources',{}).get('definitions')):
                raise ValueError('This update changes recorded resource rules. Resource migration is not yet supported; current rules remain intact.')
            validate_physical_upgrade(character, previous, target)
            validate_selections(character.get('skill_selections', []), target)
            before = project_skills(character, previous)
            after = project_skills(character, target)
            combat_after = project_combat(character, target)
            preview = {'skills': compare_skill_views(before, after),
                       'combat': compare_combat_views(project_combat(character, previous), combat_after),
                       'before_remaining': before['remaining'], 'after_remaining': after['remaining'],
                       'before_required_remaining': before['required_remaining'], 'after_required_remaining': after['required_remaining'],
                       'gaps': [*after['gaps'], *combat_after['gaps']], 'sources': after['sources'],
                       'scope': 'Selected class skills, reviewed Physical effects, class bonuses, combat training and starting-resource definitions. Resource dice are generated separately; recorded attribute/acquisition dice stay unchanged. Changes to acquired Physical or resource definitions require a separate migration.'}
        changes = [] if previous['version'] == target['version'] else [
            {'pack_id': target['id'], 'from': previous['version'], 'to': target['version']}]
        targets = [target]
        preview['equipment'] = []
        if character['game']=='heroes-unlimited' and self._hero_moves_pack(character):
            previous_moves = self._hero_moves_pack(character)
            target_moves = self.rule_archive.active('heroes-combat-moves')
            if character.get('hero_kick_choices') and canonical({k:v for k,v in previous_moves.items() if k!='version'}) != canonical({k:v for k,v in target_moves.items() if k!='version'}):
                raise ValueError('This update changes recorded Heroes kick rules. Choice/history migration is not yet supported; current rules remain intact.')
            targets.append(target_moves)
            if previous_moves['version'] != target_moves['version']:
                changes.append({'pack_id':target_moves['id'],'from':previous_moves['version'],'to':target_moves['version']})
        if character['game'] == 'heroes-unlimited' and 'heroes-super-abilities' in character.get('additional_rule_packs',{}):
            previous_powers = self.character_hero_powers_pack(character)
            target_powers = self.rule_archive.active('heroes-super-abilities')
            old_definitions = {row['id']:row for row in previous_powers['powers']}
            new_definitions = {row['id']:row for row in target_powers['powers']}
            for acquisition in character.get('hero_powers',{}).get('acquisitions',[]):
                identifier = acquisition['power']
                if canonical(old_definitions[identifier]) != canonical(new_definitions.get(identifier)):
                    raise ValueError('This update changes an acquired power definition. Acquisition/history migration is not yet supported; current rules remain intact.')
            budget = self.character_power_budget_pack(character)
            before_powers = project_powers(character,previous_powers,budget,self._hero_higher_pack(character))
            after_powers = project_powers(character,target_powers,budget,self._hero_higher_pack(character))
            for identifier,row in after_powers.get('saving_bonuses',{}).items():
                before_value = before_powers.get('saving_bonuses',{}).get(identifier,{}).get('value')
                if before_value != row['value']:
                    preview['combat'].append({'name':row['name']+' save bonus','before':before_value,'after':row['value']})
            for field,name in (('trust_intimidate','Trust/intimidate (%)'),('charm_impress','Charm/impress (%)')):
                if before_powers.get(field) != after_powers.get(field):
                    preview['combat'].append({'name':name,'before':before_powers.get(field),'after':after_powers.get(field)})
            preview['scope'] += ' Compatible power catalog additions are included; recorded acquisitions and dice remain unchanged.'
            preview['gaps'].extend(after_powers['warnings'])
            preview['sources'].extend(f"{row['source']['book']}, {row['name']}, printed p.{row['source']['printed_page']} / PDF p.{row['source']['pdf_page']}" for row in target_powers['powers'])
            targets.append(target_powers)
            if previous_powers['version'] != target_powers['version']:
                changes.append({'pack_id':target_powers['id'],'from':previous_powers['version'],'to':target_powers['version']})
        if character['game'] == 'rifts' and 'rifts-equipment' in character.get('additional_rule_packs', {}):
            previous_equipment = self.character_equipment_pack(character)
            target_equipment = equipment_class_rules(self.rule_archive.active('rifts-equipment'), character)
            validate_starting_group_upgrade(character, previous_equipment, target_equipment)
            if 'starting_funds' in character and canonical(previous_equipment.get('starting_funds')) != canonical(target_equipment.get('starting_funds')):
                raise ValueError('This update changes recorded starting funds rules. History migration is not yet supported; current rules remain intact.')
            if 'starting_gear' in character and canonical(previous_equipment.get('starting_gear')) != canonical(target_equipment.get('starting_gear')):
                raise ValueError('This update changes recorded starting gear rules. Receipt migration is not yet supported; current rules remain intact.')
            if 'starting_choices' in character and canonical(previous_equipment.get('starting_choices')) != canonical(target_equipment.get('starting_choices')):
                raise ValueError('This update changes recorded starting equipment choice rules. Receipt migration is not yet supported; current rules remain intact.')
            try:
                validate_inventory(character.get('equipment', {'credits': 0, 'items': []}), target_equipment)
            except ValueError as error:
                raise ValueError('This equipment update is incompatible with saved possessions. '
                                 'Current rules remain intact; inventory migration is not yet supported.') from error
            equipment_before = project_equipment(character, previous_equipment, project_combat(character, previous))
            equipment_after = project_equipment(character, target_equipment, project_combat(character, target))
            preview['equipment'] = compare_equipment_views(equipment_before, equipment_after)
            preview['scope'] += ' Equipment catalog corrections are included. Credits, quantities, locations and shots stay recorded.'
            preview['gaps'].extend(equipment_after['warnings'])
            source = target_equipment['source']
            preview['sources'].append(f"{source['book']}, equipment printed pp. "
                                     + ', '.join(map(str, source['pages']))
                                     + ' / PDF pp. ' + ', '.join(map(str, source['pdf_pages'])))
            if canonical(previous_equipment.get('starting_funds')) != canonical(target_equipment.get('starting_funds')):
                funds_rules = target_equipment.get('starting_funds', {})
                for definition in funds_rules.get('definitions', []):
                    funds_source = definition['source']
                    citation = (f"{funds_source['book']}, starting funds printed pp. "
                                + ', '.join(map(str, funds_source['pages']))
                                + ' / PDF pp. ' + ', '.join(map(str, funds_source['pdf_pages'])))
                    if citation not in preview['sources']:
                        preview['sources'].append(citation)
            if canonical(previous_equipment.get('starting_gear')) != canonical(target_equipment.get('starting_gear')):
                gear_source = target_equipment.get('starting_gear', {}).get('source')
                if gear_source:
                    preview['sources'].append(f"{gear_source['book']}, starting personal gear printed pp. "
                                              + ', '.join(map(str, gear_source['pages']))
                                              + ' / PDF pp. ' + ', '.join(map(str, gear_source['pdf_pages'])))
            old_items = {item['id']: item for item in previous_equipment['items']}
            for item in target_equipment['items']:
                if item != old_items.get(item['id']) and item.get('price_source'):
                    price_source = item['price_source']
                    citation = (f"{price_source['book']}, equipment prices printed pp. "
                                + ', '.join(map(str, price_source['pages']))
                                + ' / PDF pp. ' + ', '.join(map(str, price_source['pdf_pages'])))
                    if citation not in preview['sources']:
                        preview['sources'].append(citation)
            previous_groups = previous_equipment.get('starting_groups', {}).get('groups', {})
            for group_id, group in target_equipment.get('starting_groups', {}).get('groups', {}).items():
                if canonical(group) != canonical(previous_groups.get(group_id)):
                    group_source = group['source']
                    citation = (f"{group_source['book']}, starting equipment group printed pp. "
                                + ', '.join(map(str, group_source['pages']))
                                + ' / PDF pp. ' + ', '.join(map(str, group_source['pdf_pages'])))
                    if citation not in preview['sources']:
                        preview['sources'].append(citation)
            targets.append(target_equipment)
            if previous_equipment['version'] != target_equipment['version']:
                changes.append({'pack_id': target_equipment['id'], 'from': previous_equipment['version'],
                                'to': target_equipment['version']})
        if character['game'] == 'heroes-unlimited' and 'heroes-advancement' in character.get('additional_rule_packs',{}):
            previous_progression = self._character_heroes_pack(character,'heroes-advancement')
            target_progression = self.rule_archive.active('heroes-advancement')
            if 'advancement' in character and canonical(previous_progression) != canonical(target_progression):
                raise ValueError('This update changes recorded Heroes advancement rules. History migration remains pending; current rules stay intact.')
            targets.append(target_progression)
            if previous_progression['version'] != target_progression['version']:
                changes.append({'pack_id':target_progression['id'],'from':previous_progression['version'],'to':target_progression['version']})
        preview.update(revision=character['revision'], changes=changes)
        if character['game']=='heroes-unlimited' and 'heroes-higher-advancement' in character.get('additional_rule_packs',{}):
            previous_higher = self._hero_higher_pack(character)
            target_higher = self.rule_archive.active('heroes-higher-advancement')
            if character.get('later_advancements') and canonical(previous_higher)!=canonical(target_higher):
                raise ValueError('This update changes recorded Heroes later advancement rules. History migration remains pending; current rules stay intact.')
            targets.append(target_higher)
            if previous_higher['version']!=target_higher['version']:
                changes.append({'pack_id':target_higher['id'],'from':previous_higher['version'],'to':target_higher['version']})
        preview['token'] = hashlib.sha256(canonical({'character_id': identifier, 'preview': preview, 'targets': targets})).hexdigest()
        return preview

    def apply_rule_upgrade(self, identifier, *, revision, token):
        require_revision(revision)
        character = self.get(identifier)
        if revision != character['revision']:
            raise SaveConflict('This character changed after the preview. Reopen it and preview the update again.')
        preview = self.preview_rule_upgrade(identifier)
        if not preview['changes'] or not isinstance(token, str) or not secrets.compare_digest(token, preview['token']):
            raise ValueError('The rule update preview is unavailable or changed. Preview it again before applying.')
        backup = self.backup()
        pins = dict(character['additional_rule_packs'])
        for change in preview['changes']:
            pins[change['pack_id']] = change['to']
        export_bundle({**character, 'additional_rule_packs': pins}, self.rule_archive.definitions())
        updated = self.store.update(identifier, {'additional_rule_packs': pins}, revision)
        return {'character': updated, 'backup': backup}

    def select_skills(self, identifier, *, revision, selections, learned_level=None):
        require_revision(revision)
        character = self.get(identifier)
        pack = self.character_skill_pack(character)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before selecting skills.')
        if learned_level is not None and (type(learned_level) is not int or not 1 <= learned_level <= character['level']):
            raise ValueError('Choose a learned level no later than the current level')
        packs = character.get('additional_rule_packs', {})
        selections = validate_selections(selections,pack)
        changes = acquire_physical(character,selections,pack,self.die)
        changes = self._learning_changes(character, {'skill_selections': selections, 'additional_rule_packs': packs, **changes}, pack)
        if character['level'] > 1 and learned_level is not None:
            for item in selections:
                key = learning_key('skill', item['skill_id'], item['specialty'])
                if key not in character.get('learning_levels', {}):
                    changes['learning_levels'][key] = learned_level
        return self.store.update(identifier, changes, revision)

    def resource_view(self, identifier):
        character = self.get(identifier)
        return self._project_character_resources(character)

    def _project_character_resources(self, character):
        physical = None
        physical_supported = False
        power_supported = False
        if character['game'] == 'heroes-unlimited':
            pack = self._character_heroes_pack(character, 'heroes-program-skills')
            physical_supported = any(row.get('kind') == 'physical' for row in pack['skills'])
            physical = project_hero_physical(character,
                pack,
                self.character_education_pack(character))['resources']
            power_supported = 'physical_endurance_charts' in self.character_hero_powers_pack(character)
        power_resources = (power_resource_contributions(character,self.character_hero_powers_pack(character))
                           if character['game'] == 'heroes-unlimited' else None)
        if character['game'] == 'heroes-unlimited':
            power_resources = [*(power_resources or []), *advancement_power_resources(character,
                self._character_heroes_pack(character,'heroes-advancement'))]
        view = project_resources(character, self.character_resource_pack(character), physical_resources=physical,
                                 power_resources=power_resources)
        if physical_supported:
            view['guidance'] = [note.replace(
                'Additional Physical skill, unusual characteristic and power S.D.C. contributions remain unfinished.',
                'Reviewed Body Building and Running contributions apply when selected. Other Physical skill, unusual characteristic and power contributions remain unfinished.')
                for note in view['guidance']]
        if character['game'] == 'heroes-unlimited':
            view['physical_supported'] = physical_supported
            view['power_supported'] = power_supported
            if power_supported:
                view['guidance'] = [note.replace('Other Physical skill, unusual characteristic and power contributions remain unfinished.',
                    'Other Physical skill, unusual characteristic and other power contributions remain unfinished.') for note in view['guidance']]
                view['guidance'].append('Extraordinary Physical Endurance adds its recorded HP and S.D.C. dice while active, including one retained D4 for each attained level, starting at level 1. Its P.E. addition affects the starting HP snapshot only if active at initial generation. Later removal or acquisition never rewrites that snapshot. Other power resources and Heroes advancement remain unfinished.')
        if character['game'] == 'heroes-unlimited' and character.get('advancement'):
            view['guidance'] = [note.replace('Heroes advancement remain unfinished.', 'later Heroes advancement remain unfinished.').replace('Heroes advancement, other category resources,', 'Later Heroes advancement, other category resources,') for note in view['guidance']]
            view['guidance'].append((self._hero_higher_pack(character) or self._character_heroes_pack(character,'heroes-advancement'))['guidance'])
        return view

    def character_resource_pack(self, character):
        if character['game'] == 'rifts':
            return self.character_skill_pack(character)
        pack = self._character_heroes_pack(character, 'heroes-resources')
        if character['character_class'] != pack['character_class'] or character['race'] != pack['race']:
            raise ValueError('Starting resources require the reviewed Human Mutant path')
        return pack

    def generate_resources(self, identifier, *, revision):
        require_revision(revision)
        character = self.get(identifier)
        pack = self.character_resource_pack(character)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before generating starting resources.')
        changes = acquire_resources(character,pack,self.die)
        if character['game'] == 'heroes-unlimited':
            changes['additional_rule_packs'] = {**character.get('additional_rule_packs', {}), pack['id']:pack['version']}
        return self.store.update(identifier,changes,revision)

    def generate_starting_funds(self, identifier, *, revision):
        require_revision(revision)
        character = self.get(identifier)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before generating starting funds.')
        pack = self.character_equipment_pack(character)
        validate_inventory(character.get('equipment', {'credits': 0, 'items': []}), pack)
        changes = acquire_starting_funds(character, pack, self.die)
        validate_inventory(changes['equipment'], pack)
        pins = dict(character['additional_rule_packs'])
        pins[pack['id']] = pack['version']
        return self.store.update(identifier, {**changes, 'additional_rule_packs': pins}, revision)

    def grant_starting_choices(self, identifier, *, revision, choices):
        require_revision(revision)
        character = self.get(identifier)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before adding starting equipment choices.')
        pack = self.character_equipment_pack(character)
        validate_inventory(character.get('equipment', {'credits': 0, 'items': []}), pack)
        changes = acquire_starting_choices(character, pack, choices, lambda: str(uuid4()))
        validate_inventory(changes['equipment'], pack)
        pins = {**character['additional_rule_packs'], pack['id']: pack['version']}
        return self.store.update(identifier, {**changes, 'additional_rule_packs': pins}, revision)

    def grant_starting_group(self, identifier, *, revision, group_id, selection):
        require_revision(revision)
        character = self.get(identifier)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before adding a starting equipment group.')
        pack = self.character_equipment_pack(character)
        validate_inventory(character.get('equipment', {'credits': 0, 'items': []}), pack)
        changes = acquire_starting_group(character, pack, group_id, selection, lambda: str(uuid4()))
        validate_inventory(changes['equipment'], pack)
        pins = {**character['additional_rule_packs'], pack['id']: pack['version']}
        return self.store.update(identifier, {**changes, 'additional_rule_packs': pins}, revision)

    def grant_starting_gear(self, identifier, *, revision):
        require_revision(revision)
        character = self.get(identifier)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before adding starting gear.')
        pack = self.character_equipment_pack(character)
        validate_inventory(character.get('equipment', {'credits': 0, 'items': []}), pack)
        changes = acquire_starting_gear(character, pack, lambda: str(uuid4()))
        validate_inventory(changes['equipment'], pack)
        pins = dict(character['additional_rule_packs'])
        pins[pack['id']] = pack['version']
        return self.store.update(identifier, {**changes, 'additional_rule_packs': pins}, revision)

    def set_resource(self, identifier, *, revision, resource, mode, value=None):
        require_revision(revision)
        character = self.get(identifier)
        pack = self.character_resource_pack(character)
        changes = update_resource(character,pack,resource,mode,value)
        return self.store.update(identifier,changes,revision)

    def select_required_skills(self, identifier, *, revision, choices):
        character = self.get(identifier)
        pack = self.character_skill_pack(character)
        choices = validate_required_choices(choices, pack)
        return self.store.update(identifier, self._learning_changes(character, {'required_skill_choices': choices}, pack), require_revision(revision))

    def edit(self, identifier, *, name=None, notes=None, revision=None):
        changes = {}
        for key, value in (("name", name), ("notes", notes)):
            if value is not None:
                if not isinstance(value, str):
                    raise ValueError(f"{key} must be text")
                changes[key] = value
        return self.store.update(identifier, changes, require_revision(revision))

    def reroll(self, identifier, *, revision, attribute=None, generation=None):
        require_revision(revision)
        character = self.get(identifier)
        if attribute is not None and attribute not in ATTRIBUTES:
            raise ValueError("Select a known attribute")
        settings = generation_settings(generation if generation is not None else character.get("generation"))
        pack = self.rule_archive.resolve(character['rules']['id'], character['rules']['version'])
        racial_rules = next(item for item in pack["races"] if item["id"] == character["race"])
        formulas = racial_formulas(racial_rules, settings if attribute is None else None)
        sources = racial_sources(racial_rules, pack["source"])
        attributes = deepcopy(character["attributes"])
        results = {}
        for name in (ATTRIBUTES if attribute is None else (attribute,)):
            formula = formulas[name]
            result = roll_attribute(formula, settings, self.die, sources[name])
            previous = attributes[name]
            result["adjustment"] = previous.get("adjustment", 0)
            result["fixed"] = previous.get("fixed")
            if 'modifiers' in previous:
                result['modifiers'] = deepcopy(previous['modifiers'])
            result["value"] = attribute_value(result)
            attributes[name] = result
            results[name] = deepcopy(result)
        history = character.get("roll_history", [{"kind": "previous", "at": None, "attributes": deepcopy(character["attributes"])}])
        history.append({"kind": "reroll", "at": datetime.now(timezone.utc).isoformat(), "generation": settings, "attributes": results})
        return self.store.update(identifier, {"attributes": attributes, "generation": settings, "roll_history": history}, revision)

    def set_attribute(self, identifier, *, revision, attribute, mode, value=None):
        require_revision(revision)
        character = self.get(identifier)
        if attribute not in ATTRIBUTES:
            raise ValueError("Select a known attribute")
        if mode not in ("fixed", "adjustment", "calculated"):
            raise ValueError("Select fixed, adjustment, or calculated")
        if mode != "calculated" and type(value) is not int:
            raise ValueError("Attribute values must be whole numbers")
        attributes = deepcopy(character["attributes"])
        result = attributes[attribute]
        result["fixed"] = value if mode == "fixed" else None
        result["adjustment"] = value if mode == "adjustment" else 0
        result["value"] = attribute_value(result)
        return self.store.update(identifier, {"attributes": attributes}, revision)
