"""Remove unambiguous English-corpus OCR artifacts without changing rules or values."""
from repair_source_passages import ROOT, load, replace, save_repairs


def main():
    edits={
        'Heroes Unlimited - Powers Unlimited 1.md':[('## TM\n\n','')],
        'Heroes Unlimited - RPG - 2E.md':[('\n三\n','\n'),('\n一\n','\n'),('to recharge 首.','to recharge.')],
        'Rifts - Merc Ops.md':[('## 99\n','99\n'),('- 冰 Destroying','- Destroying')],
        'Rifts - Mercenaries.md':[('\n三π\n','\n'),('\nE乙π\n','\n'),('\n三2π\n','\n'),('n 日 Once they are hired','Once they are hired')],
        'Rifts - Ultimate Edition.md':[('\n日\n','\n')],
        'Rifts - World Book 06 - South America 1.md':[('Advisor I r i d n a','Advisor Iridna')],
        'Rifts - World Book 07 - Underseas.md':[('\n图\n','\n'),('Top Secret -NGR 一 Military Data','Top Secret - NGR — Military Data'),('- 除** Depleting','- ** Depleting'),('## ®\n\n',''),('## R\n\n','')],
    }
    for name,patches in edits.items():
        for before,after in patches:
            assert load(name).count(before)==1,(name,before)
            replace(name,before,after,None,None,
                'Editorial cleanup: isolated non-English artwork OCR or malformed heading; no rule, number, or English prose removed. Advisor Iridna spelling agrees with body references.')
    save_repairs(ROOT/'reports/ocr-review/source-repairs-23.json')


if __name__=='__main__':main()
