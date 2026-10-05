"""Restore energy powers and two Mercenaries story paragraphs from visual scans."""
import re
from repair_source_passages import ROOT, load, replace, replace_region, replace_paragraph, save_repairs
from repair_final_power_passages import section


def main():
    stem='Heroes Unlimited - Powers Unlimited 1';name=stem+'.md'
    labels=['Range:','Damage:','Duration:','Attacks Per Melee:','Attacks per Melee:','Bonuses:','Special Attack:','Attacks per Melee & Limitations:']
    force=section(stem,25,'Energy Expulsion: Force\n','Energy Expulsion: Force Blast',
        [('maxmum','maximum'),('106 additional','1D6 additional'),('buo different','two different'),('ID20','1D20')],labels)
    blast=section(stem,25,'Energy Expulsion: Force Blast\n','Energy Expulsion: Icy Mist',
        [('6. I m','6.1 m'),('pounds!450','pounds/450')],labels)
    icy=section(stem,25,'Energy Expulsion: Icy Mist\n','23',[('IO foot','10 foot')],labels)
    icy+=' '+section(stem,26,'','Energy Expulsion: Plasma',
        [('ID6','1D6'),('men not','When not'),('Iow','low')],labels)
    plasma=section(stem,26,'Energy Expulsion: Plasma\n','Energy Expulsion:\nUltrasonic Screech',
        [('energized, or reddish-purple','energized, bluish-green or reddish-purple'),('106 per','1D6 per'),('demage','damage'),('roll (1020)','roll (1D20)'),('at\ndifferent targets','at two\ndifferent targets')],labels)
    ultra=section(stem,26,'Ultrasonic Screech\n','Energy Shield',
        [('ID4','1D4'),('104+2','1D4+2'),('muffie','muffle'),('10. 12','10, 12')],labels)
    regions=[('Energy Expulsion: Force',force),('Energy Expulsion: Force Blast',blast),('Energy Expulsion: Icy Mist',icy),('Energy Expulsion: Plasma',plasma),('Energy Expulsion: Ultrasonic Screech',ultra)]
    after='\n\n'.join('## '+title+'\n\n'+text for title,text in regions)
    replace_region(name,'## Energy Expulsion: Force\n','## Energy Shield',after,25,23,
        'Restored five energy powers in column order from PDF 25–26; all values visually checked. Printed Force Blast range lacks a unit after 3.6; retained. Printed Plasma example says 4D6 for each divided sixth-level blast; retained despite arithmetic inconsistency.')
    name='Rifts - Mercenaries.md'
    replace_paragraph(name,'Larsen leaned over the computer.', 'Larsen leaned over the computer. "May I?" Without waiting for assent, his metal arm started typing something on the computer. When he was done, he turned the computer back toward the Governor.',10,8,'Removed trailing artwork OCR and corrected typing from visual story scan')
    replace_paragraph(name,'He.o..re ey', '"You... you erased my projections!" Ryan stammered. "You..." He contained himself when he remembered where he was. His bodyguard was standing right behind him, but Larsen\'s man was also in the tent — a Juicer from the looks of him. Should violence erupt in the tent, the Governor\'s bodyguard would be as effective as a hay roof against a tornado. Ryan forced himself to look at the computer. The only thing left there was a number, neatly centered in the screen. "That\'s... that\'s twice the amount I offered you," he said in a hoarse whisper. Larsen turned toward the Juicer.',10,8,'Recovered unreadable story opening and removed trailing stray OCR letters; visually verified')
    # Correct only the one Nightwing speed paragraph, retaining adjacent stats.
    p=[x for x in re.split(r'\r?\n\r?\n',load(name)) if x.startswith('Speed: Driving on the ground:') and 'propulsion syste   n s' in x];assert len(p)==1
    replace(name,p[0], 'Speed: Driving on the ground: Not possible. Flying: The jet propulsion system enables the Nightwing to hover stationary up to 10,000 feet (3,050 m) or fly. Maximum flying speed is Mach 2.05 — 1,350 mph (2,160 km). Cruising and attack speeds vary, but tend to be between 100 and 500 mph (160 to 800 km), depending on the target and the mission. Some attacks involve launching missiles from 5+ miles (8+ km) away, others are direct strafing runs using the rail guns and mini-missile launcher. Note: A similar jet able to reach Mach 3 is still under development. Range: The nuclear power plant gives it continual power, but the jets overheat in 10 hours of continual use above 200 mph (320 km), or 4 hours if going above 600 mph (960 km). Going at below 200 mph (320 km) with occasional rest stops will allow the plane to travel indefinitely.',152,150,'Recovered omitted Nightwing hover altitude from visual scan; checked all speeds and operating-duration figures')
    save_repairs(ROOT/'reports/ocr-review/source-repairs-20.json')


if __name__=='__main__':main()
