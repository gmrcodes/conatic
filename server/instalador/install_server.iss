; --- SECCIÓN DE CONFIGURACIÓN PRINCIPAL ---
[Setup]
; AppId identifica de forma única al proyecto. Al mantener el mismo AppId, 
; Inno Setup detectará automáticamente si es una ACTUALIZACIÓN.
AppId={{41F64431-2A6F-479B-81A1-DE0623E02E16}
AppName=Control Server
AppVersion=1.1.0
AppPublisher=germaodev
DefaultDirName={autopf}\Control Server
DefaultGroupName=Control Server
AllowNoIcons=yes
; OutputBaseFilename es el nombre del instalador resultante
OutputBaseFilename=Control_Server_Setup_v{AppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; Evita que se instale o actualice si el servidor ya se está ejecutando
AppMutex=ControlServerMutexSecret

; --- CONTROL DE ARCHIVOS ---
[Files]
; ignoreversion asegura que en una ACTUALIZACIÓN el ejecutable viejo sea reemplazado por el nuevo
Source: "..\dist\server\server.exe"; DestDir: "{app}"; Flags: ignoreversion

; NOTA SOBRE LA BASE DE DATOS (sistema_central.db): 
; Si tu script de Python crea la base de datos automáticamente al arrancar, NO la incluyas aquí.
; Si manejas una base de datos inicial con datos pre-cargados, usa la siguiente línea:
;Source: "sistema_central.db"; DestDir: "{app}"; Flags: onlyifdoesntexist uninsneveruninstall

; --- ICONOS Y ACCESOS DIRECTOS ---
[Icons]
Name: "{group}\Servidor Central Pro"; Filename: "{app}\servidor.exe"
Name: "{autodesktop}\Servidor Central Pro"; Filename: "{app}\servidor.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

; --- PROGRAMA POST-INSTALACIÓN ---
[Run]
Description: "{cm:LaunchProgram,Servidor Central Pro}"; Filename: "{app}\servidor.exe"; Flags: nowait postinstall skipifsilent

; --- DESARROLLO EN INNO PASCAL SCRIPT ---
[Code]
// Función que se ejecuta al iniciar la instalación/actualización
function InitializeSetup(): Boolean;
var
  ResultadoReg: Cardinal;
begin
  Result := True;
  // Inno Setup maneja de forma nativa el AppMutex configurado arriba.
  // Si el servidor está abierto, le advertirá al usuario que debe cerrarlo antes de continuar.
end;

// Procedimiento que se ejecuta durante la DESINSTALACIÓN
procedure CurUninstallStepChanged(JustAfterAnUninstallStep: TUninstallStep);
var
  RutaDB: String;
begin
  // Nos posicionamos justo al final de la desinstalación estándar
  if JustAfterAnUninstallStep = usPostUninstall then
  begin
    RutaDB := ExpandConstant('{app}\sistema_central.db');
    
    // Como la Base de Datos se modifica en caliente, Inno Setup no la borra por defecto.
    // Preguntamos explícitamente al usuario si desea eliminarla (Control de desinstalación limpia).
    if FileExists(RutaDB) then
    begin
      if MsgBox('¿Desea eliminar de forma permanente la base de datos (sistema_central.db) y todo el historial de las terminales?', 
                 mbConfirmation, MB_YESNO) = IDYES then
      begin
        DeleteFile(RutaDB);
        // Intentamos borrar el directorio del programa si quedó vacío
        DelTree(ExpandConstant('{app}'), True, True, True);
      end;
    end;
  end;
end;