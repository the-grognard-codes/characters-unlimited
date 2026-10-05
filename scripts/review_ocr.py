"""Apply reviewed OCR corrections and write an auditable corpus integrity report.

No statistical spelling correction, rule extrapolation, or table-value inference.
Run without --apply to audit; --apply records each changed line before writing.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "sources-markdown"
REPORT_DIR = ROOT / "reports" / "ocr-review"

# Explicit, reviewed nonwords. Do not include valid words such as Allen, bail,
# docs, fiat, hack, roil, wail, or names that only resemble common vocabulary.
# Case is preserved. These substitutions do not change rule values.
WORD_CORRECTIONS = dict(
    pair.split(":", 1)
    for pair in """
    abie:able abllities:abilities acrobaties:acrobatics actuai:actual
    actuaily:actually additionai:additional ahilities:abilities ahility:ability
    ailow:allow ailows:allows aimost:almost aiong:along airbome:airborne
    aiready:already aireraft:aircraft aiso:also aiter:alter aiternative:alternative
    aititude:altitude aithough:although aiways:always altemative:alternative
    animai:animal animais:animals applicabie:applicable attaeks:attacks
    automaticaily:automatically autornatic:automatic availabie:available
    availablc:available baiance:balance basicaliy:basically basicaily:basically
    basie:basic battie:battle biack:black biade:blade biast:blast biasts:blasts
    bieeding:bleeding biock:block biocks:blocks biood:blood bionies:bionics
    biow:blow boit:bolt boits:bolts builets:bullets buliet:bullet buliets:bullets
    buming:burning cach:each cail:call cailed:called carlier:earlier
    casy:easy causcd:caused chanee:chance characteristies:characteristics
    charaeter:character charaeters:characters chernistry:chemistry
    cight:eight ciass:class ciassic:classic ciothes:clothes circie:circle
    cirele:circle cither:either cnough:enough coid:cold coior:color coiors:colors
    comhat:combat compiete:complete compietely:completely compiex:complex
    conccaled:concealed conccalment:concealment conceaiment:concealment
    conduet:conduct confliet:conflict consequentiy:consequently
    considcred:considered controi:control controlied:controlled
    conventionai:conventional converslon:conversion couid:could coupie:couple
    covcred:covered cqual:equal cquipment:equipment cquivalent:equivalent
    crcatures:creatures criminai:criminal cybemetic:cybernetic cyes:eyes
    darnage:damage degrces:degrees demonie:demonic deseribed:described
    deseriptions:descriptions destruetion:destruction deveiopment:development
    difficuit:difficult dimenslon:dimension directiy:directly discase:disease
    diseover:discover doilars:dollars doiphins:dolphins doliars:dollars
    doubie:double doubied:doubled eannot:cannot eargo:cargo
    ectopiasmic:ectoplasmic effeet:effect effeetive:effective
    eiectronic:electronic eise:else eities:cities eity:city electricai:electrical
    electronies:electronics elementai:elemental elients:clients enabie:enable
    enabies:enables engincer:engineer equaily:equally ereate:create
    ereating:creating ereature:creature eredits:credits especiaily:especially
    exampie:example excelient:excellent exeept:except experiencc:experience
    experimentai:experimental expiosion:explosion expiosive:explosive
    expiosives:explosives expuision:expulsion extemal:external
    eybernetics:cybernetics eyborgs:cyborgs facrie:faerie facries:faeries
    faii:fail feclings:feelings feeis:feels fiames:flames fiee:flee
    fieid:field fiexible:flexible filied:filled fioating:floating fiow:flow
    firc:fire firlng:firing foik:folk foliow:follow foliowing:following
    friendiy:friendly frorn:from fuil:full fuli:full funetions:functions
    galion:gallon generai:general generaily:generally govemment:government
    govemments:governments govermments:governments greatcr:greater
    gymnasties:gymnastics haif:half hamess:harness handfui:handful
    hcaling:healing heais:heals heid:held heimet:helmet heip:help
    heipful:helpful heipless:helpless heips:helps heroie:heroic himseif:himself
    hirnself:himself hoid:hold hoiding:holding hoids:holds homeworid:homeworld
    homs:horns honuses:bonuses horribie:horrible horsc:horse
    hovereraft:hovercraft ianguage:language iarger:larger
    iater:later ievel:level iliegal:illegal imagcr:imager
    immortais:immortals impaet:impact impiants:implants impossibie:impossible
    inciude:include inciudes:includes incredibie:incredible
    individuais:individuals ineludes:includes ineoming:incoming
    inereasing:increasing ineredible:incredible ineredibly:incredibly
    infliet:inflict infliets:inflicts inhurnan:inhuman instantiy:instantly
    inteiligent:intelligent intemal:internal internai:internal invisibie:invisible
    invoive:involve invoives:involves invuinerability:invulnerability
    invulnerabie:invulnerable iong:long iooking:looking iost:lost itern:item
    itseif:itself kili:kill knoeked:knocked knowiedge:knowledge leam:learn
    leaming:learning levei:level leveis:levels litcracy:literacy
    littie:little lmpervious:impervious ltems:items magicai:magical
    magie:magic mancuvers:maneuvers mcchanical:mechanical mclee:melee
    mechanies:mechanics megavcrse:megaverse meiee:melee meiees:melees
    meit:melt melce:melee mentaily:mentally mereenary:mercenary metai:metal
    metais:metals mierowave:microwave missiies:missiles motorcyele:motorcycle
    muitiple:multiple multipie:multiple muscie:muscle muscuiar:muscular
    mystie:mystic mysties:mystics naturai:natural nobie:noble norrnal:normal
    normai:normal northem:northern nuciear:nuclear nuelear:nuclear
    objeet:object objeets:objects occan:ocean oneseif:oneself oniy:only
    onty:only opcrations:operations optie:optic optionai:optional
    pailadium:palladium paliadium:palladium partiaily:partially
    particuiar:particular pattem:pattern pattems:patterns penaities:penalties
    penaity:penalty penaltics:penalties peopie:people physicai:physical
    physicaliy:physically piace:place piaced:placed piane:plane pianet:planet
    piants:plants piasma:plasma piastic:plastic piate:plate piayed:played
    piayer:player piayers:players piaying:playing piease:please pieasure:pleasure
    planct:planet plastie:plastic polnts:points possibie:possible
    possibiiities:possibilities powerfui:powerful principied:principled
    probabiy:probably probiem:problem probiems:problems prowi:prowl
    psionie:psionic psionies:psionics psychie:psychic rareiy:rarely reai:real
    reasonabie:reasonable recognizc:recognize regardiess:regardless
    relcase:release republies:republics resembie:resemble resembies:resembles
    restrieted:restricted resuit:result resuiting:resulting resuits:results
    retractabie:retractable retum:return retumed:returned rifie:rifle
    rifies:rifles rituai:ritual rnakes:makes roie:role roli:roll rolis:rolls
    ruthiess:ruthless sarne:same schoiars:scholars scrambier:scrambler
    screcn:screen seeret:secret seidom:seldom seiection:selection
    seience:science seientific:scientific seif:self seils:sells
    sensc:sense seores:scores serambler:scrambler serupulous:scrupulous
    shieid:shield shouid:should shouider:shoulder shouiders:shoulders
    simpie:simple simpiy:simply simuitaneous:simultaneous
    simuitaneously:simultaneously simultancous:simultaneous
    simultancously:simultaneously singie:single sirnply:simply slowiy:slowly
    smail:small smali:small smalier:smaller soldler:soldier somchow:somehow
    sourccbook:sourcebook sourccbooks:sourcebooks
    soureebooks:sourcebooks spaee:space spcaking:speaking speciai:special
    specifie:specific speil:spell speli:spell spelis:spells statisties:statistics
    steei:steel stili:still strectwise:streetwise struek:struck styie:style
    styies:styles subjeet:subject suitabie:suitable supematural:supernatural
    supersoidier:supersoldier systerns:systems tabie:table tabies:tables
    targcting:targeting technoiogy:technology tentacies:tentacles thcir:their
    themseives:themselves thern:them thrce:three toois:tools troubie:trouble
    tumed:turned tums:turns typicai:typical typicaily:typically
    unabie:unable uniess:unless uniimited:unlimited unnaturai:unnatural
    untii:until usuaily:usually vehicie:vehicle vehicies:vehicles
    vehiele:vehicle vehieles:vehicles viliains:villains vioient:violent
    virtuaily:virtually virtualiy:virtually visibie:visible visuai:visual
    vollcy:volley vuinerable:vulnerable vulnerabie:vulnerable waik:walk
    walis:walls wcighs:weighs wcight:weight wieider:wielder wildemess:wilderness
    wili:will worid:world worids:worlds woridwide:worldwide wouid:would ycars:years
    """.split()
)
WORD_RE = re.compile(r"\b(?:" + "|".join(WORD_CORRECTIONS) + r")\b", re.I)
DICE_RE = re.compile(r"\b[Il]D(?:4|6|8|10|12|20|100)\b")

# Exact phrases checked in context; avoids damaging valid names and vocabulary.
PHRASES = {
    "KevinSiembieda": "Kevin Siembieda",
    "Snowballs &amp; Ice Daggers: Huried projectiles.":
        "Snowballs &amp; Ice Daggers: Hurled projectiles.",
    "Mind Maee  Old Ones": "Mind Mage  Old Ones",
    "Kevin Siem bieda": "Kevin Siembieda",
    "by Parick Nowak": "by Patrick Nowak",
    "Mextco. The Vampire Kingdoms": "Mexico. The Vampire Kingdoms",
    "- Tatoo magic, True Atlanteans": "- Tattoo magic, True Atlanteans",
    "may still be reeruited by the CS": "may still be recruited by the CS",
    "Physical Prowess (P.S.): Shows": "Physical Prowess (P.P.): Shows",
    "Intelligence Quotient (l.Q.):": "Intelligence Quotient (I.Q.):",
    "Free Quebee": "Free Quebec",
    "Emperor Prosck": "Emperor Prosek",
    "need to roil a 16": "need to roll a 16",
    "needs to roil for": "needs to roll for",
    "Neurosis: Roil on": "Neurosis: Roll on",
    "A successful roil means": "A successful roll means",
    "A failed roil means": "A failed roll means",
    "the prowl roil is": "the prowl roll is",
    "(any roil above": "(any roll above",
    "No initiative roil for": "No initiative roll for",
    "player roils the usual": "player rolls the usual",
    "Roils above the A.R.": "Rolls above the A.R.",
    "on all combat roils": "on all combat rolls",
    "can roil to save": "can roll to save",
    "player must roil": "player must roll",
    "No Weapon Proficiency (W.P.). Anybody who docs not":
        "No Weapon Proficiency (W.P.). Anybody who does not",
    "third degree bums on the skin": "third degree burns on the skin",
    "along any fiat surface": "along any flat surface",
    "smooth skin, fiat nose": "smooth skin, flat nose",
    "large fiat nose": "large flat nose",
    "wood. plaster, and glass wails": "wood. plaster, and glass walls",
    "crawling along wails and ceilings": "crawling along walls and ceilings",
    "cannot walk through wails": "cannot walk through walls",
    "person falis, he loses": "person falls, he loses",
    "Falis under that height": "Falls under that height",
    "appears as the ideal maie or female": "appears as the ideal male or female",
    "and tells other maies to stay": "and tells other males to stay",
    "and meid together in ways": "and meld together in ways",
    "Pius these weapons": "Plus these weapons",
    "pius (special) supernatural": "plus (special) supernatural",
    "Steel/lron/Titanium": "Steel/Iron/Titanium",
    "to disarm and puil punches": "to disarm and pull punches",
    "to puil punch": "to pull punch",
    "to puli punch": "to pull punch",
    "puli himself": "pull himself",
    "as weli as debilitating": "as well as debilitating",
    "real world as weil!": "real world as well!",
    "immediate arca (600 feet": "immediate area (600 feet",
    "sensing arca is a 200 foot": "sensing area is a 200 foot",
    "attack/retreat arca": "attack/retreat area",
    "energy trails in the carth": "energy trails in the earth",
    "fly as the cagle spell": "fly as the eagle spell",
    "a failed roll mcans": "a failed roll means",
    "Piloting skill number mcans": "Piloting skill number means",
    "dirty\" moncy": "dirty\" money",
    "(caten alive, after": "(eaten alive, after",
    "mind and foree or induce": "mind and force or induce",
    "(1.5 to 1.8m) tali and": "(1.5 to 1.8m) tall and",
    "(2.7-3.6 m) tali.": "(2.7-3.6 m) tall.",
    "dise camera (moving pictures) with a dozen dises":
        "disc camera (moving pictures) with a dozen discs",
}


def match_case(before: str, after: str) -> str:
    if before.isupper():
        return after.upper()
    if before[0].isupper():
        return after.capitalize()
    return after


def corrected_line(line: str) -> str:
    line = WORD_RE.sub(
        lambda m: match_case(m.group(), WORD_CORRECTIONS[m.group().lower()]), line
    )
    line = DICE_RE.sub(lambda m: "1" + m.group()[1:], line)
    for before, after in PHRASES.items():
        line = line.replace(before, after)
    return line


def cells(line: str) -> list[str]:
    return [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def is_separator(line: str) -> bool:
    return bool(line.startswith("|")) and all(
        re.fullmatch(r":?-{3,}:?", c) for c in cells(line)
    )


def audit(name: str, text: str) -> dict:
    lines = text.splitlines()
    findings = []
    section = "Front matter"
    fence = None
    fences = []
    for i, line in enumerate(lines, 1):
        heading = re.match(r"^(#{1,6})\s+(.+)", line)
        if heading:
            section = heading.group(2)
        fm = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if fm:
            if fence is None:
                fence = (fm.group(1), i)
                fences.append(i)
            elif fm.group(1)[0] == fence[0][0] and len(fm.group(1)) >= len(fence[0]):
                fence = None
        reasons = []
        if re.search(r"[\u3400-\u9fff\uf900-\ufaff]", line):
            reasons.append("unexpected CJK character in English OCR")
        known_initialisms = ["IQ", "ME", "MA", "PS", "PP", "PE", "PB", "MDC", "SDC", "PPE", "ISP", "MD", "RCC", "OCC", "ARCHIE", "SCRETS", "SHOCK", "AWA ES".replace(" ", ""), "SCUBA"]
        abbreviation_pattern = r"\b(?:" + "|".join(r"\.".join(word) for word in known_initialisms) + r")\.?(?![A-Za-z])"
        prose = re.sub(abbreviation_pattern, "ATTRIBUTE", line, flags=re.I)
        if re.search(r"(?:\b[A-Za-z]\b[ .,:'\"]{0,8}){6}", prose):
            reasons.append("run of isolated letters; possible lost words")
        tokens = re.findall(r"\b[A-Za-z]+\b", prose)
        if len(tokens) >= 20 and sum(len(w) <= 2 for w in tokens) / len(tokens) > 0.5:
            reasons.append("many word fragments; possible OCR corruption")
        if re.fullmatch(r"#{1,6}\s*", line):
            reasons.append("empty heading")
        if heading and (len(heading.group(2)) <= 2 or heading.group(2) in {"TM", "&amp;"}):
            reasons.append("heading may be artwork or a broken heading")
        if reasons:
            findings.append(dict(line=i, section=section, reasons=reasons, text=line))
    if fence:
        findings.append(dict(line=fence[1], section="Markdown structure",
                             reasons=["unclosed fenced block"], text=lines[fence[1] - 1]))

    tables = []
    i = 0
    while i < len(lines):
        if not lines[i].startswith("|"):
            i += 1
            continue
        start = i
        while i < len(lines) and lines[i].startswith("|"):
            i += 1
        rows = lines[start:i]
        counts = [len(cells(row)) for row in rows]
        reasons = []
        if len(rows) < 2 or not is_separator(rows[1]):
            reasons.append("missing or invalid header separator")
        if len(set(counts)) > 1:
            reasons.append("inconsistent table column count")
        if len(rows) == 2:
            reasons.append("header-only table; body may be absent or merged into header")
        data = [cells(row) for row in rows if not is_separator(row)]
        if len(set(counts)) == 1:
            duplicated_columns = [
                (a + 1, b + 1)
                for a in range(counts[0]) for b in range(a + 1, counts[0])
                if any(row[a] for row in data)
                and all(row[a] == row[b] for row in data)
            ]
            if duplicated_columns:
                reasons.append("identical columns: " + repr(duplicated_columns))
        if any(len(c) > 450 for row in data for c in row):
            reasons.append("long cell; possible merged text/rows")
        repeated_cells = [
            start + j + 1 for j, row in enumerate(rows)
            if not is_separator(row) and len(cells(row)) >= 3
            and len(set(cells(row))) == 1 and any(cells(row))
        ]
        if repeated_cells:
            reasons.append("same text in every cell at lines " + repr(repeated_cells))
        if reasons:
            tables.append(dict(line=start + 1, end_line=i, reasons=reasons,
                               header=rows[0]))

    # Adjacent percentile entries: candidates only. A heading, table, prose
    # block, or image ends the sequence; 00 means 100. These are never repaired
    # by extending a preceding range or guessing the next boundary.
    ranges = []
    previous = None
    for i, line in enumerate(lines, 1):
        if not line.strip():
            continue
        match = re.match(r"^(?:-\s+)?(\d{1,2})\s*[-\u2013\u2014]\s*(\d{1,2})(?:\s|[.:])", line)
        if not match:
            previous = None
            continue
        lo = int(match[1]) or 100
        hi = int(match[2]) or 100
        if lo > hi:
            ranges.append(dict(line=i, reason="reversed percentile range", text=line))
        if previous and lo != previous[2] + 1 and lo != 1:
            ranges.append(dict(line=i, previous_line=previous[0],
                               reason="noncontiguous adjacent percentile entries", text=line))
        previous = (i, lo, hi)

    broken_words = [
        dict(line=text[:m.start()].count("\n") + 1, fragments=m.group())
        for m in re.finditer(r"\b[A-Za-z]{2,}-\n\s*\n[A-Za-z]{2,}\b", text)
    ]
    return dict(file=name, sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                line_count=len(lines), headings=sum(bool(re.match(r"^#{1,6} ", l)) for l in lines),
                images=text.count("<!-- image -->"), fenced_blocks=len(fences),
                text_findings=findings, table_findings=tables,
                percentile_candidates=ranges, split_word_candidates=broken_words,
                completeness="Not certified complete; consult README.md and source-coverage.json. Image placeholders contain no image data.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    paths = sorted(SOURCE_DIR.glob("*.md"))
    if not paths:
        raise SystemExit("No source Markdown files found")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    log_path = REPORT_DIR / ("corrections.json" if args.apply else "proposed-corrections.json")
    if args.apply and log_path.exists():
        raise SystemExit("Applied corrections log already exists; use audit mode for subsequent reviews")
    corrections = []
    corpus = []
    changes_to_write = []
    for path in paths:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        newline = "\r\n" if b"\r\n" in raw else "\n"
        before_lines = text.splitlines(keepends=True)
        after_lines = [corrected_line(line) for line in before_lines]
        records = [dict(line=i, before=old.rstrip("\r\n"), after=new.rstrip("\r\n"))
                   for i, (old, new) in enumerate(zip(before_lines, after_lines), 1) if old != new]
        # A filename-derived H1 makes the document identifiable to ingestion.
        # Existing heading levels and page order are preserved, rather than
        # inferring an unsupported book hierarchy from OCR font detection.
        prefix = "" if re.search(r"^# \S", text, re.M) else f"# {path.stem}{newline}{newline}"
        new_text = prefix + "".join(after_lines)
        # Preserve every original digit, in order, apart from explicitly logged
        # dice corrections. Numeric chart repairs belong in a separate reviewed
        # patch with their primary-source evidence.
        normalized_old = DICE_RE.sub(lambda m: "1" + m.group()[1:], text)
        assert re.findall(r"\d+", normalized_old) == re.findall(r"\d+", new_text[len(prefix):]), path
        assert len(before_lines) == len(after_lines), path
        # The log can reproduce the original exactly, including newline style.
        restored = after_lines.copy()
        for rec in records:
            idx = rec["line"] - 1
            restored[idx] = before_lines[idx]
        assert "".join(restored).encode("utf-8") == raw
        corrections.append(dict(file=path.name, original_sha256=hashlib.sha256(raw).hexdigest(),
                                corrected_sha256=hashlib.sha256(new_text.encode("utf-8")).hexdigest(),
                                added_title=prefix.rstrip("\r\n"),
                                line_numbers="before title insertion", changes=records))
        corpus.append(audit(path.name, new_text))
        if new_text != text:
            changes_to_write.append((path, raw, new_text.encode("utf-8")))
    # Verify that none of the inputs changed during preparation.
    assert all(path.read_bytes() == raw for path, raw, _ in changes_to_write)
    if args.apply:
        for path, raw, corrected in changes_to_write:
            assert path.read_bytes() == raw, path
            path.write_bytes(corrected)
            assert path.read_bytes() == corrected, path
    result = dict(status="applied" if args.apply else "audited", files=corpus)
    (REPORT_DIR / "audit.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # Keep a previous applied correction log when re-running the audit.
    log_path.write_text(json.dumps(corrections, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for record, review in zip(corrections, corpus):
        print(f"{record['file']}: {len(record['changes'])} changed lines; "
              f"{len(review['text_findings'])} text flags, {len(review['table_findings'])} table flags, "
              f"{len(review['percentile_candidates'])} percentile candidates")
    print("Applied" if args.apply else "Proposed", "changes to", len(changes_to_write), "files")


if __name__ == "__main__":
    main()
