@echo off
setlocal EnableExtensions

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$files = Get-ChildItem -Path . -Filter *.md -Recurse; if (!$files) { Write-Host 'No .md files found.'; exit };" ^
  "$i = 1; $files | ForEach-Object { Write-Host ('[' + $i + '] ' + $_.FullName); $i++ };" ^
  "Write-Host '[A] Abrir todos'; $sel = Read-Host 'Seleccion';" ^
  "if ($sel -match '^[Aa]$') { $files | ForEach-Object { Start-Process $_.FullName }; exit };" ^
  "$n = [int]$sel; if ($n -ge 1 -and $n -le $files.Count) { Start-Process $files[$n-1].FullName } else { Write-Host 'Seleccion invalida.' }"

endlocal
