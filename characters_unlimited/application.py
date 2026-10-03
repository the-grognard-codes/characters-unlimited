"""Player-facing character workflows; all derived results enter through this seam."""

import secrets
import hashlib
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .storage import CharacterStore, SaveConflict
from .coverage import SourceInventory
from .generation import generation_settings, roll_attribute, racial_formula
from .skills import validate_selections, project_skills, compare_skill_views
from .portability import export_bundle, import_bundle, fresh_copy, pinned_packs, canonical
from .rules import RuleArchive
from .required_skills import validate_required_choices
from .combat import validate_combat_choices, project_combat, compare_combat_views
from .attribute_modifiers import attribute_value, roll_class_modifiers
from .education import education_selection, validate_education, project_education
from .heroes_programs import validate_program_selections, validate_secondary_selections, project_programs
from .physical import acquire_physical
from .resources import acquire_resources, project_resources, update_resource
from .equipment import validate_inventory, purchase_inventory, project_equipment, compare_equipment_views
from .starting_funds import acquire_starting_funds

ATTRIBUTES = ("IQ", "ME", "MA", "PS", "PP", "PE", "PB", "SPD")


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
        return {"games": [{"id": "rifts", "name": "Rifts Ultimate Edition"}, {"id": "heroes-unlimited", "name": self.heroes_pack["name"]}], "packs": [deepcopy(self.pack), deepcopy(self.heroes_pack)]}

    def coverage(self):
        return SourceInventory.load()

    def create(self, name="", race="human", character_class=None, notes="", generation=None, game="rifts"):
        pack = {"rifts": self.pack, "heroes-unlimited": self.heroes_pack}.get(game)
        if pack is None:
            raise ValueError("Select an available game")
        if character_class is None:
            character_class = pack["classes"][0]["id"]
        racial_rules = next((item for item in pack["races"] if item["id"] == race), None)
        selected_class = next((item for item in pack["classes"] if item["id"] == character_class), None)
        if racial_rules is None or selected_class is None:
            raise ValueError("Select an available race and class from the selected game")
        if not isinstance(name, str) or not isinstance(notes, str):
            raise ValueError("Name and notes must be text")
        settings = generation_settings(generation)
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
            formula = racial_formula(racial_rules, attribute)
            character["attributes"][attribute] = roll_attribute(formula, settings, self.die, pack["source"])
        roll_class_modifiers(character['attributes'], selected_class, self.die)
        character["roll_history"] = [{"kind": "initial", "at": character["updated_at"], "generation": settings, "attributes": deepcopy(character["attributes"])}]
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
                'resources':project_resources(character,pack)}

    def combat_view(self, identifier):
        character = self.get(identifier)
        return project_combat(character, self.character_skill_pack(character))

    def character_equipment_pack(self, character):
        if character['game'] != 'rifts':
            raise ValueError('Heroes Unlimited equipment remains unfinished')
        version = character.get('additional_rule_packs',{}).get('rifts-equipment')
        return (self.rule_archive.resolve('rifts-equipment',version) if version is not None
                else self.rule_archive.active('rifts-equipment'))

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

    def purchase_equipment(self, identifier, *, revision, item_id, quantity=1):
        require_revision(revision)
        character = self.get(identifier)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before purchasing equipment.')
        pack = self.character_equipment_pack(character)
        inventory = purchase_inventory(character.get('equipment',{'credits':0,'items':[]}),
                                       pack,item_id,quantity,str(uuid4()))
        pins = {**character.get('additional_rule_packs',{}),pack['id']:pack['version']}
        return self.store.update(identifier,{'equipment':inventory,'additional_rule_packs':pins},revision)

    def character_education_pack(self, character):
        return self._character_heroes_pack(character, 'heroes-education')

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

    def select_combat(self, identifier, *, revision, choices):
        character = self.get(identifier)
        choices = validate_combat_choices(choices, self.character_skill_pack(character))
        return self.store.update(identifier, {'combat_choices': choices}, require_revision(revision))

    def _character_heroes_pack(self, character, identifier):
        if character['game'] != 'heroes-unlimited':
            raise ValueError('Education and scholastic programs are available for Heroes Unlimited characters')
        version = character.get('additional_rule_packs', {}).get(identifier)
        return (self.rule_archive.resolve(identifier, version) if version is not None
                else self.rule_archive.active(identifier))

    def hero_program_view(self, identifier):
        character = self.get(identifier)
        return {**project_programs(character, self._character_heroes_pack(character, 'heroes-program-skills'), self.character_education_pack(character)),
                'pinned':'heroes-program-skills' in character.get('additional_rule_packs', {})}

    def select_hero_programs(self, identifier, *, revision, selections):
        require_revision(revision)
        character = self.get(identifier)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before selecting programs.')
        pack = self._character_heroes_pack(character, 'heroes-program-skills')
        selections = validate_program_selections(selections, pack)
        if 'education' not in character:
            raise ValueError('Choose education before saving scholastic programs')
        pins = {**character.get('additional_rule_packs', {}), pack['id']:pack['version']}
        return self.store.update(identifier, {'hero_program_selections':selections, 'additional_rule_packs':pins}, revision)

    def character_skill_pack(self, character):
        if character['game'] != 'rifts':
            raise ValueError('Heroes Unlimited education and skill rules remain unfinished')
        return self.rule_archive.resolve('rifts-domestic-skills', character['additional_rule_packs']['rifts-domestic-skills'])

    def select_hero_secondary(self, identifier, *, revision, selections):
        require_revision(revision)
        character = self.get(identifier)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before selecting Secondary skills.')
        pack = self._character_heroes_pack(character,'heroes-program-skills')
        selections = validate_secondary_selections(selections,pack)
        if 'education' not in character:
            raise ValueError('Choose education before saving Secondary skills')
        pins = {**character.get('additional_rule_packs',{}),pack['id']:pack['version']}
        return self.store.update(identifier,{'hero_secondary_selections':selections,'additional_rule_packs':pins},revision)

    def export_character(self, identifier):
        return export_bundle(self.get(identifier), self.rule_archive.definitions())

    def export_pdf(self, identifier):
        from .pdf_export import export_rifts_sheet

        character = self.get(identifier)
        if character['game'] != 'rifts':
            raise ValueError('Heroes Unlimited editable PDF remains unfinished')
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
            education = self.character_education_pack(character)
            before = project_programs(character, previous, education)
            after = project_programs(character, target, education)
            preview = {'skills':compare_skill_views({'grants':before['skills'], 'selected':[]},
                                                  {'grants':after['skills'], 'selected':[]}),
                       'combat':[], 'before_remaining':{}, 'after_remaining':{},
                       'before_required_remaining':{}, 'after_required_remaining':{},
                       'gaps':[*after['warnings'], *after['guidance']],
                       'sources':[f"{target['source']['book']}, printed pp. "
                                  + ', '.join(map(str, target['source']['pages']))
                                  + ' / PDF pp. ' + ', '.join(map(str, target['source']['pdf_pages']))],
                       'scope':'Heroes scholastic program skills. Education, attributes and other rules keep their saved versions.'}
        else:
            previous = self.character_skill_pack(character)
            target = self.rule_archive.active('rifts-domestic-skills')
            if 'resources' in character and canonical(previous.get('resources',{}).get('definitions')) != canonical(target.get('resources',{}).get('definitions')):
                raise ValueError('This update changes recorded resource rules. Resource migration is not yet supported; current rules remain intact.')
            for skill_id in character.get('physical_acquisitions',{}):
                before_definition = next(item for item in previous['skills'] if item['id']==skill_id)
                after_definition: dict = next((item for item in target['skills'] if item['id']==skill_id),{})
                fields = ('kind','attributes','resources','combat','source')
                if canonical({key:before_definition.get(key) for key in fields}) != canonical({key:after_definition.get(key) for key in fields}):
                    raise ValueError('This update changes recorded Physical bonus rules. Acquisition/history migration is not yet supported; current rules remain intact.')
            validate_selections(character.get('skill_selections', []), target)
            before = project_skills(character, previous)
            after = project_skills(character, target)
            combat_after = project_combat(character, target)
            preview = {'skills': compare_skill_views(before, after),
                       'combat': compare_combat_views(project_combat(character, previous), combat_after),
                       'before_remaining': before['remaining'], 'after_remaining': after['remaining'],
                       'before_required_remaining': before['required_remaining'], 'after_required_remaining': after['required_remaining'],
                       'gaps': [*after['gaps'], *combat_after['gaps']], 'sources': after['sources'],
                       'scope': 'Vagabond skills, reviewed Physical effects, class bonuses, combat training and starting-resource definitions. Resource dice are generated separately; recorded attribute/acquisition dice stay unchanged. Changes to acquired Physical or resource definitions require a separate migration.'}
        changes = [] if previous['version'] == target['version'] else [
            {'pack_id': target['id'], 'from': previous['version'], 'to': target['version']}]
        targets = [target]
        preview['equipment'] = []
        if character['game'] == 'rifts' and 'rifts-equipment' in character.get('additional_rule_packs', {}):
            previous_equipment = self.character_equipment_pack(character)
            target_equipment = self.rule_archive.active('rifts-equipment')
            if 'starting_funds' in character and canonical(previous_equipment.get('starting_funds')) != canonical(target_equipment.get('starting_funds')):
                raise ValueError('This update changes recorded starting funds rules. History migration is not yet supported; current rules remain intact.')
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
            targets.append(target_equipment)
            if previous_equipment['version'] != target_equipment['version']:
                changes.append({'pack_id': target_equipment['id'], 'from': previous_equipment['version'],
                                'to': target_equipment['version']})
        preview.update(revision=character['revision'], changes=changes)
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
        updated = self.store.update(identifier, {'additional_rule_packs': pins}, revision)
        return {'character': updated, 'backup': backup}

    def select_skills(self, identifier, *, revision, selections):
        require_revision(revision)
        character = self.get(identifier)
        pack = self.character_skill_pack(character)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before selecting skills.')
        packs = character.get('additional_rule_packs', {})
        selections = validate_selections(selections,pack)
        changes = acquire_physical(character,selections,pack,self.die)
        return self.store.update(identifier, {'skill_selections': selections, 'additional_rule_packs': packs, **changes}, revision)

    def resource_view(self, identifier):
        character = self.get(identifier)
        return project_resources(character,self.character_skill_pack(character))

    def generate_resources(self, identifier, *, revision):
        require_revision(revision)
        character = self.get(identifier)
        pack = self.character_skill_pack(character)
        if revision != character['revision']:
            raise SaveConflict('This character changed. Reopen it before generating starting resources.')
        changes = acquire_resources(character,pack,self.die)
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

    def set_resource(self, identifier, *, revision, resource, mode, value=None):
        require_revision(revision)
        character = self.get(identifier)
        pack = self.character_skill_pack(character)
        changes = update_resource(character,pack,resource,mode,value)
        return self.store.update(identifier,changes,revision)

    def select_required_skills(self, identifier, *, revision, choices):
        character = self.get(identifier)
        choices = validate_required_choices(choices, self.character_skill_pack(character))
        return self.store.update(identifier, {'required_skill_choices': choices}, require_revision(revision))

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
        attributes = deepcopy(character["attributes"])
        results = {}
        for name in (ATTRIBUTES if attribute is None else (attribute,)):
            formula = racial_formula(racial_rules, name)
            result = roll_attribute(formula, settings, self.die, pack["source"])
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
