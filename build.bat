@echo off
echo =======================================
echo Installing required Python packages...
echo =======================================
pip install -r requirements.txt

echo.
echo =======================================
echo Installing PyInstaller...
echo =======================================
pip install pyinstaller

echo.
echo =======================================
echo Creating executable file from run_app.py...
echo =======================================
pyinstaller --noconfirm --onefile --windowed --icon=icon.ico --name "N-SnapRecorde" run_app.py

echo.
echo =======================================
echo Build complete!
echo Your EXE file is in the "dist" folder with name: N-SnapRecorde.exe
echo =======================================
pause
