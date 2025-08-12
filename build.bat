@echo off
echo Installing required packages...
pip install -r requirements.txt

echo.
echo Creating executable file...
pip install pyinstaller

pyinstaller --onefile --windowed --icon=icon.ico AutoScreenshot.py

echo.
echo Build complete! Check the 'dist' folder for your exe file.
pause
