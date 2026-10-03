"""Player-facing character workflows; all derived results enter through this seam."""

import secrets
import hashlib
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .storage import CharacterStore, SaveConflict
from .coverage import SourceInventory
from .generation import generation_settings, roll_attribute
from .skills import validate_selections, project_skills, compare_skill_views
from .portability import export_bundle, import_bundle, fresh_copy, pinned_packs, canonical
from .rules import RuleArchive
from .required_skills import validate_required_choices

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
        self.skill_pack = self.rule_archive.active('rifts-domestic-skills')
        self.store = CharacterStore(directory)

    def catalog(self):
        return {"games": [{"id": "rifts", "name": "Rifts Ultimate Edition"}], "packs": [deepcopy(self.pack)]}

    def coverage(self):
        return SourceInventory.load()

    def create(self, name="", race="human", character_class="vagabond", notes="", generation=None):
        racial_rules = next((item for item in self.pack["races"] if item["id"] == race), None)
        selected_class = next((item for item in self.pack["classes"] if item["id"] == character_class), None)
        if racial_rules is None or selected_class is None:
            raise ValueError("Select an available race and class")
        if not isinstance(name, str) or not isinstance(notes, str):
            raise ValueError("Name and notes must be text")
        settings = generation_settings(generation)
        character = {
            "id": str(uuid4()), "format_version": 1, "game": "rifts",
            "name": name, "notes": notes, "race": race, "character_class": character_class,
            "rules": {"id": self.pack["id"], "version": self.pack["version"]},
            "additional_rule_packs": {self.skill_pack['id']: self.skill_pack['version']},
            "level": 1, "revision": 0, "attributes": {}, "generation": settings,
            "completion": ["Skills are not yet complete", "Equipment and resources are not yet complete"],
            "automation_gaps": selected_class["automation_gaps"],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        for attribute in ATTRIBUTES:
            formula = racial_rules["attributes"]
            character["attributes"][attribute] = roll_attribute(formula, settings, self.die, self.pack["source"])
        character["roll_history"] = [{"kind": "initial", "at": character["updated_at"], "generation": settings, "attributes": deepcopy(character["attributes"])}]
        self.store.put(character)
        return character

    def get(self, identifier):
        character = self.store.get(identifier)
        # Earlier builds already projected this exact domestic pack without a pin.
        character.setdefault('additional_rule_packs', {}).setdefault('rifts-domestic-skills', '1.0.0')
        pinned_packs(character, self.rule_archive.definitions())
        return character

    def list(self):
        return self.store.list()

    def skill_view(self, identifier):
        character = self.get(identifier)
        return project_skills(character, self.character_skill_pack(character))

    def character_skill_pack(self, character):
        return self.rule_archive.resolve('rifts-domestic-skills', character['additional_rule_packs']['rifts-domestic-skills'])

    def export_character(self, identifier):
        return export_bundle(self.get(identifier), self.rule_archive.definitions())

    def import_character(self, bundle):
        character = import_bundle(bundle, self.rule_archive.definitions())
        if 'skill_selections' in character:
            character['skill_selections'] = validate_selections(character['skill_selections'], self.character_skill_pack(character))
        if 'required_skill_choices' in character:
            character['required_skill_choices'] = validate_required_choices(character['required_skill_choices'], self.character_skill_pack(character))
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
        previous = self.character_skill_pack(character)
        target = self.rule_archive.active('rifts-domestic-skills')
        changes = [] if previous['version'] == target['version'] else [
            {'pack_id': target['id'], 'from': previous['version'], 'to': target['version']}]
        # This explicit upgrade handler changes domestic definitions only.
        validate_selections(character.get('skill_selections', []), target)
        before = project_skills(character, previous)
        after = project_skills(character, target)
        preview = {'revision': character['revision'], 'changes': changes,
                   'skills': compare_skill_views(before, after),
                   'before_remaining': before['remaining'], 'after_remaining': after['remaining'],
                   'before_required_remaining': before['required_remaining'], 'after_required_remaining': after['required_remaining'],
                   'gaps': after['gaps'], 'sources': after['sources'],
                   'scope': 'Vagabond skill definitions. Attributes and their recorded dice stay unchanged.'}
        preview['token'] = hashlib.sha256(canonical({'character_id': identifier, 'preview': preview, 'target': target})).hexdigest()
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
        pins['rifts-domestic-skills'] = preview['changes'][0]['to']
        updated = self.store.update(identifier, {'additional_rule_packs': pins}, revision)
        return {'character': updated, 'backup': backup}

    def select_skills(self, identifier, *, revision, selections):
        character = self.get(identifier)
        packs = character.get('additional_rule_packs', {})
        return self.store.update(identifier, {'skill_selections': validate_selections(selections, self.character_skill_pack(character)), 'additional_rule_packs': packs}, require_revision(revision))

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
            formula = racial_rules["attributes"]
            result = roll_attribute(formula, settings, self.die, pack["source"])
            previous = attributes[name]
            result["adjustment"] = previous.get("adjustment", 0)
            result["fixed"] = previous.get("fixed")
            result["value"] = result["fixed"] if result["fixed"] is not None else result["base"] + result["adjustment"]
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
        result["value"] = result["fixed"] if result["fixed"] is not None else result["base"] + result["adjustment"]
        return self.store.update(identifier, {"attributes": attributes}, revision)
