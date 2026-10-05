"""Restore damaged sections from visually reviewed local scans, with page evidence."""
import json
import re
from repair_source_passages import ROOT, replace, replace_paragraph, replace_region, save_repairs


def scan(stem, page):
    return json.loads((ROOT/'tmp/pdfs/scans'/stem/'ocr.json').read_text(encoding='utf8'))[page-1]['text']


def section(stem, page, start, end, fixes=(), breaks=()):
    text=scan(stem,page).replace('\r\n','\n')
    if start:
        text=text.split(start,1)[1]
    text=text.split(end,1)[0]
    for before,after in fixes:
        assert before in text, before
        text=text.replace(before,after)
    text=re.sub(r'(?<=\w)-\r?\n(?=[a-z])','',text)
    for label in breaks:
        text=text.replace('\n'+label,'\n\n'+label)
    return re.sub(r'(?<!\n)\n(?!\n)',' ',text).strip()


def main():
    stem='Heroes Unlimited - Powers Unlimited 1'; name=stem+'.md'
    reason='Restored missing words, values, and reading order from visually reviewed scan'
    replace_paragraph(name,'ds ks to Carmen',"Special Thanks to Carmen for his first contribution to Palladium Books. To Ramon Perez for a powerful and hero filled cover, and to all of Palladium's artists. And to Wayne, Alex and the rest of the Palladium super-heroes for all their hard work and acts of heroism every day. Apologies to any contributor whose name was misspelled or left out by accident.\n\n— Kevin Siembieda, 2003",5,3,reason)
    replace_paragraph(name,'Damage/Penalties: People coated in oil',"Damage/Penalties: People coated in oil will find it difficult to pickup, hold or carry anything and there is a 01-33% chance of them dropping anything in their hands at the beginning of each melee round or when using an object to strike in an attack. Additionally, moving faster than one third his normal maximum speed is likely (01-60% chance) to cause the affected character to slip and fall, losing initiative and one melee attack/action.",13,11,reason)
    # These prose paragraphs and every numerical label were checked in the page image.
    criminal=section(stem,21,'Criminal Intuition\n','Danger Sense',
        [('By Carmen Bellaire & Kevin Siembieda','By Carmen Bellaire & Kevin Siembieda\n'),('Iow level','low level'),('teds notice',"ter's notice"),('men this happens','When this happens'),('crirne','crime'),('followed!tailed','followed/tailed')],
        ['This character','Likewise,','This amazing','In addition,','Note:','Range:','Duration:','Skill Bonuses:','Limitations:'])
    replace_region(name,'## Criminal Intuition','## Danger Sense','## Criminal Intuition\n\n'+criminal,21,19,reason)
    # A fragment from Criminal Intuition was erroneously placed in the preceding column.
    replace_paragraph(name,'character like a neon sign, as do undercover cops','',21,19,'Removed misplaced duplicate continuation now restored under Criminal Intuition')
    powers=section(stem,28,'Exploding Spheres\n','Fabric/CIoth Material Animation',
        [('Inspired by Nick Luna','Inspired by Nick Luna\n'),('Speed of IO','Speed of 10'),('to IO feet','to 10 feet'),('ID6 points','1D6 points'),('attackjaction','attack/action'),('creators will',"creator's will")],
        ['The character','Range:','Damage:','Area Effect','Duration/Timing:','Number of Spheres','Delivery System:'])
    fabric=section(stem,28,'Fabric/CIoth Material Animation\n','26',
        [('Fabric/CIoth','Fabric/Cloth'),('attacWaction','attack/action'),('Snare/EntangIe Legs','Snare/Entangle Legs'),('2.\nneckties','neckties'),('ID4 damage','1D4 damage')],
        ['Range:','Duration:','Damage:','Attacks Per Melee:','Bonus:','Fabric/Material Animation:','1. Blinding','Snare/Entangle','3. Entangle','4. Tie-Up'])
    fabric=fabric.replace('Snare/Entangle Legs.','2. Snare/Entangle Legs.')
    fabric+=' '+section(stem,29,'','Feral', [('ID4 damage','1D4 damage')],['5. Whip'])
    replace_region(name,'## Exploding Spheres','## Feral','## Exploding Spheres\n\n'+powers+'\n\n## Fabric/Cloth Material Animation\n\n'+fabric,28,26,reason)
    flight=section(stem,29,'Flight: Hover\n','Flight: Insect',[],['Bonuses In Flight:','Speed:','+10','+2 to dodge','+2 to damage','+15'])
    replace_region(name,'## Flight: Hover','## Flight: Insect','## Flight: Hover\n\n'+flight,29,27,reason)
    disc=section(stem,30,'Flying Force Disc\n','Frequency Absorption',
        [('fiat force','flat force'),('Speed.','Speed:'),('Weiqht','Weight'),('Attitude','Altitude'),('too,at','too, at'),('creators',"creator's"),('ID6+I','1D6+1'),('9, II,','9, 11,'),('Range.','Range:'),('characters usual',"character's usual")],
        ['Range:','Size:','Flight Capabilities:','Weapon Capabilities','Attacks per Melee:'])
    replace_region(name,'## Force Disc','## Frequency Absorption','## Flying Force Disc\n\n'+disc,30,28,reason)
    guns=section(stem,31,'Glow Bug\n','Hardened Skin',
        [('induced tight','induced light'),('characters attacks',"character's attacks"),('fiat surface','flat surface'),('an area IO','an area 10'),('reaches cut IO','reaches out 10'),('Duration: IO','Duration: 10'),('attack oer','attack per'),('rifie','rifle'),('ID6xIO','1D6×10'),('wild]','wild.'),('Gravitational Plane','\n## Gravitational Plane\n'),('Gun Limb','\n## Gun Limb\n')],
        ['The bizarre','Creating a gravity','Range:','Area of Effect:','Height Limit:','Damage:','Duration:','Attacks per Melee:','The character','Rifle Caliber Rounds:','Payload:','Bonuses:'])
    replace_region(name,'## Glow Bug','## Hardened Skin','## Glow Bug\n\n'+guns,31,29,reason)
    quills=section(stem,39,'Quills & Spines\n','Resin',
        [('qvjJJs may Jook Jjke','quills may look like'),('-and-back','and back.'),('any-one','anyone'),('leap!pounce','leap/pounce'),('ID6','1D6'),('levet','level'),('Launch Quill*','Launch Quills:'),('tike a gun','like a gun'),('(aunched','launched'),('106+10','1D6+10')],
        ['Number of Quills:','As a defensive','Natural A.R.:','S.D.C.:','As a weapon,','1. Daggers','2. Claws','3. Launch'])
    replace_region(name,'## Quills &amp; Spines','## Resin','## Quills & Spines\n\n'+quills,39,37,reason)
    replace_paragraph(name,'The character has the ability to ride on the waves',"The character has the ability to ride on the waves that he generates, much like a surfer, but without the aid of a surfboard. At level four, the hero can generate waves out of snow as well. Unlike a real wave, the Wave Rider can change the speed and direction of his wave and even go backwards and counter to the real waves around him.",52,50,reason)
    name='Heroes Unlimited - Powers Unlimited 2.md'
    replace_paragraph(name,'Applications: 1)Attract the opposite sex',"Applications: 1) Attract the opposite sex: Emits strong pheromones that make the character more attractive to the opposite sex (effectively raises M.A. and P.B. +10 when dealing with the opposite sex and provides a +10% bonus to the Seduction skill). Can be released for two hours per day and has a range of 100 feet (30.5 m) per point of the character's normal M.A.",21,20,reason)
    text=section('Heroes Unlimited - Powers Unlimited 2',81,'76-80% Immune System Enhancement:','81-85% Bionic Sensor System:')
    replace_paragraph(name,'76-80% Immune System Enhancement:','76-80% Immune System Enhancement: '+text,81,80,reason)
    name='Rifts - World Book 07 - Underseas.md'
    replace_paragraph(name,'Pay s o  e e  d   t : pe.','Payload: 240 total: 60 per launch tube, any combination or single type.',206,207,reason)
    text=section('Rifts - World Book 07 - Underseas',206,'6. Depth Charge Launchers (2):','The NGR Poseidon',
        [('Mega-Damage: M.D.','Mega-Damage: 2D4×10 M.D.'),('32 krn','32 km'),('2D6x10','2D6×10'),('Of speed)','of speed)'),('l. Enhanced','1. Enhanced'),('Lon- Range','Long-Range'),('terns','tems')],
        ['Primary Purpose:','Secondary Purpose:','Mega-Damage:','Rate of Fire:','Effective Range:','Payload:','7. Ram Prow:','8. Sensor Systems','1. Enhanced','2. Sonar:','3. Sonic','4. Long-Range','5. Independent','6. Life support','7. As well'])
    replace_region(name,'6. Depth Charge Launchers (2): This explosive device is used against vessels and monsters somewhere below the ship.','## The NGR Poseidon','6. Depth Charge Launchers (2): '+text,206,207,reason)
    save_repairs(ROOT/'reports/ocr-review/source-repairs-16.json')


if __name__=='__main__':main()
