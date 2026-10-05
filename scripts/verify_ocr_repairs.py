"""Read-only verification: reconstruct all original Markdown bytes from repair logs."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/ocr-review'


def read(name):
    return json.loads((REPORT/name).read_text(encoding='utf8'))


def digest(text):
    return hashlib.sha256(text.encode('utf8')).hexdigest()


def line_offset(text, line):
    offset=0
    for _ in range(line-1):
        offset=text.index('\n',offset)+1
    return offset


def reverse_patch(text, repair):
    before,after=repair['before'],repair['after']
    offset=line_offset(text,repair['line_before_patch'])
    if not after:
        return text[:offset]+before+text[offset:]
    end=text.find('\n',offset)
    if end<0:end=len(text)
    position=text.find(after,offset)
    assert offset<=position<=end, ('Repair target not at recorded line',repair['file'],repair['line_before_patch'])
    return text[:position]+before+text[position+len(after):]


def main():
    current={p.name:p.read_bytes().decode('utf8') for p in (ROOT/'sources-markdown').glob('*.md')}
    final_hashes={name:digest(text) for name,text in current.items()}
    # Later source repairs use LF and are applied after the normalization pass.
    for number in reversed(range(22,24)):
        log=f'source-repairs-{number:02}.json'
        if not (REPORT/log).exists():continue
        data=read(log)
        for f in data['files']:assert digest(current[f['file']])==f['after_sha256']
        for r in reversed(data['repairs']):current[r['file']]=reverse_patch(current[r['file']],r)
        for f in data['files']:assert digest(current[f['file']])==f['before_sha256']
    if (REPORT/'newline-normalization.json').exists():
        for rec in read('newline-normalization.json')['files']:
            text=current[rec['file']];assert digest(text)==rec['after_sha256']
            parts=text.split('\n');endings=[ending for count,ending in rec['original_endings_rle'] for _ in range(count)]
            assert len(parts)==len(endings)+1
            current[rec['file']]=''.join(part+ending for part,ending in zip(parts,endings))+parts[-1]
            assert digest(current[rec['file']])==rec['before_sha256']
    sequence=['source-repairs.json']+[f'source-repairs-{i:02}.json' for i in range(2,6)]
    sequence+=['duplicate-repairs.json','source-repairs-06.json','source-repairs-07.json','percentile-order-repairs.json']
    sequence+=[f'source-repairs-{i:02}.json' for i in range(8,22)]
    for log in reversed(sequence):
        data=read(log)
        for f in data['files']:assert digest(current[f['file']])==f['after_sha256'],('After hash mismatch',log,f['file'])
        if log=='duplicate-repairs.json':
            for r in reversed(data['candidates']):
                if not r['confirmed']:continue
                name=r['file'];lines=current[name].splitlines(keepends=True);i=r['line']-1
                assert lines[i].rstrip('\r\n')==r['after'],(log,name,r['line'])
                ending=lines[i][len(lines[i].rstrip('\r\n')):]
                lines[i]=r['before']+ending;current[name]=''.join(lines)
        else:
            for r in reversed(data['repairs']):current[r['file']]=reverse_patch(current[r['file']],r)
        for f in data['files']:
            if log=='source-repairs.json' and digest(current[f['file']])!=f['before_sha256']:
                # The first batch read text with universal newline conversion.
                # Reconstruct the original CRLF representation, accepting it
                # only if it matches the recorded original byte hash exactly.
                restored=current[f['file']].replace('\r\n','\n').replace('\n','\r\n')
                assert digest(restored)==f['before_sha256'],('Original newline reconstruction failed',f['file'])
                current[f['file']]=restored
            assert digest(current[f['file']])==f['before_sha256'],('Before hash mismatch',log,f['file'])
    originals=read('corrections.json')
    results=[]
    for record in originals:
        name=record['file'];text=current[name]
        assert digest(text)==record['corrected_sha256'],('Lexical corrected hash mismatch',name)
        if record['added_title']:
            title=record['added_title'];ending='\r\n' if text.startswith(title+'\r\n') else '\n'
            prefix=title+ending+ending;assert text.startswith(prefix)
            text=text[len(prefix):]
        lines=text.splitlines(keepends=True)
        for r in reversed(record['changes']):
            i=r['line']-1;assert lines[i].rstrip('\r\n')==r['after']
            ending=lines[i][len(lines[i].rstrip('\r\n')):];lines[i]=r['before']+ending
        original=''.join(lines);assert digest(original)==record['original_sha256'],('Original hash mismatch',name)
        results.append(dict(file=name,original_sha256=digest(original),current_sha256=final_hashes[name],original_reconstruction='exact byte-for-byte match'))
    source_status=[]
    for source in read('pdf-inventory.json'):
        sha=hashlib.sha256(Path(source['pdf']).read_bytes()).hexdigest()
        assert sha==source['pdf_sha256'],('Source PDF changed',source['pdf'])
        source_status.append(dict(file=source['markdown'],source_sha256=sha,source_unchanged=True))
    output=dict(status='passed',markdown_files=results,source_pdfs=source_status,
        limitations='Verifies edit provenance and source preservation; does not establish OCR completeness or correctness of untouched text.')
    (REPORT/'verification.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf8')
    print(f'Passed: {len(results)} original Markdown files reconstructed exactly; {len(source_status)} PDF hashes unchanged.')


if __name__=='__main__':main()
