$ErrorActionPreference = 'Stop'
$workspaceMod = 'D:\Эон\faf-mods-pack\mods\Project Roc Unicorns'
$installedMod = 'D:\fafmods\mods\Project Roc Unicorns'
$backupRoot = Join-Path $workspaceMod ('source-assets\NEA0401\archive\installed-before-sync-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
$files = @(
    'units\NEA0401\NEA0401_lod0.scm',
    'units\NEA0401\NEA0401_albedo.dds',
    'units\NEA0401\NEA0401_specteam.dds',
    'units\NEA0401\NEA0401_normalsTS.dds',
    'units\NEA0401\NEA0401_rings_idle.sca',
    'units\NEA0401\NEA0401_script.lua',
    'units\NEA0401\NEA0401_unit.bp',
    'effects\emitters\nea0401_crystal_mist_emit.bp',
    'textures\particles\nea0401_crystal_mist_ramp.dds'
)
if (-not (Test-Path -LiteralPath (Join-Path $installedMod 'mod_info.lua') -PathType Leaf)) { throw 'Installed mod not found.' }
$metadata = Get-Content -LiteralPath (Join-Path $installedMod 'mod_info.lua') -Raw
if ($metadata -notmatch '04dd0e14-4dec-4b4c-87f8-e83b552bdd4e-6') { throw 'Installed mod UID differs.' }
foreach ($relative in $files) {
    if (-not (Test-Path -LiteralPath (Join-Path $workspaceMod $relative) -PathType Leaf)) { throw "Missing source: $relative" }
}
foreach ($relative in $files) {
    $source = Join-Path $workspaceMod $relative
    $target = Join-Path $installedMod $relative
    if (Test-Path -LiteralPath $target -PathType Leaf) {
        $backup = Join-Path $backupRoot $relative
        New-Item -ItemType Directory -Path (Split-Path -Parent $backup) -Force | Out-Null
        Copy-Item -LiteralPath $target -Destination $backup
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $target -Force
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash) { throw "Verification failed: $relative" }
}
"Updated and verified $($files.Count) files. Backup: $backupRoot"
