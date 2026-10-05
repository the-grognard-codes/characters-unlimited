"""Locate damaged paragraphs between matching source phrases, for manual review."""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def tokenize(text):
    return [(m.group().casefold(),m.start(),m.end()) for m in re.finditer(r"[A-Za-z0-9]+", html.unescape(text))]


def prepare(text):
    text = re.sub(r"([A-Za-z])-\s*\n\s*([a-z])",r"\1\2",text)
    return re.sub(r"\s+"," ",text).strip()


def main():
    audit = json.loads((ROOT / "reports/ocr-review/audit.json").read_text(encoding="utf-8"))
    records=[]
    for book in audit["files"]:
        name=book["file"]; stem=Path(name).stem
        native=json.loads((ROOT / "tmp/pdfs/text" / (stem+".json")).read_text(encoding="utf-8"))
        scan_path=ROOT / "tmp/pdfs/scans" / stem / "ocr.json"
        scans=json.loads(scan_path.read_text(encoding="utf-8")) if scan_path.exists() else []
        scanned={int(Path(p['image']).stem):p['text'] for p in scans}
        source=[]
        for page in native:
            n=page['pdf_page'];s=prepare(scanned.get(n,page['text']));tokens=tokenize(s);ws=[w for w,_,_ in tokens]
            source.append((n,s,tokens,{tuple(ws[i:i+8]):i for i in range(len(ws)-7)}))
        for finding in book['text_findings']:
            before=finding['text'];ws=[w for w,_,_ in tokenize(before)]
            if len(ws)<25 or not re.search(r"(?:\b[a-z]\b\s+){4}", before):continue
            matches=[]
            for n,s,tokens,index in source:
                a=index.get(tuple(ws[:8]));b=index.get(tuple(ws[-8:]))
                if a is not None and b is not None and a<b and b-a<len(ws)*2:
                    after=s[tokens[a][1]:tokens[b+7][2]]
                    # Include closing punctuation from the original paragraph.
                    after += re.search(r"[^A-Za-z0-9]*$",before).group()
                    matches.append(dict(pdf_page=n,after=after,numbers_unchanged=re.findall(r'\d+',before)==re.findall(r'\d+',after)))
            if matches:records.append(dict(file=name,line=finding['line'],before=before,matches=matches))
    (ROOT / 'reports/ocr-review/paragraph-candidates.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for r in records:print(r['file'],r['line'],[(m['pdf_page'],m['numbers_unchanged']) for m in r['matches']])


if __name__=='__main__':main()
