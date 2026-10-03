$ErrorActionPreference = 'Stop'
.\.venv\Scripts\python.exe -m mypy --check-untyped-defs characters_unlimited tests
if ($LASTEXITCODE -ne 0) { throw 'Python type checking failed' }
python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Character workflow tests failed' }
python -m compileall -q characters_unlimited tests
if ($LASTEXITCODE -ne 0) { throw 'Python compilation failed' }
foreach ($browserScript in Get-ChildItem characters_unlimited/web -Filter '*.js') {
    node --check $browserScript.FullName
    if ($LASTEXITCODE -ne 0) { throw "Browser JavaScript syntax check failed: $($browserScript.Name)" }
}
