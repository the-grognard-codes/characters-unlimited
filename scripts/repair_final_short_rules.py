"""Recover remaining short rules read in rendered PDF pages."""
import re
from repair_source_passages import ROOT, load, replace, replace_paragraph, replace_region, save_repairs
from repair_contents_tables import PU1_MINOR


def containing(name, needle, after, page, printed, reason):
    targets=[x for x in re.split(r'\r?\n\r?\n',load(name)) if needle in x]
    assert len(targets)==1,(name,needle,len(targets))
    replace(name,targets[0],after,page,printed,reason)


def main():
    name='Heroes Unlimited - RPG - 2E.md'
    reason='Recovered garbled short rule and numerical values from visually verified PDF text block'
    replace_paragraph(name,'- 01-05 Opposite sex:','- 01-05 Opposite sex: If a man, the character will either love to be around women or finds fault in everything they say or do and avoids them.',32,31,reason)
    replace_paragraph(name,'Rate of Fire: One at a time or in volleys of two, three, four, or iges','Rate of Fire: One at a time or in volleys of two, three, four, or eight. Use robot volley rules when multiple spikes are fired simultaneously.',109,108,reason)
    replace_paragraph(name,'Which specific type of animal abilities','Which specific type of animal abilities the character possesses can be selected from or determined by rolling on the following Random Animal Type Table.',252,251,reason)
    replace_paragraph(name,'Damage: Inflicts oneS.D.C.','Damage: Inflicts one S.D.C. point of damage but is startling. The shocked person loses initiative and there is a 1-50% chance the person will drop anything he/she is holding, or release an opponent that is being physically restrained, entangled, pinned or otherwise held.',271,270,reason)
    replace_paragraph(name,'Creating copies in an instant.','Creating copies in an instant. As few as one or as many as all available duplicates can be created in a single melee action (about 2-3 seconds)! Which means an opponent might suddenly find himself facing several opponents where only one had stood moments before.',284,283,reason)
    line=next(x for x in load(name).splitlines() if x.startswith('- P.S. 21 to 25:'))
    replace(name,line,'- P.S. 21 to 25: Inflicts 2D4 S.D.C. on a restrained punch, 3D6 on a full strength punch, and 6D6 with a power punch (counts as two melee attacks).',295,294,reason)
    containing(name,'The loss of memory is temporary,','The loss of memory is temporary, lasting 1D4 days for every 10 I.S.P. expended. The memory can be permanently erased if the psionic exerts 50 I.S.P. at once. A psionic can also permanently wipe a mind completely blank by expending 50 I.S.P. and permanently sacrificing four Mental Endurance (M.E.) points. This is an extremely grueling process for the psychic and the loss of the four M.E. points is permanent, even if the opponent successfully saves against the wipe and is not affected.',314,313,reason)
    name='Rifts - Ultimate Edition.md'
    p=[x for x in re.split(r'\r?\n\r?\n',load(name)) if x.startswith('Ritual/ceremonial magic,')];assert len(p)==1
    after=re.sub(r'Potential Psychic En.*?conducting the ritual\)',"Potential Psychic Energy (basically they aren't present to give their P.P.E. to the mage conducting the ritual)",p[0])
    replace(name,p[0],after,191,188,reason)
    replace(name,'natural biore m je ca ie regenerative','natural bio-regenerative',191,188,reason)
    for prefix in ['ar th al C ce m te pl ha ','hi W ar ev di W st pu to at ','p of a fo to ','p F m tir e ar 一 he as in B ti D b bi er W et d ac ar W ']:
        replace(name,prefix,'',191,188,'Removed column-interleaving OCR fragments; remaining paragraph verified against scan')
    containing(name,'- 6%  os','- 61-80 Reduce both the range and duration of the spell by 20%.',191,188,reason)
    name='Heroes Unlimited - Powers Unlimited 1.md'
    entries=[line.rsplit('|',1)[0] for line in PU1_MINOR.splitlines()[3:]]
    # The printed alphabetical list swaps these pairs relative to the contents list.
    for a,b in [('Energy Expulsion: Energy Aura','Energy Expulsion: Electromagnetic Pulse'),('Enlarge Body Parts','Enhanced Leaping'),('Power Weapon','Power Bands')]:
        i=entries.index(a);j=entries.index(b);entries[i],entries[j]=entries[j],entries[i]
    replace_region(name,'## Alphabetical List of New Minor Super Abilities','## Abnormal Energy Sense',
        '## Alphabetical List of New Minor Super Abilities\n\n'+'\n'.join('- '+x for x in entries),10,8,
        'Rebuilt three-column alphabetical list; checked every label and column sequence visually')
    save_repairs(ROOT/'reports/ocr-review/source-repairs-18.json')


if __name__=='__main__':main()
