# Windows package

Unzip the entire CharactersUnlimited folder and double-click CharactersUnlimited.exe. Keep the _internal folder beside it. Python, Node and developer tools are bundled or unnecessary. The workshop opens in your default browser; the desktop controller can reopen it or stop the local application. Wait for Saved on this PC before stopping. Closing the browser alone leaves the local controller running.

Character data is stored under %LOCALAPPDATA%\CharactersUnlimited, independently of the package. A newer package can replace the extracted folder without deleting saves. Use Back up all characters before updates; retain portable JSON exports for transfers between PCs. PDF edits stay in that PDF.

This is an early package of the currently implemented Rifts Human/Vagabond path. The original full-corpus plan, Heroes Unlimited, broader rules and advancement remain incomplete. Unfinished parts are displayed in the workshop; missing PDF values remain blank. It is not the final release.

Startup errors are written to startup-error.log in the character-data directory and displayed in a message box. Keep this log when reporting a launch failure.

For maintainers, run scripts/build-windows.ps1 on Windows with Python 3.14 installed. It creates an isolated packaging environment using requirements-build.txt, then bundles the executable and resources. Build dependencies are downloaded during the build; players need no downloads at runtime. The PyInstaller specification includes accepted packs, corpus metadata, web assets, the reference PDF and its licensed editing font. Dependency licenses and Python runtime notices are bundled under `_internal`; the font NOTICE remains beside its bundled font. The Windows CI job uploads an early package artifact after its frozen checks pass.

To check the actual frozen executable:

```powershell
$env:CHARACTERS_UNLIMITED_EXE = (Resolve-Path dist\CharactersUnlimited\CharactersUnlimited.exe).Path
python -m unittest tests.test_packaged_app -v
```

The check launches from a temporary unrelated directory with Python and Node absent from PATH and tests create/reopen, source coverage, portable import and editable PDF fields. Full release acceptance additionally requires GUI/browser delivery and all completed character paths.
