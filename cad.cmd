@echo off
rem Wrapper so models can be built with:  cad build models\name.py   (Windows)
if not exist "%~dp0.venv\Scripts\python.exe" (
  echo Not set up yet. Run: py scripts\setup.py
  exit /b 1
)
pushd "%~dp0"
".venv\Scripts\python.exe" -m cadkit %*
set rc=%errorlevel%
popd
exit /b %rc%
