"""Second repair batch: source-checked Powers Unlimited ability boundaries."""

from repair_source_passages import ROOT, replace_region, save_repairs


def main():
    name = "Heroes Unlimited - Powers Unlimited 1.md"
    replace_region(name, "## ower a1\n", "## Heightened Sense of Time\n", """## Healing Power

The character can heal others by touch and nullify poisons and drugs in the bloodstream, stopping the damage and penalties from the toxin at the moment of the healing. Can also cure minor diseases and conditions (hangover, headache, stomach ache, nausea, itching, bug bite, minor burns, etc.).

Range: Touch.

Duration: Permanent.

Healing Damage: 3D6 Hit Points or S.D.C. or stops poison, drugs and their damage and penalties at the moment of healing.

Bonuses: The super being is +5 to save vs poisons and toxins, +2 to save vs nonlethal drugs and disease, and +20% to save vs coma/death. Also add 2D4 to P.E. attribute.

Limitations &amp; Penalties: Each act of healing temporarily weakens the super being. Reduce P.E. attribute number by one and Hit Points by 1D4 per each act of healing. Both recover completely after a good night's sleep (minimum six hours).

## Heavyweight

This character is a true heavyweight, add 2D4x20 pounds (18 to 72 kg) to the character's weight, and the character appears heavy/bulky with thick arms, legs, waist and neck, like a football linebacker or heavyweight boxer (George Forman style). This mass is not just fat, but dense muscles, so the character moves with surprising agility and speed. He is able to absorb and deliver punishment that would crush a lesser man.

Bonuses: +10 to damage from punches, kicks, head butts, body flips/throws, and hand-held melee weapons (sword, mace, club, frying pan, chair, etc.). This is in addition to bonuses from other powers, P.S. attribute, and combat skills. Also +1 to his P.E. attribute, +1D6x10+12 to his S.D.C., has a Natural A.R. of 8, but reduce Spd. attribute by 20%.

## Heightened Sense of Awareness

The character has an uncanny awareness of people and events transpiring around him. The ability manifests itself as a strange sense of deja vu and readiness as he anticipates the events unfolding around him a scant second or two before they happen. This enables the hero to avoid dangerous situations, help others, or to make the best choice and be ready for action.

Bonuses: Due to this preparedness, the character doesn't usually suffer from surprise and is +2 on initiative, +1 to roll with punch, fall or impact, +2 to save vs Horror Factor, and gets an automatic dodge.

## Heightened Sense of Balance

The inner ear of the hero is exceptional, able to counter and compensate for even the most dizzying of potential circumstances. The hero's balance is unparalleled.

Bonuses: The character can fire an aimed, Called Shot or burst without penalty while moving, running, riding a horse, driving a car, somersaulting, standing on his head, hanging upside down and so on. In addition, he also enjoys these bonuses: +10% to Acrobatics, Gymnastics and Climbing skills, +5 to any maintain balance rolls and never gets dizzy, and is +2 to roll with punch, fall or impact.

## Heightened Sense of Recall

This character has a remarkable type of photographic memory when it comes to remembering factual data (events, names, dates, numbers, etc.). Remembers most things he has read, heard, seen or experienced. Specific blocks of information can be recalled at will and in perfect detail if learned recently (within the last three months), otherwise roll on the table below.

Range of Recollection:

- 01-66% Remembers every detail, much of it word for word.
- 67-90% Details are forgotten, but the full essence of the ideas and most important details are clear.
- 91-00% Can only recall the most basic concepts and general ideas and intention, no solid or exact details.
""", 32, 30, "Restored five badly damaged ability sections, including missing healing costs, dice, speed penalty, and recall ranges; visually checked the full page")

    replace_region(name, "## Ir r - ous to Cold &amp; Freezing\n", "## Increased Durability\n", """## Impervious to Cold &amp; Freezing

Just as the name suggests, this power makes the super being completely impervious to cold and freezing temperatures. Walking out in the antarctic is like a day on the beach for this character.

Range: Self.

Duration: Constant.

Bonuses: Cold-based attacks do no damage to this character unless magical, and even then magic cold does only half damage.

## Impervious to Control &amp; Possession

The character is immune to the effects of mind control and domination, be it from magic, psionics, super abilities, drugs or any other sources, nor can the character be possessed by any outside entity, spirit or other super being, etc.

Range: Self.

Duration: Constant.

## Impervious to Disease &amp; Illness

The character is totally immune to all forms of disease and illness, including magically or psionically induced illness and even radiation sickness. This power also prevents the psionic "Bio-Manipulation" attack.

Range: Self.

Duration: Constant.

## Impervious to Energy &amp; Electricity

The super being is completely impervious to electricity, energy attacks, radiation, stun, laser and ion weapons. Magical energy blasts, fire, lightning, flaming swords and other types of magical energy attacks do half damage. Most other types of spells and magic do full damage.

Range: Self.

Duration: Constant.

## Impervious to Fear &amp; Terror

This power makes the super being completely impervious to the effects of Horror Factor (and awe), as well as totally immune to other forms of terror, including magically or psionically induced forms of fear and horror.

Range: Self.

Duration: Constant.

## Impervious to Light &amp; Lasers

This power makes the superhuman completely impervious to all light based attacks, including magical lights and laser weapons (they bounce off harmlessly). Additionally, the character cannot be blinded by bright lights and can see clearly in light so intense that others must squint or shield their eyes.

Range: Self.

Duration: Constant.

## Impervious to Poison &amp; Toxins

The character is immune to the effects of lethal gases, drugs, chemicals, herbs, poisons, toxins and venoms, including magical ones, as well as potions.

Range: Self.

Duration: Constant.

Penalties: Good, healing medicine lasts only half as long and does half as much good/healing. +2 to save vs non-lethal drugs and even if he succumbs, the penalties and effects are only half as severe (do half damage) and last for only half as long.

## Impervious to Shadows &amp; Darkness

Prevents the character from being harmed by shadow-based attacks, including magic shadow attacks, Shadow Beasts and unnatural darkness. The character can also see in unnatural darkness without penalty and has limited nightvision, with a range of 60 feet (18.3 m).

Range: Self.

Duration: Constant.

## Impervious to Sound &amp; Vibrations

Impervious to Sound and Vibrations makes the character completely impervious to all types of sound-based attacks, including magical noises and sonic weapons, as well as vibration based attacks. This character cannot be permanently deafened by any means and temporary deafness lasts half as long.

Range: Self.

Duration: Constant.
""", 34, 32, "Restored power names, boundaries, and nine resistance descriptions; the missing Energy & Electricity heading had joined two distinct powers. Supplied 'forms' in the printed phrase 'other of terror' as an editorial grammar correction")

    replace_region(name, "## Mechanical Awareness\n", "## Multi-Tasking\n", """## Mechanical Awareness

Inspired by Kevin Siembieda

The character is aware of, and able to react to, all mechanical devices and weapons used against him, including guns, energy weapons, power armor, robots, cybernetics, bionic weapons and computers, sensors, vehicles and other devices. Basically any machine with moving parts or that uses electricity or has a computer chip.

This awareness lets the character know the very instant a targeting computer or radar locks onto him, the moment he falls into the cross-hairs of a gun, when a trigger is about to be squeezed, when an energy cell charges to fire, or a cybernetic muscle tenses or a turret begins to turn. More than that though, the character can actually feel the weapons and war machines as they come online or are drawn to use against him. It is as if he can see them as clearly as a weapon being pointed in his face.

Range: Self and any technology used against him within a 50 foot (15.2 m) radius per level of experience.

Duration: Constant and automatic.

### Abilities Against Weapons and Technology

1. Negates any bonuses provided by the technology, i.e., weapon, computer targeting, etc., straight unmodified roll when fired by a machine or computer enhanced.
2. The character knows what his opponent is doing the same instant that his opponent does it, enabling him to react a split second faster: +3 on initiative against attacks from modern guns and machines (bionics, robots, etc.) and +4 on initiative against artificial intelligence, computers and automated defense systems.
3. The character's gun-toting or high-tech laden opponent is at -3 to dodge the character's attacks and loses two melee attacks/actions due to time spent compensating for the superhuman's amazing instincts, agility, and moves from Mechanical Awareness.
4. Sense the presence of surveillance bugs, listening devices, concealed cameras, and spy robots.
5. The Mechanically Aware character has an automatic dodge with a +4 bonus, but only when up against technology and machine opponents (and can twist, turn, duck, somersault, and otherwise dodge attacks from "guns" and advanced weapon systems without using up a melee attack/action (otherwise dodges as normal). The hero is so fast, mobile and "aware" of mechanized systems that he or she can attempt a dodge against most weapons fire!

## Mask - No Face, No Identity

The character can transform to having a seemingly blank, featureless face or a stylized mask-like covering (may be costume-like, demonic or surreal) as if wearing some kind of facial covering, only it is impossible to remove, as if glued to the face. Even the eyes seem pale and almost blank. Furthermore, the character has no finger- or footprints, nor any distinguishing birthmarks, and if the character has tattoos and scars, they too disappear when this power of disguise is used.

Range: Self only.

Duration: Willed into effect and willed away, so even if the character is rendered unconscious his features and prints remain gone.

## Motion Detection

With sensitive hairs and eardrums, among other subtle modifications, the character is able to pick up the slight, but telltale signs of motions and changes in air pressure around him and moving toward him. This ability is so sensitive that the character can physically feel changes in air currents caused by the movements of others. This means he cannot be snuck upon or caught by surprise from a nearby opponent (long-range blasts and bullets are effective because of their great speed and small size).

Range: The motion detection sense only works in a 60 foot (18 m) diameter around the character.

Bonuses: +1 on initiative, +1 to parry and dodge.

### Motion Detection Abilities &amp; Senses

Track Movement: Can track the movement and location of those moving around him without actually looking and even if they are invisible or prowling. Tracking by motion detection alone: 42% +4% per level of experience (+20% if the target is larger than a human, a robot or vehicle).

Estimate Distance: 50% +4% per experience level.

Estimate Direction &amp; Speed: 40% +4% per experience level.

Estimate Location: 40% +4% per experience level even if the super being is blind or can't see his (invisible or concealed) opponent. Penalties for being blind or fighting an invisible foe are only -3 to strike, parry and dodge.
""", [37, 38], [35, 36], "Recovered missing combat conditions, put numbered Mechanical Awareness abilities back in their section, and restored two garbled ability names; page 37 visually checked and page 38 continuation checked against independent OCR")
    save_repairs(ROOT / "reports/ocr-review/source-repairs-02.json")


if __name__ == "__main__":
    main()
