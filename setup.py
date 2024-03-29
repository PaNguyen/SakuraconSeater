#!/usr/bin/env python3

from cx_Freeze import setup, Executable

setup(name = "SakuraconSeater",
        version = "0.1",
        description = "",
        options = {
            "build_exe": {
                "packages": ["idna","tornado","twilio","passlib"],
                "excludes": ["mysettings", "mysettings.py"],
                "bin_excludes": ["mysettings", "mysettings.py"],
                "bin_path_excludes": ["mysettings", "mysettings.py"],
                "include_files": ["templates/", "static/","sakuraconseater.bat"]
                }
            },
        executables = [Executable("sakuraconseater.py", shortcut_name="Sakuracon Seater", shortcut_dir="StartMenuFolder")])
