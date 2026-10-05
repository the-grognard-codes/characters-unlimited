"""Recover RUE rule passages and concluding prose from rendered source pages."""
import json
from repair_source_passages import ROOT, replace, save_repairs


def main():
    approved={
        143:{'61)6':'6D6','ID4':'1D4','ID6':'1D6','11)6':'1D6','1.S.P.':'I.S.P.',
             'diffculty':'difficulty','ofa':'of a','Mega- Damage':'Mega-Damage'},
        181:{'IO feet':'10 feet','ID6':'1D6','11)6':'1D6','21)6':'2D6','1.S.P.':'I.S.P.'},
        201:{"experience, Because":"experience. Because"},
        263:{},
        378:{'This is. in':'This is, in','created libr':'created for','Rifts@':'Rifts',
             'wonder- 375 till':'wonderful','bet-ore':'before','eard game':'card game'},
    }
    proposals=json.loads((ROOT/'reports/ocr-review/paragraph-candidates.json').read_text(encoding='utf-8'))
    count=0
    for rec in proposals:
        if rec['file']!='Rifts - Ultimate Edition.md' or len(rec['matches'])!=1:continue
        m=rec['matches'][0];page=m['pdf_page']
        if page not in approved:continue
        after=m['after']
        for before,new in approved[page].items():
            assert before in after,(page,before)
            after=after.replace(before,new)
        replace(rec['file'],rec['before'],after,page,page-3,
                "Recovered missing text and numerical rules; visually checked the full rendered source page and corrected independent-OCR glyph errors. Printed Electrokinesis 10 feet (0.3 m) inconsistency retained. Final Thoughts: removed the OCR-inserted page number and restored the omitted artwork count.")
        count+=1
    assert count==5
    save_repairs(ROOT/'reports/ocr-review/source-repairs-13.json')


if __name__=='__main__':main()
