@echo off
reg Query "HKLM\Hardware\Description\System\CentralProcessor\0" | find /i "x86" > NUL && set OS=32bit || set OS=64bit
if %OS%==32bit set path=%path%;%USERPROFILE%\Documents\SakuraconSeater;%PROGRAMFILES%\SakuraconSeater;%PROGRAMFILES%\SakuraconSeater\lib
if %OS%==64bit set path=%path%;%USERPROFILE%\Documents\SakuraconSeater;%PROGRAMFILES(X86)%\SakuraconSeater;%PROGRAMFILES(x86)%\SakuraconSeater\lib
start sakuraconseater.exe
timeout /t 3
start "" http://localhost:5000
