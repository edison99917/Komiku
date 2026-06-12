@echo off
REM Launcher for the Komiku downloader. Runs the bundled venv Python against
REM komiku.py and forwards all arguments. Works from any directory because
REM %~dp0 expands to this .bat file's own folder.
"%~dp0.venv\Scripts\python.exe" "%~dp0komiku.py" %*
