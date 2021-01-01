@ECHO OFF

cd {}\utonium\app
echo %CD%
venv\Scripts\activate.bat && python index.py

pause