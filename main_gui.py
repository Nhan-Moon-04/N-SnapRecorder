# main_gui.py
# GUI for Advanced Screenshot & ScreenRecorder Tool
# This file handles the user interface and communicates with screenshot_engine.py and recording_controller.py

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from screenshot_engine import ScreenshotEngine
from recording_controller import RecordingController
import keyboard  # for sending the configured auto hotkeys via buttons


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
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffcc",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Segoe UI", 8),
        )
        label.pack(ipadx=3, ipady=2)

    def hidetip(self, event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


class ScreenshotGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.screenshot_engine = ScreenshotEngine()
        self.recording_controller = RecordingController()
        
        # Add tray icon tracking flag
        self.tray_icon_created = False

        # Setup GUI variables from engine settings
        self.setup_variables()
        self.setup_gui()

        # Set engine callbacks for UI updates
        self.screenshot_engine.set_callbacks(
            status_callback=self.update_status,
            memory_callback=self.update_memory,
        )

        self.recording_controller.set_status_callback(self.update_rec_status)

        # Set tray icon callbacks for screenshot engine
        self.screenshot_engine.set_tray_callbacks(
            show_window_callback=self.show_window,
            start_recording_callback=self.start_recording,
            stop_recording_callback=self.stop_recording,
            exit_callback=self.quit_app,
        )

    def setup_variables(self):
        """Setup tkinter variables and sync with engine settings"""
        # Screenshot vars
        self.folder_path = tk.StringVar()
        self.capture_hotkey = tk.StringVar()
        self.stop_hotkey = tk.StringVar()
        self.auto_capture_interval = tk.IntVar()
        self.auto_capture_duration_min = tk.IntVar()
        self.auto_start_hotkey = tk.StringVar()
        self.auto_pause_hotkey = tk.StringVar()
        self.auto_stop_hotkey = tk.StringVar()

        # Recording vars
        self.record_hotkey = tk.StringVar()
        self.stop_record_hotkey = tk.StringVar()
        self.record_fps = tk.IntVar()
        self.record_format = tk.StringVar()
        self.record_area_mode = tk.StringVar()
        self.custom_x = tk.IntVar()
        self.custom_y = tk.IntVar()
        self.custom_w = tk.IntVar()
        self.custom_h = tk.IntVar()
        self.record_audio_enabled = tk.BooleanVar()
        self.audio_samplerate = tk.IntVar()
        self.audio_channels = tk.IntVar()

        # Load settings from engine
        self.sync_variables_from_engine()

        # Bind variables to engine updates
        self.bind_variables_to_engine()

    def sync_variables_from_engine(self):
        """Sync GUI variables with engine settings"""
        # Screenshot settings
        self.folder_path.set(self.screenshot_engine.get_setting("folder_path"))
        self.capture_hotkey.set(self.screenshot_engine.get_setting("capture_hotkey"))
        self.stop_hotkey.set(self.screenshot_engine.get_setting("stop_hotkey"))
        self.auto_capture_interval.set(
            self.screenshot_engine.get_setting("auto_capture_interval")
        )
        self.auto_capture_duration_min.set(
            self.screenshot_engine.get_setting("auto_capture_duration_min") or 0
        )
        self.auto_start_hotkey.set(
            self.screenshot_engine.get_setting("auto_start_hotkey") or "ctrl+shift+a"
        )
        self.auto_pause_hotkey.set(
            self.screenshot_engine.get_setting("auto_pause_hotkey") or "ctrl+shift+p"
        )
        self.auto_stop_hotkey.set(
            self.screenshot_engine.get_setting("auto_stop_hotkey") or "ctrl+shift+o"
        )

        # Recording settings
        self.record_hotkey.set(self.recording_controller.get_setting("record_hotkey"))
        self.stop_record_hotkey.set(
            self.recording_controller.get_setting("stop_record_hotkey")
        )
        self.record_fps.set(self.recording_controller.get_setting("record_fps"))
        self.record_format.set(self.recording_controller.get_setting("record_format"))
        self.record_area_mode.set(
            self.recording_controller.get_setting("record_area_mode")
        )
        self.custom_x.set(self.recording_controller.get_setting("custom_x"))
        self.custom_y.set(self.recording_controller.get_setting("custom_y"))
        self.custom_w.set(self.recording_controller.get_setting("custom_w"))
        self.custom_h.set(self.recording_controller.get_setting("custom_h"))
        self.record_audio_enabled.set(
            self.recording_controller.get_setting("record_audio_enabled")
        )
        self.audio_samplerate.set(
            self.recording_controller.get_setting("audio_samplerate")
        )
        self.audio_channels.set(
            self.recording_controller.get_setting("audio_channels")
        )

    def bind_variables_to_engine(self):
        """Bind GUI variables to update engine settings"""
        # Screenshot engine bindings
        self.folder_path.trace_add("write", lambda *args: self._update_folder_path())
        self.capture_hotkey.trace_add(
            "write",
            lambda *args: self._update_hotkey("capture_hotkey", self.capture_hotkey.get())
        )
        self.stop_hotkey.trace_add(
            "write",
            lambda *args: self._update_hotkey("stop_hotkey", self.stop_hotkey.get())
        )
        
        
        self.auto_capture_interval.trace_add(
            "write",
            lambda *args: self.screenshot_engine.update_setting(
                "auto_capture_interval", self.auto_capture_interval.get()
            ),
        )
        self.auto_capture_duration_min.trace_add(
            "write",
            lambda *args: self.screenshot_engine.update_setting(
                "auto_capture_duration_min", self.auto_capture_duration_min.get()
            ),
        )
        self.auto_start_hotkey.trace_add(
            "write",
            lambda *args: self._update_hotkey("auto_start_hotkey", self.auto_start_hotkey.get())
        )
        self.auto_pause_hotkey.trace_add(
            "write",
            lambda *args: self._update_hotkey("auto_pause_hotkey", self.auto_pause_hotkey.get())
        )
        self.auto_stop_hotkey.trace_add(
            "write",
            lambda *args: self._update_hotkey("auto_stop_hotkey", self.auto_stop_hotkey.get())
        )

        # Recording controller bindings
        self.record_hotkey.trace_add(
            "write",
            lambda *args: self.recording_controller.update_setting(
                "record_hotkey", self.record_hotkey.get()
            ),
        )
        self.stop_record_hotkey.trace_add(
            "write",
            lambda *args: self.recording_controller.update_setting(
                "stop_record_hotkey", self.stop_record_hotkey.get()
            ),
        )
        self.record_fps.trace_add(
            "write",
            lambda *args: self.recording_controller.update_setting(
                "record_fps", self.record_fps.get()
            ),
        )
        self.record_format.trace_add(
            "write",
            lambda *args: self.recording_controller.update_setting(
                "record_format", self.record_format.get()
            ),
        )
        self.record_area_mode.trace_add(
            "write",
            lambda *args: self.recording_controller.update_setting(
                "record_area_mode", self.record_area_mode.get()
            ),
        )
        self.custom_x.trace_add(
            "write",
            lambda *args: self.recording_controller.update_setting(
                "custom_x", self.custom_x.get()
            ),
        )
        self.custom_y.trace_add(
            "write",
            lambda *args: self.recording_controller.update_setting(
                "custom_y", self.custom_y.get()
            ),
        )
        self.custom_w.trace_add(
            "write",
            lambda *args: self.recording_controller.update_setting(
                "custom_w", self.custom_w.get()
            ),
        )
        self.custom_h.trace_add(
            "write",
            lambda *args: self.recording_controller.update_setting(
                "custom_h", self.custom_h.get()
            ),
        )
        self.record_audio_enabled.trace_add(
            "write",
            lambda *args: self.recording_controller.update_setting(
                "record_audio_enabled", self.record_audio_enabled.get()
            ),
        )
        self.audio_samplerate.trace_add(
            "write",
            lambda *args: self.recording_controller.update_setting(
                "audio_samplerate", self.audio_samplerate.get()
            ),
        )
        self.audio_channels.trace_add(
            "write",
            lambda *args: self.recording_controller.update_setting(
                "audio_channels", self.audio_channels.get()
            ),
        )

    def _update_folder_path(self):
        """Update folder path in both engines"""
        folder = self.folder_path.get()
        self.screenshot_engine.update_setting("folder_path", folder)
        self.recording_controller.update_setting("folder_path", folder)

    def _update_hotkey(self, setting_name, value):
        """Update hotkey setting and refresh hotkey registration"""
        self.screenshot_engine.update_setting(setting_name, value)
        # Refresh hotkeys in engine
        if hasattr(self.screenshot_engine, 'setup_hotkeys'):
            self.screenshot_engine.setup_hotkeys()
        
        # Bind hotkeys to GUI buttons directly
        self._bind_hotkeys_to_buttons()

    def _bind_hotkeys_to_buttons(self):
        """Bind hotkeys directly to GUI button functions"""
        try:
            import keyboard as kb
            
            # Clear existing hotkeys
            kb.unhook_all()
            
            # Bind hotkeys to button functions
            if self.capture_hotkey.get():
                kb.add_hotkey(self.capture_hotkey.get(), self.manual_capture)
            
            if self.stop_hotkey.get():
                kb.add_hotkey(self.stop_hotkey.get(), self.on_auto_stop_btn)
            
            if self.auto_start_hotkey.get():
                kb.add_hotkey(self.auto_start_hotkey.get(), self.on_auto_start_btn)
            
            if self.auto_pause_hotkey.get():
                kb.add_hotkey(self.auto_pause_hotkey.get(), self.on_auto_pause_btn)
            
            if self.auto_stop_hotkey.get():
                kb.add_hotkey(self.auto_stop_hotkey.get(), self.on_auto_stop_btn)
                
            # Recording hotkeys
            if self.record_hotkey.get():
                kb.add_hotkey(self.record_hotkey.get(), self.start_recording)
            
            if self.stop_record_hotkey.get():
                kb.add_hotkey(self.stop_record_hotkey.get(), self.stop_recording)
                
        except Exception as e:
            print(f"Hotkey binding error: {e}")

    def setup_gui(self):
        """Setup the main GUI with modern design"""
        # Window configuration
        self.root.title("Advanced Screenshot & Screen Recorder Tool")
        self.root.geometry("900x650")
        self.root.resizable(True, True)
        self.root.configure(bg="#f0f0f0")
        
        # Set minimum size
        self.root.minsize(850, 600)

        # Window icon and close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)

        # Configure ttk style with clam theme
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure custom styles
        style.configure("Title.TLabel", 
                       font=("Segoe UI", 11, "bold"),
                       foreground="#2c3e50",
                       background="#f0f0f0")
        
        style.configure("Heading.TLabel", 
                       font=("Segoe UI", 9, "bold"),
                       foreground="#34495e",
                       background="#f0f0f0")
        
        style.configure("TLabel", 
                       font=("Segoe UI", 8),
                       background="#f0f0f0")
        
        style.configure("TButton", 
                       font=("Segoe UI", 8),
                       padding=(6, 3))
        
        style.configure("TEntry", 
                       font=("Segoe UI", 8),
                       fieldbackground="white")
        
        style.configure("TCombobox", 
                       font=("Segoe UI", 8),
                       fieldbackground="white")
        
        style.configure("Action.TButton", 
                       font=("Segoe UI", 8, "bold"),
                       padding=(8, 4))
        
        style.configure("Status.TLabel", 
                       font=("Segoe UI", 8, "bold"),
                       foreground="#27ae60")

        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=8)

        # Title label
        title_label = ttk.Label(main_container, 
                               text="Advanced Screenshot & Screen Recorder Tool", 
                               style="Title.TLabel")
        title_label.pack(pady=(0, 10))

        # Create Notebook for tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill="both", expand=True)

        # Tab 1: Screenshot
        self.screenshot_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.screenshot_tab, text="📸 Screenshot")

        # Tab 2: Screen Recording
        self.recording_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.recording_tab, text="🎥 Screen Recording")

        # Setup tabs
        self.setup_screenshot_tab()
        self.setup_recording_tab()

    def setup_screenshot_tab(self):
        """Setup the screenshot tab with horizontal layout"""
        main_frame = ttk.Frame(self.screenshot_tab)
        main_frame.pack(fill="both", expand=True, padx=15, pady=10)

        # Top row - Save Location (full width)
        location_frame = ttk.LabelFrame(main_frame, text="📁 Save Location", padding="10")
        location_frame.pack(fill="x", pady=(0, 8))

        folder_container = ttk.Frame(location_frame)
        folder_container.pack(fill="x")
        folder_container.columnconfigure(0, weight=1)

        self.folder_entry = ttk.Entry(folder_container, textvariable=self.folder_path, width=80)
        self.folder_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        browse_btn = ttk.Button(folder_container, text="Browse...", command=self.select_folder)
        browse_btn.grid(row=0, column=1)

        # Middle section - Two columns layout
        middle_frame = ttk.Frame(main_frame)
        middle_frame.pack(fill="both", expand=True, pady=(0, 8))
        middle_frame.columnconfigure(0, weight=1)
        middle_frame.columnconfigure(1, weight=1)

        # Left column - Hotkey Settings
        hotkey_frame = ttk.LabelFrame(middle_frame, text="⌨️ Hotkey Settings", padding="10")
        hotkey_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        # Manual capture section
        ttk.Label(hotkey_frame, text="Manual Capture:", style="Heading.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))

        ttk.Label(hotkey_frame, text="Capture:").grid(row=1, column=0, sticky="w", pady=2)
        self.capture_entry = ttk.Entry(hotkey_frame, textvariable=self.capture_hotkey, width=20)
        self.capture_entry.grid(row=1, column=1, sticky="w", padx=(5, 0), pady=2)
        self.capture_entry.bind("<FocusOut>", self.validate_hotkey)

        ttk.Label(hotkey_frame, text="Stop:").grid(row=2, column=0, sticky="w", pady=2)
        self.stop_entry = ttk.Entry(hotkey_frame, textvariable=self.stop_hotkey, width=20)
        self.stop_entry.grid(row=2, column=1, sticky="w", padx=(5, 0), pady=2)
        self.stop_entry.bind("<FocusOut>", self.validate_hotkey)

        # Auto capture section
        ttk.Label(hotkey_frame, text="Auto Capture:", style="Heading.TLabel").grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(10, 5))

        ttk.Label(hotkey_frame, text="Start:").grid(row=4, column=0, sticky="w", pady=2)
        self.auto_start_entry = ttk.Entry(hotkey_frame, textvariable=self.auto_start_hotkey, width=20)
        self.auto_start_entry.grid(row=4, column=1, sticky="w", padx=(5, 0), pady=2)
        self.auto_start_entry.bind("<FocusOut>", self.validate_hotkey)

        ttk.Label(hotkey_frame, text="Pause:").grid(row=5, column=0, sticky="w", pady=2)
        self.auto_pause_entry = ttk.Entry(hotkey_frame, textvariable=self.auto_pause_hotkey, width=20)
        self.auto_pause_entry.grid(row=5, column=1, sticky="w", padx=(5, 0), pady=2)
        self.auto_pause_entry.bind("<FocusOut>", self.validate_hotkey)

        ttk.Label(hotkey_frame, text="Stop:").grid(row=6, column=0, sticky="w", pady=2)
        self.auto_stop_entry = ttk.Entry(hotkey_frame, textvariable=self.auto_stop_hotkey, width=20)
        self.auto_stop_entry.grid(row=6, column=1, sticky="w", padx=(5, 0), pady=2)
        self.auto_stop_entry.bind("<FocusOut>", self.validate_hotkey)

        test_btn = ttk.Button(hotkey_frame, text="🧪 Test Hotkeys", command=self.test_hotkeys)
        test_btn.grid(row=7, column=0, columnspan=2, pady=(10, 0))

        # Right column - Auto Capture Settings
        auto_frame = ttk.LabelFrame(middle_frame, text="🔄 Auto Capture Settings", padding="10")
        auto_frame.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

        # Control buttons
        ttk.Label(auto_frame, text="Control Actions:", style="Heading.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        action_frame = ttk.Frame(auto_frame)
        action_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self.auto_start_btn = ttk.Button(action_frame, text="▶️ Start", 
                                        command=self.on_auto_start_btn, style="Action.TButton")
        self.auto_start_btn.pack(side="left", padx=(0, 5))

        self.auto_pause_btn = ttk.Button(action_frame, text="⏸️ Pause", 
                                        command=self.on_auto_pause_btn, 
                                        state="disabled", style="Action.TButton")
        self.auto_pause_btn.pack(side="left", padx=(0, 5))

        self.auto_stop_btn = ttk.Button(action_frame, text="⏹️ Stop", 
                                       command=self.on_auto_stop_btn, 
                                       state="disabled", style="Action.TButton")
        self.auto_stop_btn.pack(side="left")

        # Settings
        ttk.Label(auto_frame, text="Timing Settings:", style="Heading.TLabel").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(10, 5))

        ttk.Label(auto_frame, text="Interval (sec):").grid(row=3, column=0, sticky="w", pady=3)
        self.interval_spin = ttk.Spinbox(auto_frame, from_=1, to=3600, 
                                        textvariable=self.auto_capture_interval, width=12)
        self.interval_spin.grid(row=3, column=1, sticky="w", padx=(5, 0), pady=3)

        ttk.Label(auto_frame, text="Duration (min):").grid(row=4, column=0, sticky="w", pady=3)
        self.duration_spin = ttk.Spinbox(auto_frame, from_=0, to=1440, 
                                        textvariable=self.auto_capture_duration_min, width=12)
        self.duration_spin.grid(row=4, column=1, sticky="w", padx=(5, 0), pady=3)

        ttk.Label(auto_frame, text="(0=unlimited)", font=("Segoe UI", 7), foreground="#7f8c8d").grid(
            row=5, column=1, sticky="w", padx=(5, 0))

        # Bottom section - Actions and Status
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill="x", pady=(0, 5))
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.columnconfigure(1, weight=1)

        # Main Actions
        actions_frame = ttk.LabelFrame(bottom_frame, text="🚀 Main Actions", padding="10")
        actions_frame.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        control_buttons = ttk.Frame(actions_frame)
        control_buttons.pack()

        self.bg_btn = ttk.Button(control_buttons, text="💾 Save & Run Background", 
                                command=self.save_and_run_background, style="Action.TButton")
        self.bg_btn.pack(side="left", padx=(0, 9))

        capture_now_btn = ttk.Button(control_buttons, text="📷 Capture Now", 
                                    command=self.manual_capture, style="Action.TButton")
        capture_now_btn.pack(side="left")

        # Status Section
        status_frame = ttk.LabelFrame(bottom_frame, text="📊 Status & Information", padding="10")
        status_frame.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.show_memory_var = tk.BooleanVar(value=True)
        memory_check = ttk.Checkbutton(status_frame, text="Show Memory", 
                                      variable=self.show_memory_var)
        memory_check.pack(anchor="w", pady=(0, 5))

        status_info = ttk.Frame(status_frame)
        status_info.pack(fill="x")

        ttk.Label(status_info, text="Status:").pack(side="left")
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(status_info, textvariable=self.status_var, 
                                     style="Status.TLabel")
        self.status_label.pack(side="left", padx=(5, 10))

        self.memory_var = tk.StringVar()
        self.memory_label = ttk.Label(status_info, textvariable=self.memory_var, 
                                     font=("Segoe UI", 7), foreground="#7f8c8d")
        self.memory_label.pack(side="left")

        # Add tooltips
        self.add_screenshot_tooltips()

    def setup_recording_tab(self):
        """Setup the recording tab with horizontal layout"""
        main_frame = ttk.Frame(self.recording_tab)
        main_frame.pack(fill="both", expand=True, padx=15, pady=10)

        # Top row - Save Location (full width)
        location_frame = ttk.LabelFrame(main_frame, text="📁 Save Location", padding="10")
        location_frame.pack(fill="x", pady=(0, 8))

        folder_container = ttk.Frame(location_frame)
        folder_container.pack(fill="x")
        folder_container.columnconfigure(0, weight=1)

        rec_folder_entry = ttk.Entry(folder_container, textvariable=self.folder_path, width=80)
        rec_folder_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        rec_browse_btn = ttk.Button(folder_container, text="Browse...", command=self.select_folder)
        rec_browse_btn.grid(row=0, column=1)

        # Middle section - Three columns layout
        middle_frame = ttk.Frame(main_frame)
        middle_frame.pack(fill="both", expand=True, pady=(0, 8))
        middle_frame.columnconfigure(0, weight=1)
        middle_frame.columnconfigure(1, weight=1)
        middle_frame.columnconfigure(2, weight=1)

        # Left column - Hotkeys & Video Settings
        left_frame = ttk.Frame(middle_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        # Hotkey Settings
        rec_hotkey_frame = ttk.LabelFrame(left_frame, text="⌨️ Recording Hotkeys", padding="10")
        rec_hotkey_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(rec_hotkey_frame, text="Start Recording:").grid(row=0, column=0, sticky="w", pady=3)
        self.rec_hot_entry = ttk.Entry(rec_hotkey_frame, textvariable=self.record_hotkey, width=18)
        self.rec_hot_entry.grid(row=0, column=1, sticky="w", padx=(5, 0), pady=3)
        self.rec_hot_entry.bind("<FocusOut>", self.validate_hotkey)

        ttk.Label(rec_hotkey_frame, text="Stop Recording:").grid(row=1, column=0, sticky="w", pady=3)
        self.rec_stop_entry = ttk.Entry(rec_hotkey_frame, textvariable=self.stop_record_hotkey, width=18)
        self.rec_stop_entry.grid(row=1, column=1, sticky="w", padx=(5, 0), pady=3)
        self.rec_stop_entry.bind("<FocusOut>", self.validate_hotkey)

        # Video Settings
        video_frame = ttk.LabelFrame(left_frame, text="🎬 Video Settings", padding="10")
        video_frame.pack(fill="x")

        ttk.Label(video_frame, text="FPS:").grid(row=0, column=0, sticky="w", pady=3)
        fps_spin = ttk.Spinbox(video_frame, from_=5, to=120, textvariable=self.record_fps, width=12)
        fps_spin.grid(row=0, column=1, sticky="w", padx=(5, 0), pady=3)

        ttk.Label(video_frame, text="Format:").grid(row=1, column=0, sticky="w", pady=3)
        fmt_combo = ttk.Combobox(video_frame, values=["mp4", "avi", "mkv"], 
                                textvariable=self.record_format, width=10, state="readonly")
        fmt_combo.grid(row=1, column=1, sticky="w", padx=(5, 0), pady=3)

        # Middle column - Recording Area
        area_frame = ttk.LabelFrame(middle_frame, text="📐 Recording Area", padding="10")
        area_frame.grid(row=0, column=1, sticky="nsew", padx=(4, 4))

        ttk.Label(area_frame, text="Mode:").grid(row=0, column=0, sticky="w", pady=3)
        area_combo = ttk.Combobox(area_frame, values=["fullscreen", "custom"], 
                                 textvariable=self.record_area_mode, width=12, state="readonly")
        area_combo.grid(row=0, column=1, sticky="w", padx=(5, 0), pady=3)

        ttk.Label(area_frame, text="Custom Area:", style="Heading.TLabel").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(10, 5))

        custom_grid = ttk.Frame(area_frame)
        custom_grid.grid(row=2, column=0, columnspan=2, sticky="w", pady=3)

        ttk.Label(custom_grid, text="X:").grid(row=0, column=0, sticky="w")
        ttk.Entry(custom_grid, textvariable=self.custom_x, width=6).grid(row=0, column=1, padx=(2, 8))
        ttk.Label(custom_grid, text="Y:").grid(row=0, column=2, sticky="w")
        ttk.Entry(custom_grid, textvariable=self.custom_y, width=6).grid(row=0, column=3, padx=(2, 0))

        ttk.Label(custom_grid, text="W:").grid(row=1, column=0, sticky="w", pady=(5, 0))
        ttk.Entry(custom_grid, textvariable=self.custom_w, width=6).grid(row=1, column=1, padx=(2, 8), pady=(5, 0))
        ttk.Label(custom_grid, text="H:").grid(row=1, column=2, sticky="w", pady=(5, 0))
        ttk.Entry(custom_grid, textvariable=self.custom_h, width=6).grid(row=1, column=3, padx=(2, 0), pady=(5, 0))

        # Right column - Audio Settings & Controls
        right_frame = ttk.Frame(middle_frame)
        right_frame.grid(row=0, column=2, sticky="nsew", padx=(4, 0))

        # Audio Settings
        audio_frame = ttk.LabelFrame(right_frame, text="🎤 Audio Settings", padding="10")
        audio_frame.pack(fill="x", pady=(0, 8))

        audio_check = ttk.Checkbutton(audio_frame, text="Record Audio", 
                                     variable=self.record_audio_enabled)
        audio_check.pack(anchor="w", pady=(0, 5))

        audio_grid = ttk.Frame(audio_frame)
        audio_grid.pack(fill="x")

        ttk.Label(audio_grid, text="Sample Rate:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Spinbox(audio_grid, from_=8000, to=48000, textvariable=self.audio_samplerate, 
                   width=8).grid(row=0, column=1, sticky="w", padx=(5, 0), pady=2)

        ttk.Label(audio_grid, text="Channels:").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Spinbox(audio_grid, from_=1, to=2, textvariable=self.audio_channels, 
                   width=8).grid(row=1, column=1, sticky="w", padx=(5, 0), pady=2)

        # Recording Controls
        controls_frame = ttk.LabelFrame(right_frame, text="🎮 Controls", padding="10")
        controls_frame.pack(fill="x")

        self.rec_start_btn = ttk.Button(controls_frame, text="🔴 Start", 
                                       command=self.start_recording, style="Action.TButton")
        self.rec_start_btn.pack(fill="x", pady=(0, 4))

        self.rec_pause_btn = ttk.Button(controls_frame, text="⏸️ Pause", 
                                       command=self.pause_recording, 
                                       state="disabled", style="Action.TButton")
        self.rec_pause_btn.pack(fill="x", pady=(0, 4))

        self.rec_stop_btn = ttk.Button(controls_frame, text="⏹️ Stop", 
                                      command=self.stop_recording, 
                                      state="disabled", style="Action.TButton")
        self.rec_stop_btn.pack(fill="x")

        # Bottom section - Status
        status_frame = ttk.LabelFrame(main_frame, text="📊 Recording Status", padding="10")
        status_frame.pack(fill="x")

        self.rec_status_var = tk.StringVar(value="Idle")
        status_display = ttk.Label(status_frame, textvariable=self.rec_status_var, 
                                  style="Status.TLabel", font=("Segoe UI", 9, "bold"))
        status_display.pack(pady=3)

        # Add tooltips
        self.add_recording_tooltips()

    def add_screenshot_tooltips(self):
        """Add tooltips for screenshot tab"""
        ToolTip(self.capture_entry, "Enter key combination for manual capture (e.g., ctrl+alt+s)")
        ToolTip(self.stop_entry, "Enter key combination to stop auto capture")
        ToolTip(self.auto_start_entry, "Hotkey to start automatic screenshot capture")
        ToolTip(self.auto_pause_entry, "Hotkey to pause/resume automatic capture")
        ToolTip(self.auto_stop_entry, "Hotkey to completely stop automatic capture")
        ToolTip(self.interval_spin, "Time interval between automatic screenshots (in seconds)")
        ToolTip(self.duration_spin, "Maximum duration for auto capture (0 = unlimited)")
        ToolTip(self.bg_btn, "Save settings and run the application in background with tray icon")

    def add_recording_tooltips(self):
        """Add tooltips for recording tab"""
        ToolTip(self.rec_hot_entry, "Hotkey to start screen recording")
        ToolTip(self.rec_stop_entry, "Hotkey to stop screen recording")

    def select_folder(self):
        """Select save folder"""
        folder = filedialog.askdirectory(title="Select Save Folder")
        if folder:
            self.folder_path.set(folder)

    def manual_capture(self):
        """Trigger manual capture"""
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select a save folder!")
            return
        
        try:
            self.screenshot_engine.manual_capture()
            self.update_status("Manual capture completed")
        except Exception as e:
            messagebox.showerror("Error", f"Manual capture failed: {e}")

    def validate_hotkey(self, event):
        """Validate hotkey when user finishes typing"""
        entry = event.widget
        text = entry.get().strip().lower()
        if not text:
            messagebox.showerror("Error", "Hotkey cannot be empty!")
            return
        # Normalize the hotkey format
        normalized = text.replace(" ", "")
        entry.delete(0, tk.END)
        entry.insert(0, normalized)
        
        # Update hotkeys when changed
        self._bind_hotkeys_to_buttons()

    def test_hotkeys(self):
        """Test hotkeys functionality"""
        try:
            # Setup hotkeys
            self._bind_hotkeys_to_buttons()
            
            messagebox.showinfo(
                "Hotkeys Activated", 
                f"🎉 All hotkeys are now active and ready!\n\n"
                f"📷 Manual Capture: {self.capture_hotkey.get()}\n"
                f"▶️ Auto Start: {self.auto_start_hotkey.get()}\n"
                f"⏸️ Auto Pause: {self.auto_pause_hotkey.get()}\n"
                f"⏹️ Auto Stop: {self.auto_stop_hotkey.get()}\n"
                f"🔴 Record Start: {self.record_hotkey.get()}\n"
                f"🛑 Record Stop: {self.stop_record_hotkey.get()}\n\n"
                f"Try pressing any of these key combinations!"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Hotkey setup failed: {e}")

    def save_and_run_background(self):
        """Save settings and run in background WITHOUT starting auto capture"""
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select a save folder!")
            return

        try:
            # Save settings
            if hasattr(self.screenshot_engine, 'save_settings'):
                self.screenshot_engine.save_settings()
            
            # Force disable auto capture
            self.screenshot_engine.update_setting("auto_capture_enabled", False)
            
            # Setup hotkeys
            self._bind_hotkeys_to_buttons()
            
            # Setup tray icon only if not already created
            if not self.tray_icon_created:
                if hasattr(self.screenshot_engine, 'setup_tray_icon'):
                    self.screenshot_engine.setup_tray_icon()
                    self.tray_icon_created = True
                elif hasattr(self.screenshot_engine, 'create_tray_icon'):
                    self.screenshot_engine.create_tray_icon()
                    self.tray_icon_created = True
            
            self.update_status("Running in background - Hotkeys active")
            self.root.withdraw()
            messagebox.showinfo("Background Mode", 
                              "✅ Application is now running in background!\n\n"
                              "🔑 All hotkeys are active\n"
                              "🖱️ Right-click system tray icon to access options\n"
                              "👁️ Click tray icon to show this window again")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run in background: {e}")

    def start_background(self):
        """Start background capture process - DEPRECATED, use save_and_run_background instead"""
        self.save_and_run_background()

    def start_recording(self):
        """Start screen recording"""
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select a save folder!")
            return
        self.recording_controller.start_recording()

    def pause_recording(self):
        """Pause/Resume recording"""
        self.recording_controller.toggle_pause()

    def stop_recording(self):
        """Stop screen recording"""
        self.recording_controller.stop_recording()

    def show_window(self, icon=None, item=None):
        """Show main window"""
        self.root.deiconify()
        self.root.lift()

    def on_window_close(self):
        """Handle window close event"""
        if self.screenshot_engine.is_capturing or self.recording_controller.is_recording:
            self.root.withdraw()
        else:
            self.quit_app()

    def quit_app(self, icon=None, item=None):
        """Quit the application"""
        self.screenshot_engine.cleanup()
        self.recording_controller.cleanup()
        
        # Reset tray icon flag when quitting
        self.tray_icon_created = False
        
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass

    def update_status(self, message):
        """Update status label"""
        self.status_var.set(message)

    def update_memory(self, message):
        """Update memory label"""
        self.memory_var.set(message)

    def update_rec_status(self, message):
        """Update recording status label"""
        self.rec_status_var.set(message)
        ml = message.lower()
        if ml.startswith("recording"):
            self.rec_start_btn.config(state="disabled")
            self.rec_pause_btn.config(state="normal", text="⏸️ Pause")
            self.rec_stop_btn.config(state="normal")
        elif ml.startswith("paused"):
            self.rec_pause_btn.config(state="normal", text="▶️ Resume")
        elif ml.startswith("idle") or ml.startswith("saved"):
            self.rec_start_btn.config(state="normal")
            self.rec_pause_btn.config(state="disabled", text="⏸️ Pause")
            self.rec_stop_btn.config(state="disabled")

    def update_memory_usage(self):
        """Update memory usage display if enabled"""
        if self.show_memory_var.get():
            memory_info = self.screenshot_engine.get_memory_usage()
            self.memory_var.set(memory_info)
        else:
            self.memory_var.set("")
        self.root.after(5000, self.update_memory_usage)

    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()

    def update_auto_buttons(self, running: bool, paused: bool = False):
        """Update auto capture button states"""
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

    def on_auto_start_btn(self):
        """Start auto capture"""
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select a save folder!")
            return
        
        try:
            # Enable auto capture
            self.screenshot_engine.update_setting("auto_capture_enabled", True)
            
            # Start auto capture
            if hasattr(self.screenshot_engine, "start_auto_capture"):
                success = self.screenshot_engine.start_auto_capture()
            else:
                success = self._start_auto_capture_thread()
            
            if success:
                self.update_status("Auto Capture STARTED")
                self.update_auto_buttons(running=True, paused=False)
            else:
                messagebox.showerror("Error", "Failed to start auto capture")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start auto capture: {e}")

    def _start_auto_capture_thread(self):
        """Start auto capture thread"""
        try:
            import threading
            import time
            
            def auto_capture_loop():
                self.screenshot_engine.update_setting("auto_capture_enabled", True)
                
                # Duration settings
                duration_min = self.auto_capture_duration_min.get()
                start_time = time.time()
                end_time = start_time + (duration_min * 60) if duration_min > 0 else None
                
                while self.screenshot_engine.get_setting("auto_capture_enabled"):
                    try:
                        # Check duration limit
                        if end_time and time.time() >= end_time:
                            self.screenshot_engine.update_setting("auto_capture_enabled", False)
                            self.root.after(0, lambda: self.update_status("Auto Capture - Duration completed"))
                            self.root.after(0, lambda: self.update_auto_buttons(running=False))
                            break
                        
                        # Take screenshot
                        self.screenshot_engine.manual_capture()
                        
                        # Sleep with interrupt checking
                        interval = self.auto_capture_interval.get()
                        for i in range(interval):
                            if not self.screenshot_engine.get_setting("auto_capture_enabled"):
                                break
                            time.sleep(1)
                            
                    except Exception:
                        break
            
            thread = threading.Thread(target=auto_capture_loop, daemon=True)
            thread.start()
            return True
        except Exception:
            return False

    def on_auto_pause_btn(self):
        """Pause auto capture"""
        try:
            self.screenshot_engine.update_setting("auto_capture_enabled", False)
            self.update_status("Auto Capture PAUSED")
            self.update_auto_buttons(running=True, paused=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to pause: {e}")

    def on_auto_stop_btn(self):
        """Stop auto capture"""
        try:
            self.screenshot_engine.update_setting("auto_capture_enabled", False)
            if hasattr(self.screenshot_engine, "stop_all_capture"):
                self.screenshot_engine.stop_all_capture()
            self.update_status("Auto Capture STOPPED")
            self.update_auto_buttons(running=False)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop: {e}")


if __name__ == "__main__":
    app = ScreenshotGUI()
    app.run()