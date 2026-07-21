[Files]

Source: "..\cliente\cliente.exe"; DestDir: "{app}"; Flags: ignoreversion

Source: "..\cliente\launcher.exe"; DestDir: "{app}"; Flags: ignoreversion

Source: "..\cliente\config_cliente.json"; DestDir: "{app}"; Flags: onlyifdoesntexist ignoreversion

Source: "..\cliente\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
