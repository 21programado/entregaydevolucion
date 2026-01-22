@echo off

REM === CONFIGURACIÓN ===
set "PYTHONW=C:\Program Files\Python314\pythonw.exe"
set "SCRIPT=C:\Users\Programador\Documents\PROGRAMAS\Economato Python\equipos v1\equipos_v1.py"
set "NOMBRE=Equipos y Materiales"

REM === CREAR ACCESO DIRECTO ===
powershell -NoProfile -Command ^
"$ws = New-Object -ComObject WScript.Shell; ^
$desk = [Environment]::GetFolderPath('Desktop'); ^
$sc = $ws.CreateShortcut($desk + '\%NOMBRE%.lnk'); ^
$sc.TargetPath = '%PYTHONW%'; ^
$sc.Arguments = '\"%SCRIPT%\"'; ^
$sc.WorkingDirectory = (Split-Path '%SCRIPT%'); ^
$sc.IconLocation = '%PYTHONW%'; ^
$sc.Save()"

echo Acceso directo creado correctamente.
pause
