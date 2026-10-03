"""Player-facing character workflows; all derived results enter through this seam."""

import json
import secrets
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .storage import CharacterStore, SaveConflict
from .coverage import SourceInventory
from .generation import generation_settings, roll_attribute
from .skills import validate_selections, project_skills, PACK as SKILL_PACK
from .portability import export_bundle, import_bundle, fresh_copy, pinned_packs

ATTRIBUTES = ("IQ", "ME", "MA", "PS", "PP", "PE", "PB", "SPD")


def require_revision(revision):
    if type(revision) is not int or revision < 0:
        raise ValueError("A nonnegative saved revision is required")
    return revision


class CharacterApplication:
    def __init__(self, directory: str | Path, die=None):
        self.store = CharacterStore(directory)
        self.die = die or (lambda sides: secrets.randbelow(sides) + 1)
        self.pack = json.loads(
            (Path(__file__).parent / "packs" / "rifts-core.json").read_text(encoding="utf-8")
        )

    def catalog(self):
        return {"games": [{"id": "rifts", "name": "Rifts Ultimate Edition"}], "packs": [self.pack]}

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
            "additional_rule_packs": {SKILL_PACK['id']: SKILL_PACK['version']},
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
        pinned_packs(character, [self.pack, SKILL_PACK])
        return character

    def list(self):
        return self.store.list()

    def skill_view(self, identifier):
        return project_skills(self.get(identifier))

    def export_character(self, identifier):
        return export_bundle(self.get(identifier), [self.pack, SKILL_PACK])

    def import_character(self, bundle):
        character = import_bundle(bundle, [self.pack, SKILL_PACK])
        if 'skill_selections' in character:
            character['skill_selections'] = validate_selections(character['skill_selections'])
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

    def select_skills(self, identifier, *, revision, selections):
        character = self.get(identifier)
        packs = character.get('additional_rule_packs', {})
        packs[SKILL_PACK['id']] = SKILL_PACK['version']
        return self.store.update(identifier, {'skill_selections': validate_selections(selections), 'additional_rule_packs': packs}, require_revision(revision))

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
        racial_rules = next(item for item in self.pack["races"] if item["id"] == character["race"])
        attributes = deepcopy(character["attributes"])
        results = {}
        for name in (ATTRIBUTES if attribute is None else (attribute,)):
            formula = racial_rules["attributes"]
            result = roll_attribute(formula, settings, self.die, self.pack["source"])
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
