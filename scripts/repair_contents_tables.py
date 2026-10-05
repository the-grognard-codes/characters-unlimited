"""Rebuild merged contents and missile tables from visually checked PDF pages."""
import json
import re
from repair_source_passages import ROOT, load, replace, replace_region, save_repairs


def table(data):
    rows=[line.rsplit('|',1) for line in data.strip().splitlines()]
    assert all(len(row)==2 and row[1].strip() for row in rows)
    return '| Entry | Printed page |\n| --- | --- |\n'+'\n'.join('| '+a.strip()+' | '+b.strip()+' |' for a,b in rows)


PU1_MINOR='''Introduction|7
Alphabetical List of New Minor Super Abilities|8
Minor Abilities Descriptions|9
Abnormal Energy Sense|9
Adrenaline Surge|9
Alter Physical Structure of Limb|10
Anatomical Independence|12
Animal Brother|13
Antennae|13
Battle Rage|14
Beastmaster|14
Blur|15
Bookworm|15
Bubble Glue|16
Charge Object with Explosive Energy|17
Claws|17
Color Manipulation|17
Conduct Electricity|18
Criminal Intuition|19
Danger Sense|19
Density Walking|20
Detonation or Explosive Power|20
Disintegration|20
Doorway|21
Earth Empowerment|21
Energy Claws|21
Energy Expulsion: Cold|21
Energy Expulsion: Directed Sound|22
Energy Expulsion: Energy Aura|22
Energy Expulsion: Electromagnetic Pulse|22
Energy Expulsion: Flame Ring|22
Energy Expulsion: Force|23
Energy Expulsion: Force Blast|23
Energy Expulsion: Icy Mist|23
Energy Expulsion: Plasma|24
Energy Expulsion: Ultrasonic Screech|24
Energy Shield|24
Energy Whip|25
Enlarge Body Parts|25
Enhanced Leaping|25
Exploding Spheres|26
Fabric/Cloth Material Animation|26
Feral|27
Flight: Energy|27
Flight: Hover|27
Flight: Insect|27
Flying Force Disc|28
Frequency Absorption|28
Giant|28
Glow Bug|29
Gravitational Plane|29
Gun Limb|29
Hardened Skin|29
Healing Power|30
Heavyweight|30
Heightened Sense of Awareness|30
Heightened Sense of Balance|30
Heightened Sense of Recall|30
Heightened Sense of Time|30
Hold Breath|31
Hyperdensity|31
Immovability|31
Immune to Magic|31
Immune to Psionics|31
Impact Resistance|31
Impervious to Cold & Freezing|32
Impervious to Control & Possession|32
Impervious to Disease & Illness|32
Impervious to Energy & Electricity|32
Impervious to Fear & Terror|32
Impervious to Light & Lasers|32
Impervious to Poison & Toxins|32
Impervious to Shadows & Darkness|32
Impervious to Sound & Vibrations|32
Increased Durability|32
Indestructible Bones|33
Instant Wardrobe|33
Instant Weapon|33
Iron Will|33
Life Sense|33
Lifting Field|34
Lightning Reflexes|34
Living Anatomy|34
Longevity|34
Lunar Strength|34
Mechanical Awareness|35
Mask – No Face, No Identity|35
Motion Detection|35
Multi-Tasking|36
Personal Force Field|36
Physical Perfection|36
Power Weapon|36
Power Bands|36
Quills & Spines|37
Resin|37
Seismic Power|38
Sense Death & Destruction|39
Sensory Orb|39
Shadow Meld|40
Shadow Shaping|40
Shadow Stepping|40
Sleep Dust|41
Sleeplessness|41
Sliding|41
Solar Powered|41
Sonar|42
Speed Tasking|42
Stench|43
Super Bounce|43
Super Burrowing|43
Super Hibernation & Stasis Field|44
Super Wind Blast|44
Supervision: Acute Sight|45
Supervision: Circular Vision|45
Supervision: Paranormal Sight|45
Supervision: Thermal Vision|45
Swing Line|46
Tentacles of Hair|46
Toy Control|46
Tractor Beam|47
Ultra-Hearing|47
Unnoteworthy – Forgettable|48
Un-Trackable|48
Venomous Attack|48
Warp Sound|49
Wave Rider|49
Weightlessness|50
Whip Attack|50'''

PU1_MAJOR='''New Major Super Abilities|51
Alphabetical List|51
Absorb Bio-Mass|52
Alter Physical Structure: Acid|52
Alter Physical Structure: Crystal|53
Alter Physical Structure: Light|54
Alter Physical Structure: Lava|55
Alter Physical Structure: Oil or Tar|56
Alter Physical Structure: Putty|57
Alter Physical Structure: Rubber|58
Alter Physical Structure: Sand|58
Alter Physical Structure: Shadow|60
Alter Physical Structure: Vapor or Fog|61
Alter Physical Structure: Wood|62
Amphibious|63
Borrow Power|64
Catastrophic System Failure|64
Chemical Secretion|64
Control Density|66
Copy Animal Attributes|67
Create Force Constructs|68
Dimensional Room|70
Distort Space|70
Divine Healing|71
Energy Doppleganger|71
Friction Control|72
Gateways|73
Generate Fog & Smoke|73
Geo-Thermal Energy|74
Liquefaction|76
Matter Expulsion: Crystal|77
Matter Expulsion: Metal/Steel|77
Matter Expulsion: Stone|78
Mega-Wings|79
Mirror Mastery|80
Power Touch|81
Re-Channel and Expel Energy|81
Reconstruction|81
Regeneration Ultima|82
Rocket Fists|82
Spiral/Vortex|83
Super-Consumption|84
Supernatural Bite/Jaws|85
Totem Energy Aura|85
Vertigo Field|85
Weapon Energy Extensions|86
Weapon Melding|86
Psionics|87
A Few Notes on Psionics|87
New Psionic Abilities|88
Mimic Skills|91
Sensory Link|93
Wound Transfer|95'''

PU1_QUICK='''Energy Powers|21 & 81
Giant|28
Healing|30
Healing: Divine|71
Healing: Regeneration Ultima|82
Heightened Senses (various)|30
Instant Wardrobe|33
Magic: Abnormal Energy Sense|9
Matter Expulsion starts|77
Removable Limbs (see Anatomical Independence)|12
Sense: Crime (see Criminal Intuition)|19
Sense: Danger (see Danger Sense)|19
Sense: Death (see Sense Death & Destruction)|39
Sense: Life (see Life Sense)|33
Sense: Magic (see Abnormal Energy Sense)|9
Sense: Motion (see Motion Detection)|35
Sense: Sonar|42
Sense: Sensory Link (psionic)|93
Senses: Heightened|30
Sensory Orb|39
Weapon: Alter Physical Structure of Limb|10
Weapon: Energy Extensions|86
Weapon: Exploding Spheres|26
Weapon: Flying Force Disc|28
Weapon: Force (see Create Force Constructs)|68
Weapon: Gun Limb|29
Weapon: Instant Weapon|33
Weapon: Melding|86
Weapon: Power Bands|36
Weapon: Power Weapon|36
Weapon: Quills & Spines|37
Weapon: Whip (see Whip Attack)|50'''

PU2_TOC='''Expanding the concept of heroes|7
Determining Your Power Category|7
Random Power Category Table|7
New Power Categories|7
Empowered|8
Step 3: Determining Impairment & Super Abilities|8
The Physical Impairment|8
Overcoming the Disability|11
Table 1: Emotional Inspiration|11
Table 2: Physical Compensation|11
Bionics|11
Physical Metamorphosis: Demigod|11
Physical Metamorphosis: Monster|12
Physical Metamorphosis: Psionic|12
Super Abilities to Compensate|13
Lycanthropy|15
Robotics|15
Underwater Abilities|15
Step 5: Alignments & Other Stuff|16
Experience Levels|16
Eugenic Heroes|16
Creating the Eugenics Hero|17
Genetic Construction Budget|18
Buying Eugenic Features|18
Descriptions of Eugenic Features|18
Cloned Replacement Parts|18
Modified Internal Organs|19
Glands|20
Physical Augmentation Features|21
Armor Rating (Natural)|22
Attribute Enhancement|22
Bio-Regeneration|22
Digging, Tunneling & Excavation|23
Enhanced Musculature & Strength|23
Massive Build|24
S.D.C. Augmentation|24
Spinnerets|24
Resistance|25
Reinforced Skeleton|25
Additional & Special Appendages|25
Arms & Hands|25
Flight Appendages|27
Legs|27
Serpentine Lower Body|27
Prehensile Appendage Features|28
Prehensile Tail|28
Prehensile Trunk|28
Eugenic Tails|29
Tail for Combat|29
Enhanced Senses|29
Eyes & Vision|29
Ears/Hearing|30
Other Enhanced Sensory Features|30
Antennae|30
Sonar|31
Genetic Weapons|31
Chemical Spray|32
Claws|32
Horns|33
Stinger|33
Optional Background Data|34
The Sponsoring Organization|34
Condition of Eugenic Volunteer|34
Possible Disfigurement|35
Possible Insanity|36
Step 6: Other Stuff|36
Experience Levels|36
Gestalt Superhumans|36
Nature of the Gestalt|37
Animal Gestalts|37
Step 3: Powers of the Animal Gestalt|38
The Controlling Animal Force/Intelligence|38
Determining Animal Gestalt Abilities|41
Physical Human Gestalt|43
Step 3: The Powers & Limitations|44
Who is in Control of the Gestalt|45
Super Abilities for the Human Gestalt|46
Psychic Human Gestalt|47
Step 3: The Powers & Limitations|48
Super Abilities for the Psychic Human Gestalt|49
Plant Gestalts|50
Step 3: Powers of the Plant Gestalt|50
Determining Plant Gestalt Abilities|54
Imbued Heroes|56
Step 3: Imbued Super Abilities|56
Imbued Super Abilities|57
Step 6: Equipment, Budgets & Stuff|58
Immortals|58
Step 3: Super Abilities & Immortality|59
The Nature of the Immortal|60
Super Abilities & Other Powers of Immortals|63
The Reason for Being on Earth|64
Personal Weapon|66
Super-Invention|67
Step 3: The Super-Gizmo & Powers|67
Who is the Character|67
The Physical Appearance|69
Power Level of the Super Abilities|69
The Super Abilities the Gizmo Instills|69
Repairing the Super Invention|70
Minor Heroes|71
The Minor Hero Option|71
Modifying Other Power Categories|72
Natural Genius|72
Step 3: The Power of Intelligence|73
Mental Disciplines|73
Step 6: Rounding Out & Other Stuff|75
Supersoldier|76
Step 3: Background Data|76
Nature of the Test Subject|77
Replication of the Supersoldier Process|77
Number and Type of Super Abilities|78
Special Supersoldier Enhancement Table|78
Alternative Types of Supersoldiers|81
Brain Implant Augmentation|81
Chemical Enhancement|82
Endoskeletal Replacement|83
Step 6: Rounding Out & Special Equipment|83
Special Weapons|84
Prototype Vehicle|85
Other Stuff|86
Symbiotic Superhuman|86
Step 3: Background & Abilities|87
Where Did the Symbiote Come From|87
The Symbiote's Intelligence|88
Determining Super Abilities|89
The Consequences of Removing the Organism|89
Ancient Weapons Master|90
Step 3: Special Abilities, Education & Skills|90
Specialties of Weapons Training|91
Craft Weapons|91
Penalties for Crafting Ancient Weapons|91
Time Restrictions|91
Weapons Expertise|91
Melee Weapons Expertise|91
Weapon Master|91
Parry Projectile Bonus|92
Disabling Strike|92
Missile Weapon Expertise|92
Bow Mastery|92
Trick Shooting|92
Multiple Shot|92
Dodge Projectile Bonus|93
Throwing Mastery|93
Step 4: Equipment Budget|93
Step 6: Rounding Out|93
Experience Levels|93
New Super Abilities|94
Hero Character Sheet|96'''

PU2_QUICK='''BIA: Brain Implant Augmentation (see Supersoldier)|81
Bio-Regeneration (see Eugenics)|22
Chemical Enhanced Hero (see Supersoldier)|82
Crippled/Physically Challenged Hero (Empowered)|8
Digging, Tunneling & Excavation (see Eugenics)|23
Endoskeleton (see Supersoldier)|83
Genetic Engineered Heroes|16
Genetic Body Parts (see Eugenics)|18
Inventions that provide Super Abilities|67
Magic Weapons (see Immortals)|66
Mental Disciplines (see Natural Genius)|73
Power Categories, brief overview|7
Power Category: Ancient Weapon Master|90
Power Category: Empowered|8
Power Category: Eugenic Heroes|16
Power Category: Gestalt Superhumans|36
Power Category: Imbued|56
Power Category: Immortals|58
Power Category: Minor Heroes|71
Power Category: Super-Inventions|67
Power Category: Supersoldier|76
Super Abilities (Minor): Mental Disciplines|73
Super-Gizmos (see Super-Inventions)|67
Vehicles (see Supersoldier)|85
Weapons (see Supersoldier)|84
Weapons: Magical (see Immortal)|66
Weapons: Super-powered (see Inventions)|67
Wings (see Eugenics)|27'''


def main():
    replace_region('Heroes Unlimited - Powers Unlimited 1.md','## Contents','## New Minor Super Abilities',
        '## Contents\n\n'+table(PU1_MINOR+'\n'+PU1_MAJOR)+'\n\n## Quick Find\n\n'+table(PU1_QUICK),6,4,
        'Rebuilt both contents pages and quick-find list; visually checked labels and printed page assignments against PDF pages 6–7')
    replace_region('Heroes Unlimited - Powers Unlimited 2.md','## Contents','## Expanding the concept of heroes',
        '## Contents\n\n'+table(PU2_TOC)+'\n\n## Quick Find\n\n'+table(PU2_QUICK),5,4,
        'Rebuilt both contents pages and quick-find list; visually checked labels and printed page assignments against PDF pages 5–6')
    name='Rifts - Merc Ops.md'
    matches=[m.group().rstrip('\n') for m in re.finditer(r'(?m)^\|[^\n]+\n(?:\|[^\n]*\n?)+',load(name)) if 'Short Range Missiles' in m.group()]
    assert len(matches)==1
    # Every row agrees with the independently viewed Merc Ops PDF, including its unit inconsistencies.
    data=json.loads((ROOT/'reports/ocr-review/source-repairs-05.json').read_text(encoding='utf8'))
    replace(name,matches[0],data['repairs'][0]['after'],158,158,
        'Rebuilt four missile charts, 32 rows and 192 cells; visually verified every entry against Merc Ops PDF 158. Printed unit inconsistencies retained.')
    save_repairs(ROOT/'reports/ocr-review/source-repairs-17.json')


if __name__=='__main__':main()
