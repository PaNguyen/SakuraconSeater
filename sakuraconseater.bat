@echo off
set path=%path%;%PROGRAMFILES(X86)%\SakuraconSeater;%PROGRAMFILES(X86)%\SakuraconSeater\lib;%USERPROFILE%\Documents\SakuraconSeater
start sakuraconseater.exe
timeout /t 3
start "" http://localhost:5000
