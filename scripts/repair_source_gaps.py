"""Restore recoverable text and explicitly identify a damaged source page."""
from repair_source_passages import ROOT, replace, save_repairs


def main():
    name='Rifts - Ultimate Edition.md'
    replace(name,'- 61-80 Reduce both the range and duration of the spell by 20%.',
        "- 01-20 Reduce spell damage or effects by 1D4x10%.\n- 21-40 Reduce spell duration by 1D4x10%.\n- 41-60 Reduce the spell's range by 1D4x10%.\n- 61-80 Reduce both the range and duration of the spell by 20%.\n- 81-00 Lucked out, no additional problems.",191,188,
        'Restored all five original table entries after verification detected an over-broad replacement in batch 18')
    name='Rifts - World Book 09 - South America 2.md'
    text="""The advanced bionic systems provided by the Dakir make these cyborgs extremely stealthy, fast and maneuverable. To increase their stealth and movement capabilities, the 'borg has a nearly skeletal shape (only a metallic "spinal column" links the upper torso with the legs, for example). The head is sculpted to suit individual tastes. The cyborgs enjoy having intimidating or monstrous designs on their faces and heads, the better to scare off their enemies. A special system included in the 'borg package is a virtual reality simulator that 'borgs can access during their free time to avoid boredom and depression. The VR system allows the 'borgs to live out any fantasies and temporarily escape their grim reality.

## Destroyer 'Borg Abilities and Bonuses:

1. Full Bionic Reconstruction: The Destroyer 'borgs undergo full bionic conversion, replacing 95% of all body mass with metal, plastic and ceramic components. Only a small fraction of the brain/spinal cord remains human, buried deep in the heart of the machine body. In effect, the character is a robot with a human brain, and his strength and endurance become 100% robotic. This extensive reconstruction and the use of highly advanced alloys (at least 50 years ahead of what Triax is currently capable of) produces a tougher, yet lighter cyborg warrior.

<!-- SOURCE GAP: PDF page 108 / printed page 107 has a corrupted lower half. The remaining M.D.C. description, abilities 2–4, and the beginning of the paragraph continuing at the top of the right column cannot be recovered from this copy. Consult reports/ocr-review/README.md before ingestion. -->

like his own self, or have any shape he programs into the system. The Dakir left behind an abundance of different features for the entertainment of the cyborg warriors. Among them were forest scenes, love stories, heroic adventures, sports tales, etc.

5. Robotic Attribute Bonuses: Reflexes, strength and speed are well above the human norm, or even the limits of normal cyborgs. The character gains a robotic P.S. of 35, P.P. 26., and speed running is 70 mph (112 kmph). Plus the stealth systems add +5% to prowl (the 'borg design does not have a prowl penalty like the normal full conversion cyborg does); enemy sensors are at -15% to detect it, and the 'borg is -15% to be sensed by detect ambush, tracking or similar skills. Additionally, advanced optical and targeting systems grant the cyborg a number of combat bonuses.

6. Sensory Bonuses: Advanced bionic sensors give the 'borg the equivalent of multi-optic eyes (as per the visor described under the Megaversal Trooper O.C.C.), amplified hearing, motion detector, radar detector and personal radar (range: 5 miles/8 km).

"""
    target='Full robot P.S. means mega-damage from hand to hand combat.'
    replace(name,target,text+target,108,107,
        'Recovered all complete readable paragraphs omitted by OCR from the visibly damaged PDF page. Marked the unrecoverable source gap instead of inventing missing abilities or numerical values. Truncated M.D.C. paragraph omitted pending an intact source.')
    save_repairs(ROOT/'reports/ocr-review/source-repairs-19.json')


if __name__=='__main__':main()
