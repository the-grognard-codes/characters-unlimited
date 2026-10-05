"""Repair visually checked body passages and duplicated PU3 source pages."""
from repair_source_passages import ROOT, load, replace, replace_paragraph, replace_region, save_repairs


def main():
    name = "Rifts - World Book 09 - South America 2.md"
    replace_paragraph(name, "Hand to Hand: Expert can be changed to hand to hand: marasits", 'Hand to Hand: Expert can be changed to hand to hand: martial arts or assassin at the cost of one "other" skill.', 147, 147, "Recovered unreadable Condoroid combat-skill option")
    replace_paragraph(name, "The massive robot is laden", 'The massive robot is laden with heavy armor and weaponry. The "trunk" is designed to act as a close combat weapon, and is tipped with a spiked "morning star" ball that can shatter buildings and hammer through M.D.C. plates with a few flailing blows. Two heavy missile launchers allow the pilot or gunners to engage long-range targets on the ground or the air. For direct fire, a turret on top uses a vehicle version of the infamous "boom gun" used in the Glitter Boy armor! The "tusks" of the Mastodon are laser cannons that shoot devastating double blasts. A short-range particle beam weapon mounted on the belly can be used against masses of infantry troops or light vehicles, and two mini-missile MLRS boxes provides protection against enemy missiles and aircraft, as well as to strike at targets up close.', 175, 175, "Recovered corrupted Mastodon description")
    replace_paragraph(name, "The Larhold of South America have", 'The Larhold of South America have changed their tactics. Although they still roam about and rarely stay anywhere for periods longer than a month, these nomads no longer travel throughout the Megaverse. Instead, each tribe or sub-tribe has a defined "range" which they travel through in a migratory route. Along the way, they plunder all neighboring lands and rival tribes; war between two Larhold tribes is fairly common, and just as vicious as when fighting non-Larhold. A few tribes have even allowed some towns and cities to survive with one condition: whenever the Larhold arrive in town, a huge tax is collected from that city, ranging in anything from gold and weapons to slaves and services. In return, the Larhold do not destroy the community and let the inhabitants rule themselves as they see fit, so long as they do not interfere with the nomads.', 184, 184, "Recovered corrupted Larhold history sentence")
    name = "Aliens Unlimited.md"
    replace_paragraph(name, "For eons the gallopas", "For eons the gallopas had thrived under the slightly radioactive skies of their homeworld Gagine. Every hundred years, the people were witnesses to an incredible cosmic anomaly that lit up the midnight sky with a display of swirling lights, culminating six hours later with a fiery glow that made it seem as if the atmosphere were on fire. The centennial phenomenon was a sacred Gallopa holy day, a once in a lifetime event that signaled a week of celebration. Gallopas everywhere gathered for the event. In addition, millions of other people arrived in spaceships from all corners of the galaxy to watch and record the legendary event and join in the celebration as they had for the last 300 years. One exception would be the crew of the battleship Babella, who went on a mission to aid a space station besieged by pirates.", 75, 74, "Recovered missing phrases in the Gallopas history")
    name = "Rifts - World Book 06 - South America 1.md"
    text = load(name)
    a = text.index("Bonuses: +3  to  initiative")
    b = text.index("Weapon Proficiencies:", a)
    # Preserve the following list marker, but join the continuation into its rule.
    before = text[a:b-2]
    replace(name, before, "Bonuses: +3 to initiative, +6 to strike, +6 to parry and dodge, +18 to S.D.C. damage, +2 to save vs magic, +4 to save vs psionics, +9 to save vs horror factor. Immune to all forms of mind control and psionic and magic sleeps and paralysis.\n\n", 42, 41, "Joined the cross-column continuation of Hak-Talon's bonuses")
    name = "Rifts - World Book 02 - Atlantis.md"
    replace(name, "m\n\nHEX区\n\nD国SE\n\n", "", 1, "cover", "Removed OCR hallucinations from the cover illustration; all printed cover text is already retained")
    name = "Heroes Unlimited - Powers Unlimited 3.md"
    text = load(name)
    marker = "## Pestilence"
    a = text.index(marker)
    b = text.index(marker, a + len(marker))
    replace(name, text[a:b], "", [86,87,88,89], [86,87], "The PDF contains printed pages 86-87 twice, with the first page 87 rotated. Removed the garbled first extraction of Pestilence/Petrification/Polymorph/Portals; retained the complete upright duplicate. Verified rotated PDF 87 against upright PDF 89.")
    replace(name, "While the character cannof", "While the character cannot", 89, 87, "Corrected transcription against the upright source")
    replace(name, "form of objects with tegs", "form of objects with legs", 89, 87, "Corrected transcription against the upright source")
    name = "Rifts - World Book 21 - Splynn Dimensional Market.md"
    replace_region(name, "The only  thing  standing  in  his  way", "Disposition: Stern", """The only thing standing in his way was the fact that he was physically weak compared to most other Kydian Overlords. However, his sharp mind, head for strategy and tactics, and natural fighting acumen made him a candidate for Bio-Wizard augmentation. K'Ronn Sol became a Powerlord, but not just the run of the mill Powerlord, he was offered a very special, but very dangerous experimental process reserved for only the most elite warriors. Of course, he accepted and so it was that Overlord K'Ronn Sol became Powerlord Cronus, Head of Splynn Security.

Like all Powerlords, all his physical attributes have been enhanced and he is an M.D.C. creature. In addition, his five senses are also enhanced and supplemented by additional psionic abilities. However, his greatest and most unique power lies with the array of magic powers that even many Conservators are not offered. Moreover, he was given a Temporal Link, a symbiotic organism that enables Cronus to see the ripples in the time stream that indicate the use of Temporal Magic and most forms of dimension altering magic (including dimensional portals, teleportation, Time Slip and others). This gives him a tremendous edge in combating Shifters, True Atlanteans, Temporal Wizards and Raiders and supernatural beings who can dimensionally teleport and manipulate time and reality. Unfortunately, the parasite also dramatically shortens its host's life span. Cronus is well aware of this fact and knows that he may only have 3-5 years left. Still, he knew the risks when he volunteered for the augmentation and is proud to lay down his life in service to Lord Splynncryth as one of his greatest champions. Such is the dedication of Powerlord Cronus.

Real Name: K'Ronn Sol

Alignment: Aberrant

Attributes: I.Q.: 15, M.E.: 21, M.A.: 18, P.S.: 50, P.P.: 21, P.E.: 21, P.B.: 10, Spd: 44. Strength and endurance are considered to be supernatural.

- M.D.C.: 325, plus he can transfer 597 M.D.C. from his Absurr Life Node to himself at any time.
- Size: 10 feet (3 m) tall and about 550 lbs (247.5 kg), all muscle.
- Age: 32 years
""", 56, 55, "Restored column order, omitted real name, fragmented statblock, and corrupted spelling in Powerlord Cronus's description")
    save_repairs(ROOT / "reports/ocr-review/source-repairs-06.json")


if __name__ == "__main__":
    main()
