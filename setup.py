#!/usr/bin/env python3

from cx_Freeze import setup, Executable

setup(name = "SakuraconSeater",
        version = "0.1",
        description = "",
        options = {
            "build_exe": {
                "packages": ["idna","tornado","twilio","passlib"],
                "bin_excludes": ["mysettings"],
                "include_files": ["templates/", "static/","sakuraconseater.bat"]
                }
            },
        executables = [Executable("sakuraconseater.py", shortcutName="Sakuracon Seater", shortcutDir="StartMenuFolder")])
