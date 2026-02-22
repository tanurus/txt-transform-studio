@echo off
REM Launch the transform app
CD /D "%~dp0"
IF EXIST .venv\Scripts\activate.bat (
  CALL .venv\Scripts\activate.bat
)
pythonw main.py
