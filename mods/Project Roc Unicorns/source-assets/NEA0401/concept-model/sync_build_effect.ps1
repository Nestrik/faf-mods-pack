$ErrorActionPreference = 'Stop'
$source = 'D:\Эон\faf-mods-pack\mods\Project Roc Unicorns\units\NEA0401\NEA0401_script.lua'
$target = 'D:\fafmods\mods\Project Roc Unicorns\units\NEA0401\NEA0401_script.lua'
$expected = 'DDA56D2D590208222FF730296FCD686C0208F553717F688028ABA25731FD7C02'
if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $expected) { throw 'Installed script changed after inspection; refusing to overwrite.' }
$backupDir = 'D:\Эон\faf-mods-pack\mods\Project Roc Unicorns\source-assets\NEA0401\archive\installed-before-aeon-build-effect'
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
$backup = Join-Path $backupDir ('NEA0401_script-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.lua.txt')
Copy-Item -LiteralPath $target -Destination $backup
Copy-Item -LiteralPath $source -Destination $target -Force
if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash) { throw 'Copied script failed verification.' }
"Updated and verified NEA0401 script. Backup: $backup"
