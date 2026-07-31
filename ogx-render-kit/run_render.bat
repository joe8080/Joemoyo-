@echo off
REM OGX one-click render. Usage:  run_render.bat 23_Kingdom_of_Meroe
REM Place this file (and render_ogx.py) inside your _OGX_BATCH folder.
if "%~1"=="" (
  echo Usage: run_render.bat NN_Slug   e.g. run_render.bat 23_Kingdom_of_Meroe
  exit /b 1
)
python "%~dp0render_ogx.py" %1
pause
