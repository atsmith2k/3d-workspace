@echo off
rem Wrapper so models can be built with:  cad build models\name.py
"%~dp0.venv\Scripts\python.exe" -m cadkit %*
