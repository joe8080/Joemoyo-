@echo off
setlocal
title Install MOYO Chords

rem ---- Ask Windows for permission once (needed to write to Program Files) ----
set "MOYO_BAT=%~f0"
fltmc >nul 2>&1
if not errorlevel 1 goto :admin
if /i "%~1"=="elevated" (
    echo Could not get administrator permission.
    echo Please right-click this file and choose "Run as administrator".
    pause
    exit /b 1
)
powershell -NoProfile -Command "Start-Process -FilePath $env:MOYO_BAT -ArgumentList 'elevated' -Verb RunAs"
if errorlevel 1 (
    echo.
    echo Windows needs your OK to install the plugin. Run this file again and click Yes.
    pause
)
exit /b

:admin
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s = Get-Content -LiteralPath $env:MOYO_BAT -Raw; iex ($s.Substring($s.LastIndexOf('#' + 'PS_START')))"
exit /b %errorlevel%

#PS_START
$ErrorActionPreference = 'Stop'
$name = 'MOYO Chords.vst3'
$unattended = $env:MOYO_UNATTENDED -eq '1'
function Done($code) { if (-not $unattended) { Write-Host ''; Read-Host 'Press Enter to close' | Out-Null }; exit $code }

Write-Host ''
Write-Host '  MOYO CHORDS - INSTALLER      ' -ForegroundColor Green
Write-Host '  =========================' -ForegroundColor Green
Write-Host ''

$tmp = $null
try {
    # 1. Find the plugin: next to this file, or inside the downloaded zip.
    $here = Split-Path -Parent $env:MOYO_BAT
    $src = Join-Path $here $name
    if (-not (Test-Path -LiteralPath $src)) {
        $places = @($here, (Join-Path $env:USERPROFILE 'Downloads'))
        try { $places += (New-Object -ComObject Shell.Application).NameSpace('shell:Downloads').Self.Path } catch {}
        $zip = Get-ChildItem -LiteralPath ($places | Select-Object -Unique) -Filter 'MOYO-Chords-Windows*.zip' -ErrorAction SilentlyContinue |
               Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if (-not $zip) { throw "I couldn't find MOYO-Chords-Windows.zip. Put this installer in the same folder as the zip and run it again." }
        Write-Host "  Unzipping $($zip.Name) ..."
        $tmp = Join-Path $env:TEMP ('moyo-' + [guid]::NewGuid().ToString('N'))
        Expand-Archive -LiteralPath $zip.FullName -DestinationPath $tmp
        $src = Get-ChildItem -LiteralPath $tmp -Recurse -Directory -Filter $name | Select-Object -First 1 -ExpandProperty FullName
        if (-not $src) { throw "The zip didn't contain '$name'." }
    }

    # 2. FL Studio must be closed, or Windows won't let us replace the plugin.
    while (-not $unattended -and (Get-Process -Name 'FL64', 'FL', 'FL Studio*' -ErrorAction SilentlyContinue)) {
        Write-Host '  FL Studio is open. Please close it, then press Enter.' -ForegroundColor Yellow
        Read-Host | Out-Null
    }

    # 3. Copy into the standard VST3 folder.
    $pf = if ($env:ProgramW6432) { $env:ProgramW6432 } else { $env:ProgramFiles }
    $destRoot = Join-Path $pf 'Common Files\VST3'
    New-Item -ItemType Directory -Force -Path $destRoot | Out-Null
    $dest = Join-Path $destRoot $name
    if (Test-Path -LiteralPath $dest) {
        Write-Host '  Removing the old version ...'
        Remove-Item -LiteralPath $dest -Recurse -Force
    }
    Write-Host "  Installing to $destRoot ..."
    Copy-Item -LiteralPath $src -Destination $dest -Recurse
    Get-ChildItem -LiteralPath $dest -Recurse -File | Unblock-File

    Write-Host ''
    Write-Host '  DONE! MOYO Chords is installed.' -ForegroundColor Green
    Write-Host ''
    Write-Host '  In FL Studio:'
    Write-Host '   1. Options > Manage plugins > Find more plugins'
    Write-Host '   2. Tick the star next to MOYO Chords'
    Write-Host '   3. In the Channel Rack click + and choose MOYO Chords'
    $code = 0
}
catch {
    Write-Host ''
    Write-Host "  Something went wrong: $($_.Exception.Message)" -ForegroundColor Red
    $code = 1
}
finally {
    if ($tmp -and (Test-Path -LiteralPath $tmp)) { Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue }
}
Done $code
