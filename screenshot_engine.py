# screenshot_engine.py
# Engine for screenshot functionality
# Dependencies: keyboard, pystray, pillow, psutil, pyautogui

import os
import time
import pyautogui
import threading
import json
import keyboard
import pystray
from PIL import Image, ImageDraw
from datetime import datetime
import gc
import psutil


class ScreenshotEngine:
    def __init__(self):
        self.settings_file = "screenshot_settings.json"
        self.is_capturing = False
        self.capture_thread = None
        self.auto_capture_thread = None
        self.tray_icon = None

        # Optimize pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.05

        # Settings dictionary - only screenshot related
        self.settings = {
            'folder_path': '',
            'capture_hotkey': 'ctrl+shift+s',
            'stop_hotkey': 'ctrl+shift+q',
            'auto_capture_enabled': False,
            'auto_capture_interval': 60,
        }

        # Callbacks for UI updates
        self.status_callback = None
        self.memory_callback = None

        self.load_settings()

    def set_callbacks(self, status_callback=None, memory_callback=None):
        """Set callback functions for UI updates"""
        self.status_callback = status_callback
        self.memory_callback = memory_callback

    def update_status(self, message):
        """Update status and call callback if set"""
        if self.status_callback:
            self.status_callback(message)

    def load_settings(self):
        """Load settings from JSON file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                    self.settings.update(saved_settings)
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_settings(self):
        """Save settings to JSON file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def update_setting(self, key, value):
        """Update a single setting"""
        self.settings[key] = value

    def get_setting(self, key):
        """Get a setting value"""
        return self.settings.get(key)

    def setup_hotkeys(self):
        """Set up global hotkeys"""
        try:
            keyboard.unhook_all()
            keyboard.add_hotkey(self.settings['capture_hotkey'], self.manual_capture)
            keyboard.add_hotkey(self.settings['stop_hotkey'], self.stop_all_capture)
        except Exception as e:
            print(f"Error setting up hotkeys: {e}")

    def manual_capture(self):
        """Manual screenshot capture"""
        if not self.settings['folder_path']:
            print("Error: Please select a save folder!")
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.settings['folder_path'], f"screenshot_{timestamp}.png")

            screenshot = pyautogui.screenshot()
            screenshot.save(filename, optimize=True, quality=85)

            self.update_status(f"Captured: {os.path.basename(filename)}")

            del screenshot
            gc.collect()

        except Exception as e:
            print(f"Failed to capture: {e}")
            self.update_status(f"Error: {e}")

    def auto_capture_loop(self):
        """Auto capture loop running in background thread"""
        while self.settings['auto_capture_enabled'] and self.is_capturing:
            try:
                self.manual_capture()
                for _ in range(self.settings['auto_capture_interval']):
                    if not self.settings['auto_capture_enabled'] or not self.is_capturing:
                        break
                    time.sleep(1)
            except Exception as e:
                print(f"Auto capture error: {e}")
                time.sleep(1)

    def start_background_capture(self):
        """Start background capture process"""
        if not self.settings['folder_path']:
            print("Error: Please select a save folder!")
            return False

        self.save_settings()
        self.setup_hotkeys()
        self.is_capturing = True
        
        if self.settings['auto_capture_enabled']:
            self.auto_capture_thread = threading.Thread(target=self.auto_capture_loop, daemon=True)
            self.auto_capture_thread.start()
        
        self.create_tray_icon()
        self.update_status("Running in background...")
        return True

    def stop_all_capture(self):
        """Stop all capture processes"""
        self.is_capturing = False
        self.settings['auto_capture_enabled'] = False
        self.update_status("Stopped")

    def show_window(self, icon=None, item=None):
        """Show main window - callback for tray icon"""
        if hasattr(self, 'show_window_callback') and self.show_window_callback:
            self.show_window_callback()

    def start_recording(self, icon=None, item=None):
        """Start recording - callback for tray icon"""
        if hasattr(self, 'start_recording_callback') and self.start_recording_callback:
            self.start_recording_callback()

    def stop_recording(self, icon=None, item=None):
        """Stop recording - callback for tray icon"""
        if hasattr(self, 'stop_recording_callback') and self.stop_recording_callback:
            self.stop_recording_callback()

    def exit_app(self, icon=None, item=None):
        """Exit application - callback for tray icon"""
        if hasattr(self, 'exit_callback') and self.exit_callback:
            self.exit_callback()

    def set_tray_callbacks(self, show_window_callback=None, start_recording_callback=None, 
                          stop_recording_callback=None, exit_callback=None):
        """Set callbacks for tray icon actions"""
        self.show_window_callback = show_window_callback
        self.start_recording_callback = start_recording_callback
        self.stop_recording_callback = stop_recording_callback
        self.exit_callback = exit_callback

    def create_tray_icon(self):
        """Create system tray icon"""
        image = Image.new('RGB', (64, 64), color='blue')
        draw = ImageDraw.Draw(image)
        draw.ellipse([16, 16, 48, 48], fill='white')
        menu = pystray.Menu(
            pystray.MenuItem("Show Window", self.show_window),
            pystray.MenuItem("Capture Now", self.manual_capture),
            pystray.MenuItem("Start Recording", self.start_recording),
            pystray.MenuItem("Stop Recording", self.stop_recording),
            pystray.MenuItem("Stop Auto", self.stop_all_capture),
            pystray.MenuItem("Exit", self.exit_app)
        )
        self.tray_icon = pystray.Icon("ScreenshotApp", image, "Screenshot Tool", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def get_memory_usage(self):
        """Get current memory usage"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            return f"Memory: {memory_mb:.1f} MB"
        except:
            return "Memory: N/A"

    def cleanup(self):
        """Cleanup resources"""
        self.is_capturing = False
        self.save_settings()
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except:
                pass
        keyboard.unhook_all()
