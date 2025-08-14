# screenshot_engine.py
# Engine for screenshot functionality
# Dependencies: keyboard, pystray, pillow, psutil, mss

import os
import time
import mss
import threading
import json
import keyboard
import pystray
from PIL import Image, ImageDraw
from datetime import datetime
import gc
import psutil
import io  # Add for clipboard functionality


class ScreenshotEngine:
    def __init__(self):
        self.settings_file = "screenshot_settings.json"
        self.is_capturing = False
        self.capture_thread = None
        self.auto_capture_thread = None
        self.tray_icon = None
        
        self.tray_icon_created = False

        # Don't initialize MSS in __init__ - create per-thread instances instead
        self.main_sct = None

        # Settings dictionary - only screenshot related
        self.settings = {
            'folder_path': '',
            'capture_hotkey': 'ctrl+shift+s',
            'stop_hotkey': 'ctrl+shift+q',
            'auto_capture_enabled': False,
            'auto_capture_interval': 60,
            'auto_capture_duration_min': 0,
            'auto_start_hotkey': 'ctrl+shift+a',
            'auto_pause_hotkey': 'ctrl+shift+p',
            'auto_stop_hotkey': 'ctrl+shift+o',
            'capture_format': 'png',  # png, jpg, bmp
            'capture_quality': 95,    # for jpg format
            'capture_region': 'fullscreen',  # fullscreen, custom
            'custom_region': {'x': 0, 'y': 0, 'width': 1920, 'height': 1080},
            'monitor_index': 1,  # which monitor to capture (1 = primary)
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

    def get_mss_instance(self):
        """Get thread-safe MSS instance"""
        try:
            # Create a new MSS instance for each call to ensure thread safety
            return mss.mss()
        except Exception as e:
            print(f"Error creating MSS instance: {e}")
            return None

    def get_monitor_info(self):
        """Get information about available monitors"""
        sct = self.get_mss_instance()
        if not sct:
            return []
            
        try:
            monitors = sct.monitors
            monitor_info = []
            for i, monitor in enumerate(monitors):
                if i == 0:  # Skip the "All in One" monitor
                    continue
                monitor_info.append({
                    'index': i,
                    'width': monitor['width'],
                    'height': monitor['height'],
                    'left': monitor['left'],
                    'top': monitor['top']
                })
            return monitor_info
        except Exception as e:
            print(f"Error getting monitor info: {e}")
            return []
        finally:
            try:
                sct.close()
            except:
                pass

    def get_capture_region(self):
        """Get the region to capture based on settings"""
        sct = self.get_mss_instance()
        if not sct:
            return {'left': 0, 'top': 0, 'width': 1920, 'height': 1080}
            
        try:
            if self.settings['capture_region'] == 'custom':
                region = self.settings['custom_region']
                return {
                    'left': region['x'],
                    'top': region['y'],
                    'width': region['width'],
                    'height': region['height']
                }
            else:
                # Use specific monitor or primary monitor
                monitor_index = self.settings.get('monitor_index', 1)
                monitors = sct.monitors
                
                if monitor_index < len(monitors):
                    monitor = monitors[monitor_index]
                    return {
                        'left': monitor['left'],
                        'top': monitor['top'],
                        'width': monitor['width'],
                        'height': monitor['height']
                    }
                else:
                    # Fallback to primary monitor
                    monitor = monitors[1] if len(monitors) > 1 else monitors[0]
                    return {
                        'left': monitor['left'],
                        'top': monitor['top'],
                        'width': monitor['width'],
                        'height': monitor['height']
                    }
        except Exception as e:
            print(f"Error getting capture region: {e}")
            # Fallback to full screen
            return {'left': 0, 'top': 0, 'width': 1920, 'height': 1080}
        finally:
            try:
                sct.close()
            except:
                pass

    def save_to_clipboard(self, image):
        """Save image to clipboard"""
        try:
            # Method 1: Using win32clipboard (preferred)
            import win32clipboard
            from io import BytesIO
            
            # Convert PIL image to bitmap format for clipboard
            output = BytesIO()
            image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]  # Remove BMP header (first 14 bytes)
            output.close()
            
            # Copy to clipboard
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            
            print("Screenshot saved to clipboard")
            
        except ImportError:
            # Method 2: Fallback using tkinter clipboard (limited functionality)
            try:
                import tkinter as tk
                
                root = tk.Tk()
                root.withdraw()  # Hide the window
                
                # Save image info to clipboard as text
                root.clipboard_clear()
                root.clipboard_append(f"Screenshot captured at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                root.update()
                root.destroy()
                
                print("Screenshot info saved to clipboard (install pywin32 for image copy)")
                
            except Exception as e:
                print(f"Fallback clipboard method failed: {e}")
                
        except Exception as e:
            print(f"Error saving to clipboard: {e}")

    def manual_capture(self):
        """Manual screenshot capture with MSS - sharper and faster"""
        if not self.settings['folder_path']:
            print("Error: Please select a save folder!")
            return

        # Create thread-safe MSS instance
        sct = self.get_mss_instance()
        if not sct:
            self.update_status("Error: Could not initialize MSS")
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            capture_format = self.settings.get('capture_format', 'png').lower()
            filename = os.path.join(self.settings['folder_path'], f"screenshot_{timestamp}.{capture_format}")

            # Get capture region
            region = self.get_capture_region()
            
            # Take screenshot using MSS (much faster and sharper than pyautogui)
            screenshot_data = sct.grab(region)
            
            # Convert MSS screenshot to PIL Image
            screenshot = Image.frombytes("RGB", screenshot_data.size, screenshot_data.bgra, "raw", "BGRX")
            
            # Save to file with specified format and quality
            if capture_format == 'jpg' or capture_format == 'jpeg':
                screenshot = screenshot.convert('RGB')
                quality = self.settings.get('capture_quality', 95)
                screenshot.save(filename, format='JPEG', quality=quality, optimize=True)
            elif capture_format == 'bmp':
                screenshot.save(filename, format='BMP')
            else:  # Default to PNG
                screenshot.save(filename, format='PNG', optimize=True)
            
            # Save to clipboard
            self.save_to_clipboard(screenshot)

            # Get file size for status
            file_size = os.path.getsize(filename) / 1024  # KB
            self.update_status(f"Captured: {os.path.basename(filename)} ({file_size:.1f}KB) + clipboard")

            # Clean up memory
            del screenshot
            del screenshot_data
            gc.collect()

        except Exception as e:
            print(f"Failed to capture: {e}")
            self.update_status(f"Error: {e}")
        finally:
            # Always close the MSS instance
            try:
                sct.close()
            except:
                pass

    def capture_region(self, x, y, width, height):
        """Capture a specific region of the screen"""
        # Create thread-safe MSS instance
        sct = self.get_mss_instance()
        if not sct:
            self.update_status("Error: Could not initialize MSS")
            return None

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            capture_format = self.settings.get('capture_format', 'png').lower()
            filename = os.path.join(self.settings['folder_path'], f"region_{timestamp}.{capture_format}")

            # Define custom region
            region = {'left': x, 'top': y, 'width': width, 'height': height}
            
            # Take screenshot using MSS
            screenshot_data = sct.grab(region)
            
            # Convert to PIL Image
            screenshot = Image.frombytes("RGB", screenshot_data.size, screenshot_data.bgra, "raw", "BGRX")
            
            # Save to file
            if capture_format == 'jpg' or capture_format == 'jpeg':
                screenshot = screenshot.convert('RGB')
                quality = self.settings.get('capture_quality', 95)
                screenshot.save(filename, format='JPEG', quality=quality, optimize=True)
            elif capture_format == 'bmp':
                screenshot.save(filename, format='BMP')
            else:
                screenshot.save(filename, format='PNG', optimize=True)
            
            # Save to clipboard
            self.save_to_clipboard(screenshot)

            file_size = os.path.getsize(filename) / 1024
            self.update_status(f"Region captured: {os.path.basename(filename)} ({file_size:.1f}KB)")

            # Clean up
            del screenshot
            del screenshot_data
            gc.collect()

            return filename

        except Exception as e:
            print(f"Failed to capture region: {e}")
            self.update_status(f"Region capture error: {e}")
            return None
        finally:
            # Always close the MSS instance
            try:
                sct.close()
            except:
                pass

    def start_auto_capture(self):
        """Start auto capture with duration support"""
        if not self.settings['folder_path']:
            print("Error: Please select a save folder!")
            return False

        self.settings['auto_capture_enabled'] = True
        self.is_capturing = True

        # Start auto capture thread
        self.auto_capture_thread = threading.Thread(target=self.auto_capture_loop_with_duration, daemon=True)
        self.auto_capture_thread.start()
        
        duration = self.settings.get('auto_capture_duration_min', 0)
        if duration > 0:
            self.update_status(f"Auto-capture started (MSS engine) - {duration} min duration")
        else:
            self.update_status("Auto-capture started (MSS engine) - unlimited")
        
        return True

    def auto_capture_loop_with_duration(self):
        """Auto capture loop with duration limit support"""
        start_time = time.time()
        duration_seconds = self.settings.get('auto_capture_duration_min', 0) * 60
        
        while self.settings['auto_capture_enabled'] and self.is_capturing:
            try:
                # Check duration limit
                if duration_seconds > 0:
                    elapsed = time.time() - start_time
                    if elapsed >= duration_seconds:
                        self.settings['auto_capture_enabled'] = False
                        self.update_status("Auto-capture completed - duration limit reached")
                        break
                
                # Take screenshot (this will create its own MSS instance)
                self.manual_capture()
                
                # Wait for the specified interval with interruption check
                interval = self.settings['auto_capture_interval']
                for i in range(interval):
                    if not self.settings['auto_capture_enabled'] or not self.is_capturing:
                        break
                    time.sleep(1)
                    
                    # Update status with remaining time if duration is set
                    if duration_seconds > 0 and i % 10 == 0:  # Update every 10 seconds
                        elapsed = time.time() - start_time
                        remaining = max(0, duration_seconds - elapsed)
                        if remaining > 0:
                            remaining_min = remaining / 60
                            self.update_status(f"Auto-capturing (MSS) - {remaining_min:.1f} min remaining")
                    
            except Exception as e:
                print(f"Auto capture error: {e}")
                time.sleep(1)

    def auto_capture_loop(self):
        """Auto capture loop running in background thread with clipboard support"""
        while self.settings['auto_capture_enabled'] and self.is_capturing:
            try:
                # Use manual_capture which creates its own MSS instance
                self.manual_capture()
                
                # Wait for the specified interval
                for _ in range(self.settings['auto_capture_interval']):
                    if not self.settings['auto_capture_enabled'] or not self.is_capturing:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                print(f"Auto capture error: {e}")
                time.sleep(1)

    def start_background_capture(self):
        """Start background capture process with MSS"""
        if not self.settings['folder_path']:
            print("Error: Please select a save folder!")
            return False

        self.save_settings()
        self.setup_hotkeys()
        self.is_capturing = True

        # Start auto capture thread if enabled
        if self.settings['auto_capture_enabled']:
            self.auto_capture_thread = threading.Thread(target=self.auto_capture_loop, daemon=True)
            self.auto_capture_thread.start()
            self.update_status("Auto-capture started (MSS engine - high quality)")
        else:
            self.update_status("Background capture ready (MSS engine - high quality)")

        # Create tray icon only once
        if not self.tray_icon_created:
            self.create_tray_icon()
            self.tray_icon_created = True

        return True


    def stop_all_capture(self):
        """Stop all capture processes"""
        self.is_capturing = False
        self.settings['auto_capture_enabled'] = False
        self.update_status("All capture processes stopped")

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
            pystray.MenuItem("Capture Now (MSS + Clipboard)", self.manual_capture),
            pystray.MenuItem("Start Recording", self.start_recording),
            pystray.MenuItem("Stop Recording", self.stop_recording),
            pystray.MenuItem("Stop Auto Capture", self.stop_all_capture),
            pystray.MenuItem("Exit", self.exit_app)
        )
        self.tray_icon = pystray.Icon("ScreenshotApp", image, "Screenshot Tool (MSS)", menu)
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
        
        # MSS instances are created per-call and closed immediately, no cleanup needed
        
        if self.tray_icon:
            try:
                self.tray_icon.stop()
                self.tray_icon = None
                self.tray_icon_created = False
            except:
                pass
        keyboard.unhook_all()