"""Restore two damaged abilities from the visually checked PU1 PDF page 22."""
from repair_source_passages import ROOT, replace_paragraph, replace_region, save_repairs


def main():
    name = "Heroes Unlimited - Powers Unlimited 1.md"
    replace_region(name, "## Density Wa ir 4\n", "## Disintegration\n", """## Density Walking

By Carmen Bellaire &amp; Kevin Siembieda

This ability allows the character to walk or run, without serious penalty, on various materials at his full Speed.

At first level the super being can walk on loose gravel, sand, and similar unstable surfaces where people might slip and slide.

At second level he can walk over mud, ice or any slimy, slippery surface.

At third level the character can walk on top of sticky, gooey surfaces without impairment.

At fourth level the character can walk on the surface of water regardless of its depth, but cannot ride waves and can get knocked down and submerged by large waves. Can also walk on any soft, gushy surface.

At fifth level the character can walk on mist, fog or smoke, though this requires the character to move up or down an imaginary "stairway" or the billows of smoke. Can also walk on the top of the blades of tall grass, weeds, and bushes.

At sixth level he can actually walk on clouds, though he probably needs to exit an aircraft or walk up a flight of "smoke" to get to the clouds.

Note: Cannot walk on air itself. Carrying smoke grenades or other means of making smoke is common among characters with this super ability. However, while the character can walk on smoke, fire, heat and noxious fumes from smoke all have their normal effects and damage on the character (may need a gas mask or oxygen supply like a scuba diver). Maximum Altitude: 30,000 feet (9,144 m).

Range: Self.

Duration: As desired and conscious.

Penalty: The power may also be used with abilities such as Extraordinary Speed or Sonic Speed, but the character loses one attack per melee round due to the additional focus required to maintain both powers.

## Detonation or Explosive Power

The character is able to generate an explosive blast similar to a hand grenade, with the blast radius centered around the character himself. The super being is impervious to his own explosions and usually finds it amusing to catch opponents off guard by, effectively, blowing himself up. This power is great for shaking off numerous attackers in hand to hand combat, smashing through doors and barriers, stopping vehicles, creating a diversion, and making an explosive entrance.

Range: The character can control the concussion blast radius around him in the following increments: four feet (1.2 m), 10 feet (3 m), 15 feet (4.6 m), 20 feet (6.1 m) and 30 feet (9.1 m); increase each by 10 feet (3 m) when used underwater.

Damage: 2D6 +1D6 per level of experience, which cannot be reduced; it always does full damage. Area effect; no aimed shot or long-range attacks are possible, but everybody within the blast radius takes full damage from the explosion.

Explosive fisticuffs: In the alternative the character can punch or kick with an explosive boom and impact that does 3D6 damage and unleashes a powerful force that knocks the individual off his feet and 1D4 yards/meters per level of experience (a directed force). The victim loses initiative, one melee attack and a portion of his pride. This attack counts as two melee attacks for the explosive character and cannot be used as a parry or in any other combat maneuver.

Duration: Instant.

Attacks per Melee: Each explosive blast counts as two melee attacks.

Bonuses: The super being is resistant to explosions and heavy impacts like getting hit by a car (takes half damage from both) and that can be reduced by half again if he makes a successful roll with punch, fall or impact. And he enjoys an extra +2 bonus to do so in addition to bonuses he may gain from Hand to Hand Combat skills and other powers.
""", 22, 20, "Recovered unreadable abilities, omitted knockback dice, and a dropped zero in the altitude limit; verified original rendered page")
    replace_paragraph(name, "T s is one of r", "This is one of the most dangerous minor powers available. By weakening every molecular bond in an object, the character can cause severe damage to that object by separating its molecules; in effect, disintegrating or vaporizing it. This power is focused through the eyes in a type of death gaze that is summoned up at will.", 22, 20, "Recovered corrupted Disintegration introduction from the rendered PDF")
    save_repairs(ROOT / "reports/ocr-review/source-repairs-03.json")


if __name__ == "__main__":
    main()
