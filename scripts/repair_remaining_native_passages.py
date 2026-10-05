"""Restore additional damaged HU2 paragraphs and lost numerical values."""
import json
from repair_source_passages import ROOT, replace, save_repairs


def clean(text):
    for old,new in {'1 20':'120','31 5':'315','1 5-20':'15-20','1 0.':'10.',
                    '406 points':'4D6 points','206 points':'2D6 points','1 04 minutes':'1D4 minutes',
                    'Ibs':'lbs','any\u00ad thing':'anything','A.A. and application':'A.R. and application',
                    'modem weapons':'modern weapons'}.items():text=text.replace(old,new)
    return text


def main():
    continued=json.loads((ROOT/'reports/ocr-review/continued-native-candidates.json').read_text(encoding='utf-8'))
    assert len(continued)==6
    for rec in continued:
        replace(rec['file'],rec['before'],clean(rec['after']),rec['pdf_pages'],None,
                "Recovered the complete source paragraph in column order, including a damaged beginning; manually reviewed prose. Whirlwind and Jumping Spider numerical values verified in rendered PDF blocks.")
    partial=json.loads((ROOT/'reports/ocr-review/native-recovery-candidates.json').read_text(encoding='utf-8'))
    overrides={
        88:'01-40 Engine chokes, stalled out and descending. Must restart the vehicle. Pilot skill roll at -25%; try once per melee. Altitude is lost at a rate of 500 feet (150 m) per melee (an Emergency Landing may be necessary). All attacks are defensive only and at -4 to strike.',
        195:'This type of robot tends to be less expensive because it requires a human operator or pilot and not a costly artificial intelligence. The machine can be any of the body styles, vehicular, humanoid or animal, but must be large enough to accommodate a pilot. This means the robot must always be large and bulky, at least the size of a mid-sized automobile.',
    }
    for rec in partial:
        n=rec['pdf_page']
        if n not in [88,114,195,240,289,292]:continue
        after=clean(overrides.get(n,rec['after']))
        replace(rec['file'],rec['before'],after,n,None,
                "Restored paragraph from visually checked PDF block, including all numerical values. Rejoined the continuation for the robot-vehicle description and failed-piloting entry; corrected native extraction glyphs.")
    save_repairs(ROOT/'reports/ocr-review/source-repairs-11.json')


if __name__=='__main__':main()
