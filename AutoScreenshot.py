import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pyautogui
import threading
import json
import keyboard
import pystray
from PIL import Image, ImageDraw
from datetime import datetime
import gc
import psutil

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        self.widget.bind("<Enter>", self.showtip)
        self.widget.bind("<Leave>", self.hidetip)

    def showtip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                        font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self, event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

class ScreenshotApp:
    def __init__(self):
        self.root = tk.Tk()
        self.settings_file = "screenshot_settings.json"
        self.is_capturing = False
        self.capture_thread = None
        self.auto_capture_thread = None
        self.tray_icon = None
        
        # Optimize pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.1
        
        self.setup_variables()
        self.load_settings()
        self.setup_gui()
        self.setup_hotkeys()
        
    def setup_variables(self):
        self.folder_path = tk.StringVar()
        self.capture_hotkey = tk.StringVar(value="ctrl+shift+s")
        self.stop_hotkey = tk.StringVar(value="ctrl+shift+q")
        self.auto_capture_enabled = tk.BooleanVar()
        self.auto_capture_interval = tk.IntVar(value=60)
        
    def load_settings(self):
        """Load settings from JSON file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.folder_path.set(settings.get('folder_path', ''))
                    self.capture_hotkey.set(settings.get('capture_hotkey', 'ctrl+shift+s'))
                    self.stop_hotkey.set(settings.get('stop_hotkey', 'ctrl+shift+q'))
                    self.auto_capture_enabled.set(settings.get('auto_capture_enabled', False))
                    self.auto_capture_interval.set(settings.get('auto_capture_interval', 60))
        except Exception as e:
            print(f"Error loading settings: {e}")
            
    def save_settings(self):
        """Save settings to JSON file"""
        try:
            settings = {
                'folder_path': self.folder_path.get(),
                'capture_hotkey': self.capture_hotkey.get(),
                'stop_hotkey': self.stop_hotkey.get(),
                'auto_capture_enabled': self.auto_capture_enabled.get(),
                'auto_capture_interval': self.auto_capture_interval.get()
            }
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
            
    def setup_gui(self):
        self.root.title("Advanced Screenshot Tool")
        self.root.geometry("500x450")
        self.root.resizable(False, False)
        
        # Window icon and close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
        # Create styles
        style = ttk.Style()
        style.configure('TLabel', font=('Arial', 9))
        style.configure('TButton', font=('Arial', 9))
        style.configure('TEntry', font=('Arial', 9))
        style.configure('Title.TLabel', font=('Arial', 10, 'bold'))
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # ==================== Folder Selection ====================
        folder_header = ttk.Label(main_frame, text="SAVE LOCATION", style='Title.TLabel')
        folder_header.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(main_frame, text="Save folder:").grid(row=1, column=0, sticky=tk.W, pady=2)
        
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_path, width=50)
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(folder_frame, text="Browse...", command=self.select_folder)
        browse_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # ==================== Hotkey Settings ====================
        hotkey_header = ttk.Label(main_frame, text="HOTKEY SETTINGS", style='Title.TLabel')
        hotkey_header.grid(row=3, column=0, sticky=tk.W, pady=(10, 5))
        
        hotkey_frame = ttk.Frame(main_frame, borderwidth=1, relief="solid", padding="5")
        hotkey_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Hotkey input instructions
        help_text = "Format: Hold Ctrl/Shift/Alt + another key (e.g., ctrl+shift+s)"
        ttk.Label(hotkey_frame, text=help_text, foreground="blue", font=('Arial', 8)).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Capture hotkey
        ttk.Label(hotkey_frame, text="Capture hotkey:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.capture_entry = ttk.Entry(hotkey_frame, textvariable=self.capture_hotkey, width=20)
        self.capture_entry.grid(row=1, column=1, sticky=tk.W, padx=5)
        self.capture_entry.bind('<FocusOut>', self.validate_hotkey)
        
        # Stop hotkey
        ttk.Label(hotkey_frame, text="Stop hotkey:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.stop_entry = ttk.Entry(hotkey_frame, textvariable=self.stop_hotkey, width=20)
        self.stop_entry.grid(row=2, column=1, sticky=tk.W, padx=5)
        self.stop_entry.bind('<FocusOut>', self.validate_hotkey)
        
        # Test hotkeys button
        test_btn = ttk.Button(hotkey_frame, text="Test Hotkeys", command=self.test_hotkeys)
        test_btn.grid(row=3, column=0, columnspan=2, pady=(5, 0))
        
        # ==================== Auto Capture ====================
        auto_header = ttk.Label(main_frame, text="AUTO CAPTURE", style='Title.TLabel')
        auto_header.grid(row=5, column=0, sticky=tk.W, pady=(10, 5))
        
        auto_frame = ttk.Frame(main_frame, borderwidth=1, relief="solid", padding="5")
        auto_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Auto capture checkbox
        auto_capture_cb = ttk.Checkbutton(auto_frame, text="Enable auto capture", 
                                        variable=self.auto_capture_enabled)
        auto_capture_cb.grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        # Capture interval
        ttk.Label(auto_frame, text="Interval (seconds):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.interval_spin = ttk.Spinbox(auto_frame, from_=1, to=3600, 
                                    textvariable=self.auto_capture_interval, width=10)
        self.interval_spin.grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # ==================== Control Buttons ====================
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=7, column=0, columnspan=2, pady=(15, 10))
        
        self.start_btn = ttk.Button(control_frame, text="Save & Run in Background", 
                                command=self.start_background)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Capture Now", command=self.manual_capture).pack(side=tk.LEFT, padx=5)
        
        # ==================== Status Section ====================
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=8, column=0, columnspan=2, pady=(5, 0))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                    foreground="green", font=('Arial', 9, 'bold'))
        self.status_label.pack()
        
        # Memory usage
        self.memory_var = tk.StringVar()
        self.memory_label = ttk.Label(status_frame, textvariable=self.memory_var, 
                                    font=('Arial', 8), foreground="gray")
        self.memory_label.pack(pady=(5, 0))
        
        self.update_memory_usage()
        
        # Tooltips
        ToolTip(self.capture_entry, "Press key combination (e.g., ctrl+alt+s)")
        ToolTip(self.stop_entry, "Press a different key combination")
        ToolTip(self.interval_spin, "Time between auto captures")
        
        # Set default focus
        folder_entry.focus_set()
        
    def select_folder(self):
        folder = filedialog.askdirectory(title="Select Save Folder")
        if folder:
            self.folder_path.set(folder)
            
    def setup_hotkeys(self):
        """Set up global hotkeys"""
        try:
            # Remove old hotkeys
            keyboard.unhook_all()
            
            # Register new hotkeys
            keyboard.add_hotkey(self.capture_hotkey.get(), self.manual_capture)
            keyboard.add_hotkey(self.stop_hotkey.get(), self.stop_all_capture)
        except Exception as e:
            print(f"Error setting up hotkeys: {e}")
            
    def manual_capture(self):
        """Manual screenshot capture"""
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select a save folder!")
            return
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.folder_path.get(), f"screenshot_{timestamp}.png")
            
            # Optimized screenshot with lower quality to reduce lag
            screenshot = pyautogui.screenshot()
            screenshot.save(filename, optimize=True, quality=85)
            
            self.status_var.set(f"Captured: {os.path.basename(filename)}")
            
            # Clean up memory
            del screenshot
            gc.collect()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to capture: {e}")
            
    def validate_hotkey(self, event):
        """Validate hotkey when user finishes typing"""
        entry = event.widget
        var = self.capture_hotkey if entry == self.capture_entry else self.stop_hotkey
        
        hotkey = var.get().strip().lower()
        if not hotkey:
            messagebox.showerror("Error", "Hotkey cannot be empty!")
            var.set("ctrl+shift+s" if var == self.capture_hotkey else "ctrl+shift+q")
            return
        
        # Check special keys
        special_keys = ['ctrl', 'shift', 'alt', 'win', 'cmd']
        parts = hotkey.split('+')
        
        if len(parts) < 2:
            messagebox.showerror("Error", "Hotkey must have at least 2 keys (e.g., ctrl+a)")
            var.set("ctrl+shift+s" if var == self.capture_hotkey else "ctrl+shift+q")
            return
        
        for part in parts:
            if part not in special_keys and len(part) > 1 and not part.isdigit():
                messagebox.showerror("Error", f"Key '{part}' is invalid. Use single keys (a-z, 0-9) or special keys")
                var.set("ctrl+shift+s" if var == self.capture_hotkey else "ctrl+shift+q")
                return
        
        # Check for duplicates
        if self.capture_hotkey.get() == self.stop_hotkey.get():
            messagebox.showerror("Error", "Capture and stop hotkeys cannot be the same!")
            var.set("ctrl+shift+s" if var == self.capture_hotkey else "ctrl+shift+q")

    def test_hotkeys(self):
        """Test current hotkeys"""
        try:
            # Temporarily override functions for testing
            original_capture = self.manual_capture
            original_stop = self.stop_all_capture
            
            def test_capture():
                messagebox.showinfo("Test", f"Capture hotkey ({self.capture_hotkey.get()}) works!")
                
            def test_stop():
                messagebox.showinfo("Test", f"Stop hotkey ({self.stop_hotkey.get()}) works!")
                
            self.manual_capture = test_capture
            self.stop_all_capture = test_stop
            
            # Set up temporary hotkeys
            keyboard.unhook_all()
            keyboard.add_hotkey(self.capture_hotkey.get(), test_capture)
            keyboard.add_hotkey(self.stop_hotkey.get(), test_stop)
            
            messagebox.showinfo("Test", 
                            f"Testing hotkeys:\n"
                            f"Capture: {self.capture_hotkey.get()}\n"
                            f"Stop: {self.stop_hotkey.get()}\n\n"
                            f"Press the hotkeys to test. Click OK to finish testing.")
            
            # Restore original functions
            keyboard.unhook_all()
            self.manual_capture = original_capture
            self.stop_all_capture = original_stop
            self.setup_hotkeys()
            
        except Exception as e:
            messagebox.showerror("Error", f"Invalid hotkey: {str(e)}")
            
    def auto_capture_loop(self):
        """Auto capture loop"""
        while self.auto_capture_enabled.get() and self.is_capturing:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(self.folder_path.get(), f"auto_{timestamp}.png")
                
                screenshot = pyautogui.screenshot()
                screenshot.save(filename, optimize=True, quality=85)
                
                # Update status on main thread
                self.root.after(0, lambda: self.status_var.set(f"Auto: {os.path.basename(filename)}"))
                
                del screenshot
                gc.collect()
                
                # Sleep with status checking
                for _ in range(self.auto_capture_interval.get()):
                    if not self.auto_capture_enabled.get() or not self.is_capturing:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                print(f"Auto capture error: {e}")
                time.sleep(1)       
                
    def start_background(self):
        """Start running in background"""
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select a save folder!")
            return
            
        # Save settings
        self.save_settings()
        
        # Set up hotkeys
        self.setup_hotkeys()
        
        # Start capturing
        self.is_capturing = True
        
        if self.auto_capture_enabled.get():
            self.auto_capture_thread = threading.Thread(target=self.auto_capture_loop, daemon=True)
            self.auto_capture_thread.start()
            
        # Create system tray icon
        self.create_tray_icon()
        
        # Hide window
        self.root.withdraw()
        
        self.status_var.set("Running in background...")
        
    def stop_all_capture(self):
        """Stop all capturing"""
        self.is_capturing = False
        self.auto_capture_enabled.set(False)
        self.status_var.set("Stopped")
        
    def create_tray_icon(self):
        """Create system tray icon"""
        # Create simple icon
        image = Image.new('RGB', (64, 64), color='blue')
        draw = ImageDraw.Draw(image)
        draw.ellipse([16, 16, 48, 48], fill='white')
        
        # Tray menu
        menu = pystray.Menu(
            pystray.MenuItem("Show Window", self.show_window),
            pystray.MenuItem("Capture Now", self.manual_capture),
            pystray.MenuItem("Stop Auto", self.stop_all_capture),
            pystray.MenuItem("Exit", self.quit_app)
        )
        
        self.tray_icon = pystray.Icon("ScreenshotApp", image, "Screenshot Tool", menu)
        
        # Run tray in separate thread
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
        
    def show_window(self, icon=None, item=None):
        """Show the window"""
        self.root.deiconify()
        self.root.lift()
        
    def on_window_close(self):
        """Handle window close"""
        if self.is_capturing:
            # If capturing, hide window instead of exiting
            self.root.withdraw()
        else:
            self.quit_app()
            
    def quit_app(self, icon=None, item=None):
        """Quit application completely"""
        self.is_capturing = False
        self.save_settings()
        
        if self.tray_icon:
            self.tray_icon.stop()
            
        keyboard.unhook_all()
        self.root.quit()
        self.root.destroy()
        
    def update_memory_usage(self):
        """Update memory usage information"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_var.set(f"Memory: {memory_mb:.1f} MB")
        except:
            self.memory_var.set("Memory: N/A")
            
        # Update every 5 seconds
        self.root.after(5000, self.update_memory_usage)
        
    def run(self):
        """Run the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = ScreenshotApp()
    app.run()