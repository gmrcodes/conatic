#define AppName "Control Cliente"
#define AppVersion "1.2.0"
#define AppPublisher "German Riveros"

[Setup]

AppId={{4A45C420-3DB4-4DF8-8524-DDEC42EC1468}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
ArchitecturesInstallIn64BitMode=x64
ChangesAssociations=no
CloseApplications=yes
Compression=lzma2
DefaultDirName={autopf}\Control Cliente
DefaultGroupName=Control Cliente
DisableDirPage=yes
DisableFinishedPage=no
DisableProgramGroupPage=yes
DisableReadyMemo=no
DisableStartupPrompt=yes
DisableWelcomePage=no
OutputDir=Output
OutputBaseFilename=ControlCliente_Setup_v{#AppVersion}
PrivilegesRequired=admin
RestartApplications=no
SetupIconFile=resources\icono.ico
SolidCompression=yes
UninstallDisplayIcon={app}\cliente.exe
UsePreviousAppDir=no
UsePreviousGroup=no
UsePreviousSetupType=no
UsePreviousTasks=no
VersionInfoVersion={#AppVersion}
VersionInfoTextVersion={#AppVersion}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription=Instalador oficial de Control Cliente
WizardStyle=modern
AppMutex=ControlClienteMutexSecret,ControlLauncherMutexSecret