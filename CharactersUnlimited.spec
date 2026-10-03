# Build on Windows. All data stays outside this distributable folder.
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, copy_metadata

data = collect_data_files('characters_unlimited')
for dependency in ('pypdf', 'reportlab', 'Pillow', 'charset-normalizer', 'pyinstaller'):
    data += copy_metadata(dependency)
data += [(str(Path(sys.base_prefix) / 'LICENSE.txt'), 'third-party-licenses/Python')]

a = Analysis(['scripts/windows_entry.py'], pathex=['.'],
             datas=data,
             hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='CharactersUnlimited',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False, console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='CharactersUnlimited')
