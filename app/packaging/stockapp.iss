; StockApp Windows Installer Script (Inno Setup)
;
; Optional / best-effort, per the original spec ("if possible, create an
; installer"). Requires Inno Setup (https://jrsoftware.org/isinfo.php)
; installed on the Windows build machine — not wired into build.bat since
; it's a separate tool with its own install step.
;
; Usage:
;   1. Run build.bat first to produce dist\StockApp\StockApp.exe
;   2. Open this file in Inno Setup Compiler (or run: iscc stockapp.iss)
;   3. Output installer appears in packaging\output\StockAppSetup.exe

#define AppName "StockApp"
#define AppVersion "1.0.0"
#define AppPublisher "StockApp"
#define AppExeName "StockApp.exe"

[Setup]
AppId={{B6E1F6E4-6B8C-4B1B-9C7B-STOCKAPP0001}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=output
OutputBaseFilename=StockAppSetup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
; Uninstall must NOT touch %APPDATA%\StockApp so a user's data (and
; existing backups) survive an uninstall/reinstall.
Uninstallable=yes

[Languages]
Name: "thai"; MessagesFile: "compiler:Languages\Thai.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\StockApp\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "สร้างไอคอนบน Desktop"; GroupDescription: "ตัวเลือกเพิ่มเติม:"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "เปิดใช้งาน {#AppName}"; Flags: nowait postinstall skipifsilent
