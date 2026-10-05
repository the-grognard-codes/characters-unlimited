"""Restore PU1 headings corroborated by its independent OCR and ability index."""
from repair_source_passages import ROOT, replace, replace_region, save_repairs


def main():
    name = "Heroes Unlimited - Powers Unlimited 1.md"
    replace_region(name, "## Minor ew Abilities 11 r\n", "## Alp iabetical list", """## New Minor Super Abilities

## Powers Unlimited

Powers Unlimited seems a fitting title for a book that is filled with nearly 200 fully fleshed-out super abilities, not including the many nuances and sub-powers of many of them, especially the Major abilities. If this doesn't spice up your Heroes Unlimited campaign, nothing will.

These new super abilities are designed to provide even more variety for the Heroes Unlimited RPG, Second Edition and are suitable for any characters who wield strange and unusual powers, from superhumans in Rifts and Skraypers to mutants in After the Bomb and the Mutant Underground and even non-Palladium super-hero games. Many of the abilities are powerful, others strange; all are imaginative and fun, and should provide ideas for a couple hundred new super beings — heroes, villains and blundering NPCs.

This book is written by Palladium newcomer Carmen Bellaire, who gathered up powers and abilities from the pages of The Rifter (thank you, guys) and other ideas from various Palladium RPG books to mix in with a heaping helping of his own ingenious ideas. I then took the whole lot, tweaked, modified and fine-tuned them for publication, added a few of my own ideas for new super abilities, some dynamic artwork, and voila! You have one pulse-pounding sourcebook of super abilities.

Now all that's left to do is for you guys and gals to sit down and unleash your imaginations for a multitude of new adventures in the annals of role-playing. Go for it.

— Kevin Siembieda
""", 9, 7, "Recovered unreadable introduction and headings from visually checked page; registered/trademark symbols omitted consistently with the existing prose")
    replace_region(name, '## jical Indep.e 1i so known as "Body Freal .\n', "## Parts that can be detache dently:\n", """## Anatomical Independence

Also known as "Body Freak"

This strange power allows the super being to separate pieces of his own body, without pain or any ill effects or damage to himself, and send them off like mobile units! As amazing as it may sound, the separated body parts continue to function as if they were still connected to the super being, only functioning at long-distance like remote control drones. Blood still pumps through the character's veins and eyes still see, even if they are separated from the body by hundreds of feet. But damage done to a part is still taken off his S.D.C. and Hit Point totals, as if the body part was still attached to the rest of the body.

Range: 200 feet (61 m) +100 feet (30.5 m) per each level of experience. All limbs, except for eyes and ears, must be within line of sight to use accurately, but can be "called back" to the character and return like a homing pigeon. The super being can also sense the location of a missing body part(s) and is able to track it down to recover it.

Bio-Regeneration: A body part that is destroyed will regenerate after 72 hours of being destroyed. Any body part kept away from the weird character dies within 72 hours of separation, and under this situation, takes eight days to regenerate. Until the limb regrows, the character is without that appendage, eye, or ear.

Duration of Separation: 72 hours maximum, usually only a matter of minutes or hours. See Bio-Regeneration.

Attacks or Actions per Melee: Removing a body part counts as one melee action, then the limb has three melee actions/attacks per round. Meanwhile, the diminished character loses one melee action/attack for each separated part as well as loses the use of the particular organ or limb.
""", 14, 12, "Recovered unreadable ability introduction, range, regeneration limits and action costs from visually checked page; editorial correction of printed 'As amazing at' to 'As amazing as'")
    headings = [
        ("Alp iabetical list of New Minor Super Abilities", "Alphabetical List of New Minor Super Abilities", 10),
        ("Parts that can be detache dently:", "Parts that can be detached and used independently:", 14),
        ("t Rage", "Battle Rage", 16),
        ("Battle Rage Bonuses incle:", "Battle Rage Bonuses include:", 16),
        ("Beast ias", "Beastmaster", 16),
        ("Conr ict Electrici,", "Conduct Electricity", 20),
        ("iminal Intui", "Criminal Intuition", 21),
        ("C orway", "Doorway", 23),
        ('EnerExpuls L "ected Sound', "Energy Expulsion: Directed Sound", 24),
        ("Er rgy Expulsic·F: e", "Energy Expulsion: Force", 25),
        ("Energy Ex  sir · Force E st", "Energy Expulsion: Force Blast", 25),
        ("Energy E ouls n: Icy Mist", "Energy Expulsion: Icy Mist", 25),
        ("Enhanced napi", "Enhanced Leaping", 27),
        ("Expl c ig Sphel s", "Exploding Spheres", 28),
        ("Fabrth aterial Animation", "Fabric/Cloth Material Animation", 28),
        ("Gun Lit b", "Gun Limb", 31),
        ("Immune to Psiors", "Immune to Psionics", 33),
    ]
    for before, after, page in headings:
        replace(name, "## " + before + "\n", "## " + after + "\n", page, page-2,
                "Corrected heading using independent source-page OCR and the book's alphabetical ability list; no numerical rules changed")
    save_repairs(ROOT / "reports/ocr-review/source-repairs-07.json")


if __name__ == "__main__":
    main()
