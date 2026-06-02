@echo off
title ARIA Launcher

echo Starting memory proxy...
start /min "ARIA Memory" cmd /c "cd /d C:\ARIA\persona-mesh-agent && python llm_proxy.py"

timeout /t 3 /nobreak >nul

echo Starting PersonaEngine...
start "" /D "C:\ARIA\PersonaEngine-3.0.2-win-x64" "C:\ARIA\PersonaEngine-3.0.2-win-x64\PersonaEngine.exe"

exit
