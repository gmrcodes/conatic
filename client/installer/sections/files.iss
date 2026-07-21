[Files]

Source: "..\src\dist\cliente\cliente.exe"; DestDir: "{app}"; Flags: ignoreversion

Source: "..\launcher\dist\launcher.exe"; DestDir: "{app}"; Flags: ignoreversion

Source: "..\src\config_cliente.json"; DestDir: "{app}"; Flags: onlyifdoesntexist ignoreversion

Source: "..\src\dist\cliente\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
