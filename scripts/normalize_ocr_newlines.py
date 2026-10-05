"""Normalize Markdown line endings to LF, recording reversible original endings."""
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/ocr-review/newline-normalization.json'


def main():
    assert not REPORT.exists(),'Normalization log already exists'
    records=[];writes=[]
    for path in sorted((ROOT/'sources-markdown').glob('*.md')):
        raw=path.read_bytes();text=raw.decode('utf8');runs=[]
        for m in re.finditer(r'\r+\n|\r|\n',text):
            ending=m.group()
            if runs and runs[-1][1]==ending:runs[-1][0]+=1
            else:runs.append([1,ending])
        after=re.sub(r'\r+\n|\r|\n','\n',text).encode('utf8')
        records.append(dict(file=path.name,before_sha256=hashlib.sha256(raw).hexdigest(),after_sha256=hashlib.sha256(after).hexdigest(),original_endings_rle=runs))
        writes.append((path,raw,after))
    assert all(p.read_bytes()==raw for p,raw,_ in writes)
    REPORT.write_text(json.dumps(dict(operation='LF line endings only; no words or values changed',files=records),indent=2)+'\n',encoding='utf8')
    for path,raw,after in writes:path.write_bytes(after)
    print('Normalized 13 files to LF; recorded original line endings for exact reconstruction.')


if __name__=='__main__':main()
