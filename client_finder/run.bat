@echo off
echo ================================
echo   CLIENT FINDER
echo ================================
echo.
echo Enter business type (e.g. dentist):
set /p QUERY="> "
echo.
echo Enter location (e.g. London UK):
set /p LOCATION="> "
echo.
echo Running...
echo.
python -m client_finder.main --query "%QUERY%" --location "%LOCATION%"
echo.
pause
