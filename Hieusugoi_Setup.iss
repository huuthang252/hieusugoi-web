#define MyAppName "Hieusugoi"
#define MyAppVersion "2.1.0"
#define MyAppPublisher "Hieusugoi Project"
#define MyAppExeName "Hieusugoi.exe"

[Setup]
AppId={{A6F8E3D2-9B35-4B6B-8C2B-HIEUSUGOI106}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

OutputDir=installer
OutputBaseFilename=Hieusugoi_Setup_v2.1.0

SetupIconFile=assets\logo.ico

Compression=lzma
SolidCompression=yes
WizardStyle=modern

PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "dist\Hieusugoi\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: ".env"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Hieusugoi"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Hieusugoi"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Hieusugoi"; Flags: nowait postinstall skipifsilent