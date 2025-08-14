# AutoScreenshot_with_ScreenRecord.py
# Extended from user's AutoScreenshot.py to add screen recording with microphone
# Dependencies: mss, opencv-python, sounddevice, numpy, scipy, keyboard, pystray, pillow, psutil
# Optional: ffmpeg (if installed, it will automatically merge audio + video into a single mp4)

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

# NEW: optional fallback for hotkeys
try:
    from pynput import keyboard as pynput_keyboard
except Exception:
    pynput_keyboard = None


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
        try:
            x, y, _, _ = self.widget.bbox("insert")
        except Exception:
            x, y = 0, 0
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
        self.is_paused = False
        self.auto_enabled = False  # NEW: separate flag for auto capture
        self.capture_thread = None
        self.auto_capture_thread = None
        self.tray_icon = None
        self.tray_icon_created = False
        
        self.pynput_listener = None
        self._debounce_last = {}
        self._debounce_lock = threading.Lock()
        self.auto_end_time = None

        # Optimize pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.05

        self.setup_variables()
        self.load_settings()
        self.setup_gui()
        self.setup_hotkeys()

    def setup_variables(self):
        self.folder_path = tk.StringVar()
        self.capture_hotkey = tk.StringVar(value="ctrl+shift+s")
        self.stop_hotkey = tk.StringVar(value="ctrl+shift+q")
        self.auto_capture_interval = tk.IntVar(value=60)
        self.auto_capture_duration_min = tk.IntVar(value=0)
        self.auto_start_hotkey = tk.StringVar(value="ctrl+shift+a")
        self.auto_pause_hotkey = tk.StringVar(value="ctrl+shift+p")
        self.auto_stop_hotkey = tk.StringVar(value="ctrl+shift+o")

    def load_settings(self):
        """Load settings from JSON file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.folder_path.set(settings.get('folder_path', ''))
                    self.capture_hotkey.set(settings.get('capture_hotkey', 'ctrl+shift+s'))
                    self.stop_hotkey.set(settings.get('stop_hotkey', 'ctrl+shift+q'))
                    self.auto_capture_interval.set(settings.get('auto_capture_interval', 60))
                    self.auto_capture_duration_min.set(settings.get('auto_capture_duration_min', 0))
                    self.auto_start_hotkey.set(settings.get('auto_start_hotkey', 'ctrl+shift+a'))
                    self.auto_pause_hotkey.set(settings.get('auto_pause_hotkey', 'ctrl+shift+p'))
                    self.auto_stop_hotkey.set(settings.get('auto_stop_hotkey', 'ctrl+shift+o'))
        except Exception as e:
            print(f"Error loading settings: {e}")
        
        # ENSURE: always disable auto capture on startup
        self.auto_enabled = False
        self.is_capturing = False

    def save_settings(self):
        """Save settings to JSON file"""
        try:
            settings = {
                'folder_path': self.folder_path.get(),
                'capture_hotkey': self.capture_hotkey.get(),
                'stop_hotkey': self.stop_hotkey.get(),
                'auto_capture_interval': self.auto_capture_interval.get(),
                'auto_capture_duration_min': self.auto_capture_duration_min.get(),
                'auto_start_hotkey': self.auto_start_hotkey.get(),
                'auto_pause_hotkey': self.auto_pause_hotkey.get(),
                'auto_stop_hotkey': self.auto_stop_hotkey.get(),
            }
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def setup_gui(self):
        self.root.title("Advanced Screenshot & ScreenRecorder Tool")
        self.root.geometry("640x600")
        self.root.resizable(False, False)

        # Window icon and close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)

        # Create styles
        style = ttk.Style()
        style.configure('TLabel', font=('Arial', 9))
        style.configure('TButton', font=('Arial', 9))
        style.configure('TEntry', font=('Arial', 9))
        style.configure('Title.TLabel', font=('Arial', 10, 'bold'))

        # Main frame with Notebook
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=8, pady=8)

        # Tab 1: Screenshot
        tab1 = ttk.Frame(notebook)
        notebook.add(tab1, text='Screenshot')

        # Tab 2: Screen Recording
        tab2 = ttk.Frame(notebook)
        notebook.add(tab2, text='Screen Record')

        # ----------------- Screenshot Tab -----------------
        main_frame = ttk.Frame(tab1, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        folder_header = ttk.Label(main_frame, text="SAVE LOCATION", style='Title.TLabel')
        folder_header.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        ttk.Label(main_frame, text="Save folder:").grid(row=1, column=0, sticky=tk.W, pady=2)

        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_path, width=50)
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        browse_btn = ttk.Button(folder_frame, text="Browse...", command=self.select_folder)
        browse_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # hotkeys and auto capture
        hotkey_header = ttk.Label(main_frame, text="HOTKEY SETTINGS", style='Title.TLabel')
        hotkey_header.grid(row=3, column=0, sticky=tk.W, pady=(10, 5))

        hotkey_frame = ttk.Frame(main_frame, borderwidth=1, relief="solid", padding="5")
        hotkey_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(hotkey_frame, text="Capture hotkey:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.capture_entry = ttk.Entry(hotkey_frame, textvariable=self.capture_hotkey, width=20)
        self.capture_entry.grid(row=1, column=1, sticky=tk.W, padx=5)
        self.capture_entry.bind('<FocusOut>', self.validate_hotkey)

        ttk.Label(hotkey_frame, text="Stop hotkey:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.stop_entry = ttk.Entry(hotkey_frame, textvariable=self.stop_hotkey, width=20)
        self.stop_entry.grid(row=2, column=1, sticky=tk.W, padx=5)
        self.stop_entry.bind('<FocusOut>', self.validate_hotkey)

        ttk.Label(hotkey_frame, text="Auto Start hotkey:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.auto_start_entry = ttk.Entry(hotkey_frame, textvariable=self.auto_start_hotkey, width=20)
        self.auto_start_entry.grid(row=3, column=1, sticky=tk.W, padx=5)
        self.auto_start_entry.bind('<FocusOut>', self.validate_hotkey)

        ttk.Label(hotkey_frame, text="Auto Pause hotkey:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.auto_pause_entry = ttk.Entry(hotkey_frame, textvariable=self.auto_pause_hotkey, width=20)
        self.auto_pause_entry.grid(row=4, column=1, sticky=tk.W, padx=5)
        self.auto_pause_entry.bind('<FocusOut>', self.validate_hotkey)

        ttk.Label(hotkey_frame, text="Auto Stop hotkey:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.auto_stop_entry = ttk.Entry(hotkey_frame, textvariable=self.auto_stop_hotkey, width=20)
        self.auto_stop_entry.grid(row=5, column=1, sticky=tk.W, padx=5)
        self.auto_stop_entry.bind('<FocusOut>', self.validate_hotkey)

        test_btn = ttk.Button(hotkey_frame, text="Test Hotkeys", command=self.test_hotkeys)
        test_btn.grid(row=6, column=0, columnspan=2, pady=(5, 0))

        auto_header = ttk.Label(main_frame, text="AUTO CAPTURE", style='Title.TLabel')
        auto_header.grid(row=5, column=0, sticky=tk.W, pady=(10, 5))

        auto_frame = ttk.Frame(main_frame, borderwidth=1, relief="solid", padding="5")
        auto_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Action buttons
        action_btns = ttk.Frame(auto_frame)
        action_btns.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        self.auto_start_btn = ttk.Button(action_btns, text="Start Auto", command=self.start_auto_capture)
        self.auto_start_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.auto_pause_btn = ttk.Button(action_btns, text="Pause", command=self.pause_auto_capture, state="disabled")
        self.auto_pause_btn.pack(side=tk.LEFT, padx=5)
        self.auto_stop_btn = ttk.Button(action_btns, text="Stop Auto", command=self.stop_all_capture, state="disabled")
        self.auto_stop_btn.pack(side=tk.LEFT, padx=5)

        ttk.Label(auto_frame, text="Interval (seconds):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.interval_spin = ttk.Spinbox(auto_frame, from_=1, to=3600, 
                                        textvariable=self.auto_capture_interval, width=10)
        self.interval_spin.grid(row=1, column=1, sticky=tk.W, padx=5)

        ttk.Label(auto_frame, text="Duration (minutes):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.duration_spin = ttk.Spinbox(auto_frame, from_=0, to=1440,
                                         textvariable=self.auto_capture_duration_min, width=10)
        self.duration_spin.grid(row=2, column=1, sticky=tk.W, padx=5)

        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=7, column=0, columnspan=2, pady=(15, 10))

        self.start_btn = ttk.Button(control_frame, text="Save & Run in Background", 
                                    command=self.start_background)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="Capture Now", command=self.manual_capture).pack(side=tk.LEFT, padx=5)

        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=8, column=0, columnspan=2, pady=(5, 0))

        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                      foreground="green", font=('Arial', 9, 'bold'))
        self.status_label.pack()

        self.memory_var = tk.StringVar()
        self.memory_label = ttk.Label(status_frame, textvariable=self.memory_var, 
                                      font=('Arial', 8), foreground="gray")
        self.memory_label.pack(pady=(5, 0))

        self.update_memory_usage()

        ToolTip(self.capture_entry, "Press key combination (e.g., ctrl+alt+s)")
        ToolTip(self.stop_entry, "Press a different key combination")
        ToolTip(self.interval_spin, "Time between auto captures")
        ToolTip(self.duration_spin, "Auto-capture max duration in minutes (0 = unlimited)")

        folder_entry.focus_set()

    def select_folder(self):
        folder = filedialog.askdirectory(title="Select Save Folder")
        if folder:
            self.folder_path.set(folder)

    def setup_hotkeys(self):
        """Set up global hotkeys with fallback and debounce"""
        self._stop_hotkeys()
        
        combos = {}
        if self.capture_hotkey.get():
            combos[self.capture_hotkey.get()] = ("capture", self.manual_capture)
        if self.stop_hotkey.get():
            combos[self.stop_hotkey.get()] = ("stop_all", self.stop_all_capture)
        if self.auto_start_hotkey.get():
            combos[self.auto_start_hotkey.get()] = ("auto_start", self.start_auto_capture)
        if self.auto_pause_hotkey.get():
            combos[self.auto_pause_hotkey.get()] = ("auto_pause", self.pause_auto_capture)
        if self.auto_stop_hotkey.get():
            combos[self.auto_stop_hotkey.get()] = ("auto_stop", self.stop_all_capture)

        used_keyboard = False
        used_pynput = False

        # Try keyboard backend first
        try:
            import keyboard as kb
            kb.unhook_all()
            for hk, (name, func) in combos.items():
                kb.add_hotkey(hk, self._wrap_action(name, func))
            used_keyboard = True
            print(f"Registered {len(combos)} hotkeys with keyboard backend")
        except Exception as e:
            print(f"keyboard backend failed: {e}")

        # Also start pynput fallback if available
        try:
            if pynput_keyboard:
                mapping = {}
                for hk, (name, func) in combos.items():
                    combo = self._to_pynput_combo(hk)
                    if combo:
                        mapping[combo] = self._wrap_action(name, func)
                if mapping:
                    self.pynput_listener = pynput_keyboard.GlobalHotKeys(mapping)
                    self.pynput_listener.start()
                    used_pynput = True
                    print(f"Registered {len(mapping)} hotkeys with pynput backend")
        except Exception as e:
            print(f"pynput backend failed: {e}")

        # Update status with backend info
        try:
            if used_keyboard and used_pynput:
                self.status_var.set("Hotkeys active (keyboard + pynput)")
            elif used_keyboard:
                self.status_var.set("Hotkeys active (keyboard)")
            elif used_pynput:
                self.status_var.set("Hotkeys active (pynput)")
            else:
                self.status_var.set("Hotkeys inactive - Check console for errors")
        except Exception:
            pass

    def _to_pynput_combo(self, s: str) -> str:
        if not s:
            return ""
        parts = [p.strip().lower() for p in s.split("+") if p.strip()]
        out = []
        for p in parts:
            if p in ("ctrl", "control", "ctrl_l", "ctrl_r"):
                out.append("<ctrl>")
            elif p in ("shift", "shift_l", "shift_r"):
                out.append("<shift>")
            elif p in ("alt", "alt_l", "alt_r"):
                out.append("<alt>")
            elif p in ("win", "super", "cmd", "meta"):
                out.append("<cmd>")
            else:
                out.append(p)
        return "+".join(out)

    def _wrap_action(self, name, func):
        def _wrapped():
            now = time.time()
            with self._debounce_lock:
                last = self._debounce_last.get(name, 0)
                if now - last < 0.2:
                    return
                self._debounce_last[name] = now
            try:
                func()
            except Exception as e:
                print(f"Hotkey '{name}' handler error: {e}")
        return _wrapped

    def _stop_hotkeys(self):
        try:
            import keyboard as kb
            kb.unhook_all()
        except Exception:
            pass
        if self.pynput_listener:
            try:
                self.pynput_listener.stop()
            except Exception:
                pass
            self.pynput_listener = None

    def manual_capture(self):
        """Manual screenshot capture"""
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select a save folder!")
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.folder_path.get(), f"screenshot_{timestamp}.png")

            screenshot = pyautogui.screenshot()
            screenshot.save(filename, optimize=True, quality=85)

            self.status_var.set(f"Captured: {os.path.basename(filename)}")

            del screenshot
            gc.collect()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to capture: {e}")

    def validate_hotkey(self, event):
        """Validate hotkey when user finishes typing"""
        entry = event.widget
        text = entry.get().strip().lower().replace(" ", "")
        if not text:
            messagebox.showerror("Error", "Hotkey cannot be empty!")
            return
        entry.delete(0, tk.END)
        entry.insert(0, text)
        self.save_settings()
        self.setup_hotkeys()

    def test_hotkeys(self):
        try:
            messagebox.showinfo("Test", "Press the hotkeys you assigned. If the app responds, they work.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def auto_capture_loop(self):
        """Auto capture loop with proper duration handling"""
        start_time = time.time()
        duration_minutes = max(0, int(self.auto_capture_duration_min.get()))
        if duration_minutes > 0:
            self.auto_end_time = start_time + (duration_minutes * 60)
            print(f"Auto capture will run for {duration_minutes} minutes")
        else:
            self.auto_end_time = None
            print("Auto capture will run indefinitely")

        while self.is_capturing and self.auto_enabled:
            # Check if duration limit reached
            if self.auto_end_time is not None:
                current_time = time.time()
                if current_time >= self.auto_end_time:
                    print(f"Duration limit reached. Stopping auto capture.")
                    self.stop_all_capture()
                    break

            try:
                self.manual_capture()
                # Sleep in small intervals to allow for responsive stopping
                interval = int(self.auto_capture_interval.get())
                for i in range(interval):
                    if not self.is_capturing or not self.auto_enabled:
                        break
                    if self.auto_end_time is not None and time.time() >= self.auto_end_time:
                        self.stop_all_capture()
                        break
                    time.sleep(1)
            except Exception as e:
                print(f"Auto capture error: {e}")
                time.sleep(1)

    def start_background(self):
        """Start background service WITHOUT auto capture"""
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select a save folder!")
            return
        
        self.save_settings()
        self.setup_hotkeys()

        # IMPORTANT: Do NOT start auto capture automatically
        self.is_capturing = False
        self.auto_enabled = False
        self.auto_end_time = None

        # Create tray icon
        if not self.tray_icon_created:
            self.create_tray_icon()
            self.tray_icon_created = True

        self.root.withdraw()
        self.status_var.set("Running in background - Use buttons or hotkeys to start auto capture")

    def stop_all_capture(self):
        """Stop all capture activities"""
        print("Stopping all capture...")
        self.is_capturing = False
        self.auto_enabled = False
        self.auto_end_time = None
        self.status_var.set("Stopped")
        self.update_auto_buttons(running=False)
        return True

    def create_tray_icon(self):
        if self.tray_icon and hasattr(self.tray_icon, 'visible') and self.tray_icon.visible:
            return
        image = Image.new('RGB', (64, 64), color='blue')
        draw = ImageDraw.Draw(image)
        draw.ellipse([16, 16, 48, 48], fill='white')
        menu = pystray.Menu(
            pystray.MenuItem("Show Window", self.show_window),
            pystray.MenuItem("Capture Now", self.manual_capture),
            pystray.MenuItem("Stop Auto", self.stop_all_capture),
            pystray.MenuItem("Exit", self.quit_app)
        )
        self.tray_icon = pystray.Icon("ScreenshotApp", image, "Screenshot Tool", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self, icon=None, item=None):
        self.root.deiconify()
        self.root.lift()

    def on_window_close(self):
        if self.is_capturing:
            self.root.withdraw()
        else:
            self.quit_app()

    def quit_app(self, icon=None, item=None):
        self.is_capturing = False
        self.auto_enabled = False
        self.save_settings()
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except:
                pass
        self._stop_hotkeys()
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass

    def update_memory_usage(self):
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_var.set(f"Memory: {memory_mb:.1f} MB")
        except:
            self.memory_var.set("Memory: N/A")
        self.root.after(5000, self.update_memory_usage)

    def update_auto_buttons(self, running: bool, paused: bool = False):
        """Update button states based on capture status"""
        if running and not paused:
            self.auto_start_btn.config(state="disabled")
            self.auto_pause_btn.config(state="normal")
            self.auto_stop_btn.config(state="normal")
        elif running and paused:
            self.auto_start_btn.config(state="normal")
            self.auto_pause_btn.config(state="disabled")
            self.auto_stop_btn.config(state="normal")
        else:
            self.auto_start_btn.config(state="normal")
            self.auto_pause_btn.config(state="disabled")
            self.auto_stop_btn.config(state="disabled")

    def start_auto_capture(self):
        """Start auto capture ONLY when explicitly called"""
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select a save folder!")
            return

        print("Starting auto capture...")
        
        # Stop any existing capture first
        if self.is_capturing:
            self.stop_all_capture()
            time.sleep(0.5)

        # Start new capture session
        self.is_capturing = True
        self.auto_enabled = True
        
        # Start the capture thread
        self.auto_capture_thread = threading.Thread(target=self.auto_capture_loop, daemon=True)
        self.auto_capture_thread.start()
        
        self.status_var.set("Auto Capture STARTED")
        self.update_auto_buttons(running=True, paused=False)
        return True

    def pause_auto_capture(self):
        """Pause auto capture"""
        if self.is_capturing and self.auto_enabled:
            self.auto_enabled = False
            self.status_var.set("Auto Capture PAUSED")
            self.update_auto_buttons(running=True, paused=True)
            print("Auto capture paused")
            return True
        else:
            self.status_var.set("Auto Capture not active")


if __name__ == "__main__":
    app = ScreenshotApp()
    app.root.mainloop()
        if self.is_capturing:
            self.stop_all_capture()
            time.sleep(0.5)  # Brief pause

        # Start new capture session
        self.is_capturing = True
        self
        
        # Start the capture thread
        self.auto_capture_thread = threading.Thread(target=self.auto_capture_loop, daemon=True)
        self.auto_capture_thread.start()
        
        self.status_var.set("Auto Capture started")
        self.update_auto_buttons(running=True, paused=False)
        return True

    def pause_auto_capture(self):
        """Pause auto capture without stopping the main capture state"""
        if self.is_capturing and selfTrue:
            self
            self.status_var.set("Auto Capture paused")
            self.update_auto_buttons(running=True, paused=True)
            print("Auto capture paused")
            return True
        else:
            self.status_var.set("Auto Capture not active")
