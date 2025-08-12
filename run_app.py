# run_app.py
# Main entry point for the Advanced Screenshot & ScreenRecorder Tool

"""
Advanced Screenshot & ScreenRecorder Tool
==========================================

This application has been split into two main components:

1. screenshot_engine.py - Contains all the core functionality for:
   - Screenshot capture
   - Screen recording
   - Audio recording
   - File management
   - Hotkey handling
   - System tray integration

2. main_gui.py - Contains the user interface:
   - Tkinter GUI components
   - User input handling
   - Settings display
   - Communication with the engine

Usage:
    python run_app.py

Dependencies:
    - mss, opencv-python, sounddevice, numpy, scipy
    - keyboard, pystray, pillow, psutil
    - tkinter (usually comes with Python)

The engine and GUI communicate through:
    - Settings dictionary in the engine
    - Callback functions for UI updates
    - Direct method calls from GUI to engine
"""

from main_gui import ScreenshotGUI

def main():
    """Main entry point"""
    try:
        app = ScreenshotGUI()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
    except Exception as e:
        print(f"Application error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
