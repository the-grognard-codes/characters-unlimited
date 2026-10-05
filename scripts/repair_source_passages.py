"""Restore passages checked visually against supplied PDF pages.

Each patch records its full before/after text and its PDF/printed page locator.
The local PDF, rather than a similar passage in another edition, is the source.
"""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/ocr-review/source-repairs.json"
records = []
documents = {}
originals = {}


def load(name):
    if name not in documents:
        path = ROOT / "sources-markdown" / name
        originals[name] = path.read_bytes()
        documents[name] = [path, originals[name].decode("utf-8")]
    return documents[name][1]


def replace(name, before, after, pdf_page, printed_page, reason):
    text = load(name)
    if before not in text and "\r\n" in text and "\r\n" not in before:
        before = before.replace("\n", "\r\n")
    if "\r\n" in before and "\r\n" not in after:
        after = after.replace("\n", "\r\n")
    if text.count(before) != 1:
        raise ValueError(f"Expected one patch target in {name}: {before[:100]!r}")
    records.append(dict(file=name, line_before_patch=text[:text.index(before)].count("\n") + 1,
                        pdf_page=pdf_page, printed_page=printed_page, reason=reason,
                        before=before, after=after))
    documents[name][1] = text.replace(before, after, 1)


def replace_paragraph(name, start, after, pdf_page, printed_page, reason):
    paragraphs = re.split(r"\r?\n\r?\n", load(name))
    targets = [p for p in paragraphs if p.startswith(start)]
    if len(targets) != 1:
        raise ValueError((name, start, len(targets)))
    replace(name, targets[0], after, pdf_page, printed_page, reason)


def replace_region(name, start, end, after, pdf_page, printed_page, reason):
    text = load(name)
    assert text.count(start) == 1 and text.count(end) == 1, (name, start, end)
    a = text.index(start)
    b = text.index(end, a)
    replace(name, text[a:b], after.rstrip() + "\n\n", pdf_page, printed_page, reason)


def save_repairs(report=REPORT):
    if report.exists():
        raise ValueError("Refusing to overwrite an applied repair log")
    output = []
    for name, (path, text) in documents.items():
        assert path.read_bytes() == originals[name], "Input changed during review: " + name
        output.append(dict(file=name, before_sha256=hashlib.sha256(originals[name]).hexdigest(),
                           after_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest()))
    report.write_text(json.dumps(dict(files=output, repairs=records), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for name, (path, text) in documents.items():
        path.write_bytes(text.encode("utf-8"))
        assert path.read_bytes() == text.encode("utf-8")
    print(f"Applied {len(records)} logged repairs to {len(documents)} books")


def attribute_chart():
    # All 150 entries were read in both books' rendered charts (HU2 p.15,
    # RUE p.281). The two M.E. and P.P. subrows remain separately labelled.
    repeated = "+1 +1 +2 +2 +3 +3 +4 +4 +5 +5 +6 +6 +7 +7 +8".split()
    rows = [
        ("I.Q. add to all skills (one-time bonus)", [f"+{n}%" for n in range(2, 17)]),
        ("M.E. save vs. psionic attack", repeated),
        ("M.E. save vs. insanity", "+1 +1 +2 +2 +3 +4 +5 +6 +7 +8 +9 +10 +11 +12 +13".split()),
        ("M.A. trust/intimidate", "40% 45% 50% 55% 60% 65% 70% 75% 80% 84% 88% 92% 94% 96% 97%".split()),
        ("P.S. Hand to Hand combat: damage", [f"+{n}" for n in range(1, 16)]),
        ("P.P. parry and dodge bonus", repeated),
        ("P.P. bonus to strike", repeated),
        ("P.E. save vs. coma/death", "+4% +5% +6% +8% +10% +12% +14% +16% +18% +20% +22% +24% +26% +28% +30%".split()),
        ("P.E. save vs. magic/poison", repeated),
        ("P.B. charm/impress", "30% 35% 40% 45% 50% 55% 60% 65% 70% 75% 80% 83% 86% 90% 92%".split()),
    ]
    assert all(len(values) == 15 for _, values in rows)
    return "\n".join([
        "| Attribute / bonus | " + " | ".join(map(str, range(16, 31))) + " |",
        "| " + " | ".join(["---"] * 16) + " |",
        *("| " + label + " | " + " | ".join(values) + " |" for label, values in rows),
    ]) + "\n\nSpd. No special bonuses other than the raw, natural ability to run."


def replace_attribute_chart(name, pdf_page, printed_page):
    matches = [m for m in re.finditer(r"(?m)^\|[^\n]+\n(?:\|[^\n]*\n?)+", load(name))
               if "save vs." in m.group() and "trust/intimidate" in m.group()]
    assert len(matches) == 1
    before = matches[0].group().rstrip("\n")
    replace(name, before, attribute_chart(), pdf_page, printed_page,
            "Restored corrupted/missing chart cells and separated the speed note from numerical data")


def speed_chart():
    # Keep the supplied editions' printed kilometer figures (including 148,
    # 241 and 321), rather than importing a later publisher web chart.
    rows = [
        (5, "3.5", "5.6"), (11, "7.5", "12"), (22, "15", "24"),
        (27, "18.5", "29.7"), (33, "22.5", "36"), (44, "30", "48"),
        (50, "35", "56"), (55, "37.5", "60"), (58, "40", "64"),
        (66, "45", "72"), (77, "53", "85"), (88, "60", "96"),
        (110, "75", "120"), (132, "90", "148"), (220, "150", "241"),
        (293, "200", "321"),
    ]
    return "\n".join(["| Speed Factor | Approx. MPH | Kilometers Per Hour |",
                      "| --- | --- | --- |",
                      *(f"| {a} | {b} | {c} |" for a, b, c in rows)])


def main():
    if REPORT.exists():
        raise SystemExit("Source-repair log already exists; do not overwrite an applied audit trail")
    hu = "Heroes Unlimited - RPG - 2E.md"
    rue = "Rifts - Ultimate Edition.md"
    pu1 = "Heroes Unlimited - Powers Unlimited 1.md"
    replace_attribute_chart(hu, 16, 15)
    replace_attribute_chart(rue, 284, 281)
    for name, pdf_page, printed_page in [(hu, 17, 16), (rue, 284, 281)]:
        matches = [m for m in re.finditer(r"(?m)^\|[^\n]+\n(?:\|[^\n]*\n?)+", load(name))
                   if "Speed Factor" in m.group() and "Approx. MPH" in m.group()]
        assert len(matches) == 1
        replace(name, matches[0].group().rstrip("\n"), speed_chart(), pdf_page, printed_page,
                "Restored mixed fractions as unambiguous decimal MPH values; retained printed kilometer values")

    replace_paragraph(pu1, "The fantasy world of Heroes Unlimited", "The fantasy world of Heroes Unlimited™ is violent, deadly and filled with superhumans, aliens, supernatural monsters, and strange powers. Superhuman mutants, aliens, and nefarious villains threaten, rob, torment and prey on humans. Monsters, gods, demons, magic, insanity, drugs, biological experiments, war and heroic adventure are all elements of this book.", 3, 1, "Recovered unreadable warning text")
    replace_paragraph(pu1, "Some parents may find", "Some parents may find the violence, magic, super abilities and supernatural elements of this book inappropriate for young readers/players. We suggest parental discretion.", 3, 1, "Recovered missing warning text")
    replace_paragraph(pu1, "Please  te at none", "Please note that none of us at Palladium Books condone or encourage the occult, the practice of magic, the use of drugs, vigilantism or violence.", 3, 1, "Recovered unreadable warning text")
    replace_paragraph(pu1, "A power packed sourcebook for the Heroes Unlimited RPG®, 2nd Edi n.", "A power packed sourcebook for the Heroes Unlimited RPG®, 2nd Edition. Compatible with After the Bomb® and the entire Palladium Books® Megaverse®!", 3, 1, "Recovered edition and compatibility statement")

    # Recover the sentence split by a misplaced OCR chart heading.
    replace(hu, "\n\n## ATTRIBUTE BONUS CHART\n\nmay offer other bonuses", " may offer other bonuses", 16, 15,
            "Joined the physical-skills paragraph across an incorrectly placed chart heading")
    table = attribute_chart()
    replace(hu, table, "## Attribute Bonus Chart\n\n" + table, 16, 15,
            "Placed chart heading immediately above its table")
    replace(hu, "Being *superhuman,\"", 'Being "superhuman,"', 16, 15,
            "Corrected corrupted quotation marks in the joined paragraph")
    replace_paragraph(hu, "Speed (Spd): Specifically", "Speed (Spd): Specifically, this is the character's maximum running speed. The speed times 20 is the number of yards or meters that the character can run in one minute. Speed times five is the number of yards/meters covered in a melee round (15 seconds). Dividing the distance covered in a melee round by the character's number of attacks indicates how far the character can move on each attack.", 16, 15, "Recovered the missing movement-per-attack calculation")
    replace_paragraph(hu, "Mental Endurance (M.E.), Intelligence Quotient", "Mental Endurance (M.E.), Intelligence Quotient (I.Q.), Mental Affinity (M.A.), and Physical Beauty (P.B.) are normally maxed out at 30 for mortals. Bonuses do not increase should the character have a number higher than thirty; the only exception might be a god and aliens (which are clearly not normal humans). This will be extremely rare, but not impossible. Use your discretion.", 16, 15, "Recovered two missing attribute names in the cap rule")
    pp_rule = "Physical Prowess (P.P.): The bonus to strike, parry and dodge, stops at 30. But for every four P.P. points beyond 30, the character gets a bonus of one on his initiative roll. Thus, add +1 on initiative at P.P. 34, 38, 42, 46, and 50. A physical prowess of 50 is the absolute P.P. limit even if they are superhuman or alien!"
    pe_start = "Physical Endurance (P.E.): The bonus to save vs poison and magic stops at 30"
    paragraphs = load(hu).split("\n\n")
    old_pe = next(p for p in paragraphs if p.startswith(pe_start))
    old_pp = next(p for p in paragraphs if p.startswith("Physical Prowess (P.P.): The bonus to strike"))
    replace(hu, old_pe + "\n\n" + old_pp, pp_rule + "\n\nPhysical Endurance (P.E.): The bonus to save vs poison and magic stops at 30, but the percentage to save vs coma continues at an increment of one point per each additional point beyond 30%. Thus, a P.E. of 31 provides a 31% chance to save vs coma, 32 is 32%, and so on.", 17, 16, "Restored the missing size of the initiative bonus, damaged P.E. continuation, and source paragraph order")

    replace_paragraph(rue, "The following is a simple conversion table of speed factors", "The following is a simple conversion table of speed factors into approximate miles per hour (mph) and kilometer equivalents.", 284, 281, "Recovered the damaged speed-chart introduction")
    replace_paragraph(rue, "Superhuman Men at Arms who have undergone", "Superhuman Men at Arms who have undergone some type of augmentation, like Full Conversion Cyborgs and Headhunters (bionics), Crazies (brain implants), Juicers (chemical augmentation), and Light Power Armor, all possess a level of strength that transcends even exceptional human P.S.; see the Augmented Strength listing. Note: Giant robots, robot vehicles, heavy power armor (Glitter Boy, Ulti-Max and SAMAS), Skelebots and other robots (no human inside) use the Robot Strength listing. Supernatural Strength applies to dragons and all demons, gods, demigods, godlings, and other supernatural beings. Supernatural P.S. may also apply to select O.C.C.s and R.C.C.s. If a character, monster or villain has any type of enhanced strength, it will be noted in the stats.", 284, 281, "Recovered the missing last sentence of the strength classification rule")
    replace_paragraph(rue, "Note: I.S.P. (Inner Strength Points", "Note: I.S.P. (Inner Strength Points for psionic powers) and P.P.E. (Potential Psychic Energy for magic) are important aspects of the character, but they are not attributes per se, and are covered elsewhere. Also see Perception Rolls in the combat section.", 284, 281, "Recovered the distinction between attributes and energy pools")
    replace_paragraph(rue, "A Note About Bonuses:", "A Note About Bonuses: Many skills and abilities provide characters with bonuses to strike, parry, dodge, save, etc. These bonuses are typically added to a particular combat or melee attack/action. Always be sure to include your character's bonuses, since they may make the difference between success and failure, life and death. Note that bonuses from psionics or magic are temporary bonuses, and only apply while that power or spell is in place.", 284, 281, "Recovered missing bonus-application guidance")

    # Prepare all changes before touching any file. The earlier typo-correction
    # log identifies the state on which this second repair pass depends.
    save_repairs()


if __name__ == "__main__":
    main()
