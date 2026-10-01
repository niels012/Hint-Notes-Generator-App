; Inno Setup Script for Hint Notes Generator
#define MyAppName "Hint Notes Generator"
#define MyAppVersion "1.4.1"
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
[Code]
// When the app updates itself, the installer inherits PyInstaller's internal
// _PYI_* environment variables from the running app and passes them on to the
// app relaunched by [Run] above. The relaunched app's bootloader then mistakes
// this installer for its own parent process and fails with "Security validation
// failure: parent process has different executable!". Setting this variable
// tells the bootloader to ignore the inherited values and start fresh. Done here
// (not only in the app) because older app versions launch the installer without
// cleaning their environment.
function SetEnvironmentVariable(lpName: String; lpValue: String): Boolean;
  external 'SetEnvironmentVariableW@kernel32.dll stdcall';

function InitializeSetup(): Boolean;
begin
  SetEnvironmentVariable('PYINSTALLER_RESET_ENVIRONMENT', '1');
  Result := True;
end;
