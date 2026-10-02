"""Player-facing character workflows; all derived results enter through this seam."""

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .storage import CharacterStore, SaveConflict
from .coverage import SourceInventory

ATTRIBUTES = ("IQ", "ME", "MA", "PS", "PP", "PE", "PB", "SPD")


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

    def create(self, name="", race="human", character_class="vagabond", notes=""):
        racial_rules = next((item for item in self.pack["races"] if item["id"] == race), None)
        selected_class = next((item for item in self.pack["classes"] if item["id"] == character_class), None)
        if racial_rules is None or selected_class is None:
            raise ValueError("Select an available race and class")
        if not isinstance(name, str) or not isinstance(notes, str):
            raise ValueError("Name and notes must be text")
        character = {
            "id": str(uuid4()), "format_version": 1, "game": "rifts",
            "name": name, "notes": notes, "race": race, "character_class": character_class,
            "rules": {"id": self.pack["id"], "version": self.pack["version"]},
            "level": 1, "revision": 0, "attributes": {},
            "completion": ["Skills are not yet complete", "Equipment and resources are not yet complete"],
            "automation_gaps": selected_class["automation_gaps"],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        for attribute in ATTRIBUTES:
            formula = racial_rules["attributes"]
            rolls = [self.die(formula["sides"]) for _ in range(formula["count"])]
            total = sum(rolls) + formula["constant"]
            bonus_rolls = []
            exceptional = formula["exceptional"]
            if total in exceptional["thresholds"]:
                for _ in range(exceptional["max_bonus_dice"]):
                    bonus = self.die(formula["sides"])
                    bonus_rolls.append(bonus)
                    total += bonus
                    if bonus != formula["sides"]:
                        break
            character["attributes"][attribute] = {
                "base": total, "value": total, "rolls": rolls, "bonus_rolls": bonus_rolls,
                "explanation": {"formula": "3D6; eligible initial totals add exceptional dice", "source": self.pack["source"]},
            }
        self.store.put(character)
        return character

    def get(self, identifier):
        return self.store.get(identifier)

    def list(self):
        return self.store.list()

    def edit(self, identifier, *, name=None, notes=None, revision=None):
        changes = {}
        for key, value in (("name", name), ("notes", notes)):
            if value is not None:
                if not isinstance(value, str):
                    raise ValueError(f"{key} must be text")
                changes[key] = value
        if type(revision) is not int or revision < 0:
            raise ValueError("A nonnegative saved revision is required")
        return self.store.update(identifier, changes, revision)
