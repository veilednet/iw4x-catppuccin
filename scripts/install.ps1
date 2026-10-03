param([string]$GameDir)
. "$PSScriptRoot\common.ps1"

Write-Host ''
Write-Host '  Catppuccin Macchiato for IW4x - install' -ForegroundColor Magenta
Write-Host ''
try {
    $game = Find-GameDir $GameDir
    Write-Step "Game folder: $game"
    Assert-GameClosed $game

    $ver = (Get-Item (Join-Path $game 'iw4x.dll') -ErrorAction SilentlyContinue).VersionInfo.FileVersion
    if ($ver -and $ver.Trim() -ne $BuiltForIw4x) {
        Write-Warn "Your IW4x is $ver; this theme was generated from $BuiltForIw4x."
        Write-Warn 'It will still work, but menus IW4x changed since then show the older layout until the theme is rebuilt.'
    }

    $userraw = Join-Path $game 'userraw'
    New-Item -ItemType Directory -Force $userraw | Out-Null
    foreach ($f in $PayloadFiles) { Copy-Item (Join-Path $PayloadDir $f) $userraw -Force }
    foreach ($f in $LegacyFiles) { Remove-Item (Join-Path $userraw $f) -Force -ErrorAction SilentlyContinue }
    Write-Good 'Copied theme files to userraw\'

    # Console / scoreboard / sprint-meter colours live in the player config.
    $cfgPath = Join-Path $game 'players\iw4x_config.cfg'
    if (Test-Path $cfgPath) {
        $cfg = Read-Config $cfgPath
        $dvars = Get-ThemeDvars
        $backupPath = Join-Path $userraw $BackupName
        if (-not (Test-Path $backupPath)) {      # keep the very first originals across re-installs
            $orig = [ordered]@{}
            foreach ($k in $dvars.Keys) { $orig[$k] = Get-ConfigValue $cfg.Text $k }
            $orig | ConvertTo-Json | Set-Content -Path $backupPath -Encoding UTF8
        }
        foreach ($k in $dvars.Keys) { Set-ConfigValue $cfg $k $dvars[$k] }
        Write-Config $cfgPath $cfg.Text
        Write-Good "Applied console/HUD colours ($($dvars.Count) settings, originals saved for uninstall)"
    } else {
        Write-Warn 'No players\iw4x_config.cfg yet - start IW4x once, then run install again for the console colours.'
        Write-Warn '(Or type  exec ctp_theme  in the in-game console.)'
    }

    Write-Host ''
    Write-Good 'Done! Launch IW4x as usual.'
    Write-Step 'To remove everything: run uninstall.bat'
    exit 0
} catch {
    Write-Host ''
    Write-Host "  Install failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
