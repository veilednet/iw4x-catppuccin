# Shared helpers for install.ps1 / uninstall.ps1
$ErrorActionPreference = 'Stop'

$PackageRoot   = Split-Path -Parent $PSScriptRoot
$PayloadDir    = Join-Path $PackageRoot 'userraw'
$PayloadFiles  = @('z_catppuccin.iwd', 'ctp_theme.cfg')
$LegacyFiles   = @('ctp_classes.cfg')   # shipped by v1.0.0; cleaned up on install/uninstall
$BackupName    = 'catppuccin_backup.json'
$BuiltForIw4x  = 'r5154'   # IW4x client the bundled menus were generated from
$GameFolder    = 'Call of Duty Modern Warfare 2'

function Write-Step($msg)  { Write-Host "  $msg" }
function Write-Good($msg)  { Write-Host "  $msg" -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "  $msg" -ForegroundColor Yellow }

function Test-GameDir($dir) {
    return $dir -and (Test-Path (Join-Path $dir 'iw4x.exe')) -and (Test-Path (Join-Path $dir 'main'))
}

function Get-SteamLibraries {
    $roots = @()
    foreach ($key in 'HKCU:\Software\Valve\Steam', 'HKLM:\SOFTWARE\WOW6432Node\Valve\Steam', 'HKLM:\SOFTWARE\Valve\Steam') {
        try {
            $p = Get-ItemProperty -Path $key -ErrorAction Stop
            foreach ($v in $p.SteamPath, $p.InstallPath) { if ($v) { $roots += ($v -replace '/', '\') } }
        } catch {}
    }
    $libs = @()
    foreach ($r in ($roots | Select-Object -Unique)) {
        $libs += $r
        $vdf = Join-Path $r 'steamapps\libraryfolders.vdf'
        if (Test-Path $vdf) {
            foreach ($m in [regex]::Matches((Get-Content $vdf -Raw), '"path"\s+"([^"]+)"')) {
                $libs += ($m.Groups[1].Value -replace '\\\\', '\')
            }
        }
    }
    return $libs | Select-Object -Unique
}

function Find-GameDir([string]$Requested) {
    if ($Requested) {
        if (Test-GameDir $Requested) { return (Resolve-Path $Requested).Path }
        throw "No IW4x install found in '$Requested' (expected iw4x.exe there)."
    }
    # 1) package extracted inside the game folder
    $parent = Split-Path -Parent $PackageRoot
    if (Test-GameDir $parent) { return $parent }
    # 2) any Steam library
    foreach ($lib in Get-SteamLibraries) {
        $dir = Join-Path $lib "steamapps\common\$GameFolder"
        if (Test-GameDir $dir) { return $dir }
    }
    # 3) ask
    Add-Type -AssemblyName System.Windows.Forms
    $dlg = New-Object System.Windows.Forms.FolderBrowserDialog
    $dlg.Description = "Select your '$GameFolder' folder (the one containing iw4x.exe)"
    if ($dlg.ShowDialog() -eq 'OK' -and (Test-GameDir $dlg.SelectedPath)) { return $dlg.SelectedPath }
    throw "Couldn't find an IW4x install. Run the IW4x launcher once first, or pass the folder: install.bat `"D:\...\$GameFolder`""
}

function Assert-GameClosed($game) {
    $running = Get-Process -Name iw4x -ErrorAction SilentlyContinue |
        Where-Object { $_.Path -and $_.Path.StartsWith($game, [StringComparison]::OrdinalIgnoreCase) }
    if ($running) {
        throw 'IW4x is running - close the game and run this again (it rewrites its config on exit).'
    }
}

function Get-ThemeDvars {
    $map = [ordered]@{}
    foreach ($line in Get-Content (Join-Path $PayloadDir 'ctp_theme.cfg')) {
        if ($line -match '^seta\s+(\S+)\s+"([^"]*)"') { $map[$Matches[1]] = $Matches[2] }
    }
    return $map
}

function Read-Config($path) {
    $text = [IO.File]::ReadAllText($path)
    $nl = if ($text.Contains("`r`n")) { "`r`n" } else { "`n" }
    return @{ Text = $text; NL = $nl }
}

function Write-Config($path, $text) {
    [IO.File]::WriteAllText($path, $text, (New-Object System.Text.UTF8Encoding $false))
}

function Get-ConfigValue($text, $name) {
    $m = [regex]::Match($text, '(?m)^seta ' + [regex]::Escape($name) + ' "([^"\r\n]*)"')
    if ($m.Success) { return $m.Groups[1].Value } else { return $null }
}

function Set-ConfigValue($cfg, $name, $value) {
    $pattern = '(?m)^seta ' + [regex]::Escape($name) + ' "[^"\r\n]*"'
    $line = "seta $name `"$value`""
    if ([regex]::IsMatch($cfg.Text, $pattern)) {
        $cfg.Text = [regex]::Replace($cfg.Text, $pattern, $line.Replace('$', '$$'))
    } else {
        $cfg.Text = $cfg.Text.TrimEnd("`r", "`n") + $cfg.NL + $line + $cfg.NL
    }
}

function Remove-ConfigValue($cfg, $name) {
    $cfg.Text = [regex]::Replace($cfg.Text, '(?m)^seta ' + [regex]::Escape($name) + ' "[^"\r\n]*"\r?\n?', '')
}
