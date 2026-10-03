param([string]$GameDir)
. "$PSScriptRoot\common.ps1"

Write-Host ''
Write-Host '  Catppuccin Macchiato for IW4x - uninstall' -ForegroundColor Magenta
Write-Host ''
try {
    $game = Find-GameDir $GameDir
    Write-Step "Game folder: $game"
    Assert-GameClosed $game

    $userraw = Join-Path $game 'userraw'
    $backupPath = Join-Path $userraw $BackupName
    $cfgPath = Join-Path $game 'players\iw4x_config.cfg'

    if ((Test-Path $backupPath) -and (Test-Path $cfgPath)) {
        $orig = Get-Content $backupPath -Raw | ConvertFrom-Json
        $cfg = Read-Config $cfgPath
        foreach ($p in $orig.PSObject.Properties) {
            if ($null -eq $p.Value) { Remove-ConfigValue $cfg $p.Name } else { Set-ConfigValue $cfg $p.Name $p.Value }
        }
        Write-Config $cfgPath $cfg.Text
        Write-Good 'Restored your original console/HUD colours'
    }

    $removed = 0
    foreach ($f in $PayloadFiles + $BackupName) {
        $p = Join-Path $userraw $f
        if (Test-Path $p) { Remove-Item $p -Force; $removed++ }
    }
    Write-Good "Removed $removed theme file(s) from userraw\"

    Write-Host ''
    Write-Good 'Done - IW4x is back to its stock look.'
    Write-Step 'Classes loaded with ctp_classes stay in your profile; edit or reset them in Create-a-Class.'
    exit 0
} catch {
    Write-Host ''
    Write-Host "  Uninstall failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
