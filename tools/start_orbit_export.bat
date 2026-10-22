@echo off
cd /d "%~dp0"
python orbit_fixtures_export.py --loop 60
pause
