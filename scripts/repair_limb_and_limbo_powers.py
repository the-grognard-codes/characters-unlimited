"""Restore PU1 damaged limb and dimensional-limbo powers from visual scans."""
from repair_source_passages import ROOT, replace_region, save_repairs
from repair_final_power_passages import section


def main():
    stem='Heroes Unlimited - Powers Unlimited 1';name=stem+'.md'
    labels=['Note:','1. Crystal:','2. Ice:','3. Liquid:','4. Magma:','5. Steel:','6. Oil:','7. Tentacles:','8. Sand:','9. Stone:','10. Wood:',
        'Rock Hard','Light Beam:','Hard Fist','Snowballs','Water Bolt:','Burning Touch:','Fling Lava:','Steel Hard','Steel Blade','Bolt of Liquid','Oil Slick:',
        'Bonuses','Tentacle legs','Sand Blasts:','Stone Mace','Wood Hard','Fire Wood','Range:','Damage:','Damage/Penalties:','Attacks','Bonus:','Duration:']
    first=section(stem,12,'Alter Physical Structure of Limb\n','\n10',[
        ('IDIO','1D10'),('S D.C.','S.D.C.'),('hand!arm','hand/arm'),('feets','feels'),('feetJlegs','feet/legs'),('I. Crystal','1. Crystal'),
        ('206','2D6'),('handlarm','hand/arm'),('ID6','1D6'),('106','1D6'),('8, II,','8, 11,'),('Qama.ge','Damage:'),('or I point','or 1 point'),
        ('ID4','1D4'),('Liquid: Because','3. Liquid: Because'),('3.\nliquid water','liquid water'),('406','4D6'),('Pires','pires'),('fooVO.9','foot/0.9'),
        ('A.R. and 75','A.R. 12 and 75'),('Damaqe','Damage'),('tums','turns'),('Ranqe','Range')],labels)
    last=section(stem,13,'','\n11',[
        ('Damaqe.','Damage:'),('Damage/PenaIties','Damage/Penalties'),('206','2D6'),('204','2D4'),('Men directed','When directed'),
        ('ID4','1D4'),('9.\nAttacks','Attacks'),('Stone: The limb','9. Stone: The limb'),('tum','turn'),('IO. Wood','10. Wood'),('wo wood','two wood')],labels)
    replace_region(name,'## Alter Physical Structure of Limb','## Anatomical Independence',
        '## Alter Physical Structure of Limb\n\n'+first+'\n\n'+last,12,10,
        'Rebuilt all ten limb forms from PDF 12–13; visually verified every rule, value, and action cost. Restored lost A.R. 12 for Magma and moved misordered entry numbers.')
    wardrobe=section(stem,35,'Instant Wardrobe\n','Instant Weapon',[
        ('exam-\npie','exam-\nple'),('I: This','1: This'),('for nights on the\nIn each','for nights on the\ntown.\nIn each'),('men the character','When the character')],
        ['1:','2:','3:','4:','In each','Note:','Range:','Duration:','Limitations:'])
    weapon=section(stem,35,'Instant Weapon\n','Iron Will',[
        ('directiy','directly'),('Likewise,an','Likewise, an'),('plus IO','plus 10')],['Because weapons','Note:','Range:','Duration:','Limitations:'])
    replace_region(name,'## Instant Wardrobe','## Iron Will',
        '## Instant Wardrobe\n\n'+wardrobe+'\n\n## Instant Weapon\n\n'+weapon,35,33,
        'Restored two dimensional-limbo powers from visual scan, including all weight limits, level progression, and exchange restrictions')
    save_repairs(ROOT/'reports/ocr-review/source-repairs-22.json')


if __name__=='__main__':main()
