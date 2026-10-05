"""Restore category boundaries and column order checked in PU2 source pages."""
from repair_source_passages import ROOT, replace, replace_region, save_repairs


def main():
    name = "Heroes Unlimited - Powers Unlimited 2.md"
    replace_region(name, "The Empowered character is often", "## Step Three: Determining Impairment", """Weapons Training: This is a classic type of super-hero that has trained with one class of ancient weapons (missile or melee) to the point of pure perfection.

## Empowered

By Carmen Bellaire &amp; Kevin Siembieda

There are a few heroes out there who strive, more than any others, to be a true hero and protector of the innocent. These often seem to be heroes who have, themselves, suffered from a physical, mental or emotional trauma or lasting disability, but have overcome it to become true SUPER-heroes. Often their maladies are the results of a crime or injustice perpetrated against them, but they are just as often the result of luck (good or bad). This perceived injustice or weird happenstance ultimately gives the character super abilities and the inner drive to become a champion of justice — a true hero. Most often, this type of super being is self-made, acquiring super abilities through self-experimentation, accident, luck, genetic mutation or, as impossible as it may seem, sheer force of will alone.

The Empowered character is often the intellectual type, a thinker, planner and strategist with an indomitable will and a powerful (sometimes fanatical) sense of purpose and drive. These traits, and the fact that the Empowered hero is overcoming personal pain, affliction or other obstacles to help others, means the character tends to attract other super-heroes to his/her side as teammates, sidekicks, and agents/helpers. These "associates" often look to the hero as a source of inspiration as well as their leader and mentor and who often serves as their moral center. In comic books, characters like Batman, Daredevil and the Punisher immediately come to mind.

## Step One: The Usual

Determine the normal Eight Attributes, Hit Points, S.D.C., Alignment and Optional Rounding Out of Your Character as you would any character for Heroes Unlimited. Don't worry at all about any low physical attributes since they are not the thrust of this character and are often normal, unimpressive or limited.

Note: Keep all these initial stats in pencil as they will be modified later. Case in point, the Empowered Hero gets the following bonuses to his mental attributes due to his force of will and cerebral strength: +1D4 to I.Q., +1D4+3 to M.E., and +1D6 to M.A.

## Step Two: Hit Points &amp; S.D.C.

Hit Points: Roll to determine as usual. Add up the character's P.E. attribute number and an additional +1D6 per level of experience.

Structural Damage Capacity (S.D.C.): The Empowered hero gets a base amount of 20 S.D.C. points to start, plus any bonuses provided by physical skills and super abilities.
""", 9, 8, "Restored omitted Empowered heading and reordered the introduction, category-list entry, and creation steps to match the two source columns")
    replace(name, "Original concepts and material by Jay Fitzloff", "## Gestalt Superhumans\n\nOriginal concepts and material by Jay Fitzloff", 37, 36, "Restored missing category heading visible in the PDF")
    replace(name, "## By Carmen Bellaire\n\nNot all heroes", "## Imbued Heroes\n\nBy Carmen Bellaire\n\nNot all heroes", 57, 56, "Restored missing category heading and demoted the author credit")
    replace(name, "## morals\n\n## By Carmen Bellaire &amp; Kevin Siembieda", "## Immortals\n\nBy Carmen Bellaire &amp; Kevin Siembieda", 59, 58, "Corrected unreadable heading and demoted author credit")
    replace(name, "## SUPER-\n", "## Super-Invention\n", 68, 67, "Restored second line of the category heading")
    replace(name, "## By Carmen Bellaire and Kevin Siembieda\n\nA symbiotic organism", "## Symbiotic Superhuman\n\nBy Carmen Bellaire and Kevin Siembieda\n\nA symbiotic organism", 87, 86, "Restored missing category heading and demoted author credit")
    save_repairs(ROOT / "reports/ocr-review/source-repairs-04.json")


if __name__ == "__main__":
    main()
