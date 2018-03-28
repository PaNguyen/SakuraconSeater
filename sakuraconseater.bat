@echo off
reg Query "HKLM\Hardware\Description\System\CentralProcessor\0" | find /i "x86" > NUL && set OS=32bit || set OS=64bit
if %OS%==32bit set path=%path%;%PROGRAMFILES%\SakuraconSeater;%PROGRAMFILES%\SakuraconSeater\lib;%USERPROFILE%\Documents\SakuraconSeater
if %OS%==64bit set path=%path%;%PROGRAMFILES(X86)%\SakuraconSeater;%PROGRAMFILES(x86)%\SakuraconSeater\lib;%USERPROFILE%\Documents\SakuraconSeater
start sakuraconseater.exe
timeout /t 3
start "" http://localhost:5000
