; Inno Setup Script for Hint Notes Generator
#define MyAppName "Hint Notes Generator"
#define MyAppVersion "1.3.1"
#define MyAppPublisher "Nilo Urmeneta Jr"
#define MyAppExeName "Hint_Notes_Generator.exe"

[Setup]
AppId={{A3C1D2E4-5F6G-7H8I-9J0K-1L2M3N4O5P6Q}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=.
OutputBaseFilename=Hint_Notes_Generator_Setup_v{#MyAppVersion}
SetupIconFile=favicon_io\favicon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
CloseApplications=force
RestartApplications=no
AppMutex=HintNotesGeneratorMutex

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "favicon_io\favicon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\favicon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\favicon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall