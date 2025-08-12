# main_gui.py
# GUI for Advanced Screenshot & ScreenRecorder Tool
# This file handles the user interface and communicates with screenshot_engine.py and recording_controller.py

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from screenshot_engine import ScreenshotEngine
from recording_controller import RecordingController


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


class ScreenshotGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.screenshot_engine = ScreenshotEngine()
        self.recording_controller = RecordingController()
        
        # Setup GUI variables from engine settings
        self.setup_variables()
        self.setup_gui()
        
        # Set engine callbacks for UI updates
        self.screenshot_engine.set_callbacks(
            status_callback=self.update_status,
            memory_callback=self.update_memory
        )
        
        self.recording_controller.set_status_callback(self.update_rec_status)
        
        # Set tray icon callbacks for screenshot engine
        self.screenshot_engine.set_tray_callbacks(
            show_window_callback=self.show_window,
            start_recording_callback=self.start_recording,
            stop_recording_callback=self.stop_recording,
            exit_callback=self.quit_app
        )
        
        # Start memory monitoring
        self.update_memory_usage()

    def setup_variables(self):
        """Setup tkinter variables and sync with engine settings"""
        self.folder_path = tk.StringVar()
        self.capture_hotkey = tk.StringVar()
        self.stop_hotkey = tk.StringVar()
        self.auto_capture_enabled = tk.BooleanVar()
        self.auto_capture_interval = tk.IntVar()

        # recording variables
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
        self.folder_path.set(self.screenshot_engine.get_setting('folder_path'))
        self.capture_hotkey.set(self.screenshot_engine.get_setting('capture_hotkey'))
        self.stop_hotkey.set(self.screenshot_engine.get_setting('stop_hotkey'))
        self.auto_capture_enabled.set(self.screenshot_engine.get_setting('auto_capture_enabled'))
        self.auto_capture_interval.set(self.screenshot_engine.get_setting('auto_capture_interval'))
        
        # Recording settings
        self.record_hotkey.set(self.recording_controller.get_setting('record_hotkey'))
        self.stop_record_hotkey.set(self.recording_controller.get_setting('stop_record_hotkey'))
        self.record_fps.set(self.recording_controller.get_setting('record_fps'))
        self.record_format.set(self.recording_controller.get_setting('record_format'))
        self.record_area_mode.set(self.recording_controller.get_setting('record_area_mode'))
        self.custom_x.set(self.recording_controller.get_setting('custom_x'))
        self.custom_y.set(self.recording_controller.get_setting('custom_y'))
        self.custom_w.set(self.recording_controller.get_setting('custom_w'))
        self.custom_h.set(self.recording_controller.get_setting('custom_h'))
        self.record_audio_enabled.set(self.recording_controller.get_setting('record_audio_enabled'))
        self.audio_samplerate.set(self.recording_controller.get_setting('audio_samplerate'))
        self.audio_channels.set(self.recording_controller.get_setting('audio_channels'))

    def bind_variables_to_engine(self):
        """Bind GUI variables to update engine settings"""
        # Screenshot engine bindings
        self.folder_path.trace_add('write', lambda *args: self._update_folder_path())
        self.capture_hotkey.trace_add('write', lambda *args: self.screenshot_engine.update_setting('capture_hotkey', self.capture_hotkey.get()))
        self.stop_hotkey.trace_add('write', lambda *args: self.screenshot_engine.update_setting('stop_hotkey', self.stop_hotkey.get()))
        self.auto_capture_enabled.trace_add('write', lambda *args: self.screenshot_engine.update_setting('auto_capture_enabled', self.auto_capture_enabled.get()))
        self.auto_capture_interval.trace_add('write', lambda *args: self.screenshot_engine.update_setting('auto_capture_interval', self.auto_capture_interval.get()))
        
        # Recording controller bindings
        self.record_hotkey.trace_add('write', lambda *args: self.recording_controller.update_setting('record_hotkey', self.record_hotkey.get()))
        self.stop_record_hotkey.trace_add('write', lambda *args: self.recording_controller.update_setting('stop_record_hotkey', self.stop_record_hotkey.get()))
        self.record_fps.trace_add('write', lambda *args: self.recording_controller.update_setting('record_fps', self.record_fps.get()))
        self.record_format.trace_add('write', lambda *args: self.recording_controller.update_setting('record_format', self.record_format.get()))
        self.record_area_mode.trace_add('write', lambda *args: self.recording_controller.update_setting('record_area_mode', self.record_area_mode.get()))
        self.custom_x.trace_add('write', lambda *args: self.recording_controller.update_setting('custom_x', self.custom_x.get()))
        self.custom_y.trace_add('write', lambda *args: self.recording_controller.update_setting('custom_y', self.custom_y.get()))
        self.custom_w.trace_add('write', lambda *args: self.recording_controller.update_setting('custom_w', self.custom_w.get()))
        self.custom_h.trace_add('write', lambda *args: self.recording_controller.update_setting('custom_h', self.custom_h.get()))
        self.record_audio_enabled.trace_add('write', lambda *args: self.recording_controller.update_setting('record_audio_enabled', self.record_audio_enabled.get()))
        self.audio_samplerate.trace_add('write', lambda *args: self.recording_controller.update_setting('audio_samplerate', self.audio_samplerate.get()))
        self.audio_channels.trace_add('write', lambda *args: self.recording_controller.update_setting('audio_channels', self.audio_channels.get()))

    def _update_folder_path(self):
        """Update folder path in both engines"""
        folder = self.folder_path.get()
        self.screenshot_engine.update_setting('folder_path', folder)
        self.recording_controller.update_setting('folder_path', folder)

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
        self.setup_screenshot_tab(tab1)
        
        # ----------------- Screen Recording Tab -----------------
        self.setup_recording_tab(tab2)

    def setup_screenshot_tab(self, parent):
        """Setup the screenshot tab"""
        main_frame = ttk.Frame(parent, padding="10")
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

        test_btn = ttk.Button(hotkey_frame, text="Test Hotkeys", command=self.test_hotkeys)
        test_btn.grid(row=3, column=0, columnspan=2, pady=(5, 0))

        auto_header = ttk.Label(main_frame, text="AUTO CAPTURE", style='Title.TLabel')
        auto_header.grid(row=5, column=0, sticky=tk.W, pady=(10, 5))

        auto_frame = ttk.Frame(main_frame, borderwidth=1, relief="solid", padding="5")
        auto_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        auto_capture_cb = ttk.Checkbutton(auto_frame, text="Enable auto capture", 
                                          variable=self.auto_capture_enabled)
        auto_capture_cb.grid(row=0, column=0, columnspan=2, sticky=tk.W)

        ttk.Label(auto_frame, text="Interval (seconds):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.interval_spin = ttk.Spinbox(auto_frame, from_=1, to=3600, 
                                        textvariable=self.auto_capture_interval, width=10)
        self.interval_spin.grid(row=1, column=1, sticky=tk.W, padx=5)

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

        # Add tooltips
        ToolTip(self.capture_entry, "Press key combination (e.g., ctrl+alt+s)")
        ToolTip(self.stop_entry, "Press a different key combination")
        ToolTip(self.interval_spin, "Time between auto captures")

        folder_entry.focus_set()

    def setup_recording_tab(self, parent):
        """Setup the recording tab"""
        rec_frame = ttk.Frame(parent, padding="10")
        rec_frame.pack(fill='both', expand=True)

        rec_folder_label = ttk.Label(rec_frame, text="Save folder:")
        rec_folder_label.grid(row=0, column=0, sticky=tk.W)
        rec_folder_entry = ttk.Entry(rec_frame, textvariable=self.folder_path, width=50)
        rec_folder_entry.grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(rec_frame, text="Browse...", command=self.select_folder).grid(row=0, column=2)

        ttk.Label(rec_frame, text="Recording Hotkey:").grid(row=1, column=0, sticky=tk.W, pady=6)
        self.rec_hot_entry = ttk.Entry(rec_frame, textvariable=self.record_hotkey, width=20)
        self.rec_hot_entry.grid(row=1, column=1, sticky=tk.W)
        self.rec_hot_entry.bind('<FocusOut>', self.validate_hotkey)

        ttk.Label(rec_frame, text="Stop Hotkey:").grid(row=2, column=0, sticky=tk.W, pady=6)
        self.rec_stop_entry = ttk.Entry(rec_frame, textvariable=self.stop_record_hotkey, width=20)
        self.rec_stop_entry.grid(row=2, column=1, sticky=tk.W)
        self.rec_stop_entry.bind('<FocusOut>', self.validate_hotkey)

        ttk.Label(rec_frame, text="FPS:").grid(row=3, column=0, sticky=tk.W, pady=6)
        fps_spin = ttk.Spinbox(rec_frame, from_=5, to=120, textvariable=self.record_fps, width=10)
        fps_spin.grid(row=3, column=1, sticky=tk.W)

        ttk.Label(rec_frame, text="Format:").grid(row=4, column=0, sticky=tk.W, pady=6)
        fmt_combo = ttk.Combobox(rec_frame, values=['mp4','avi','mkv'], textvariable=self.record_format, width=8)
        fmt_combo.grid(row=4, column=1, sticky=tk.W)

        ttk.Label(rec_frame, text="Area:").grid(row=5, column=0, sticky=tk.W, pady=6)
        area_combo = ttk.Combobox(rec_frame, values=['fullscreen','custom'], textvariable=self.record_area_mode, width=12)
        area_combo.grid(row=5, column=1, sticky=tk.W)

        area_custom_frame = ttk.Frame(rec_frame)
        area_custom_frame.grid(row=6, column=0, columnspan=3, sticky=tk.W, pady=4)
        ttk.Label(area_custom_frame, text="x:").pack(side=tk.LEFT)
        ttk.Entry(area_custom_frame, textvariable=self.custom_x, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Label(area_custom_frame, text="y:").pack(side=tk.LEFT)
        ttk.Entry(area_custom_frame, textvariable=self.custom_y, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Label(area_custom_frame, text="w:").pack(side=tk.LEFT)
        ttk.Entry(area_custom_frame, textvariable=self.custom_w, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Label(area_custom_frame, text="h:").pack(side=tk.LEFT)
        ttk.Entry(area_custom_frame, textvariable=self.custom_h, width=6).pack(side=tk.LEFT, padx=2)

        ttk.Checkbutton(rec_frame, text="Record Microphone", variable=self.record_audio_enabled).grid(row=7, column=0, columnspan=2, sticky=tk.W)

        rec_buttons = ttk.Frame(rec_frame)
        rec_buttons.grid(row=8, column=0, columnspan=3, pady=10)
        self.rec_start_btn = ttk.Button(rec_buttons, text="Start Recording", command=self.start_recording)
        self.rec_start_btn.pack(side=tk.LEFT, padx=4)
        ttk.Button(rec_buttons, text="Stop Recording", command=self.stop_recording).pack(side=tk.LEFT, padx=4)

        self.rec_status_var = tk.StringVar(value="Idle")
        ttk.Label(rec_frame, textvariable=self.rec_status_var, font=('Arial',9,'bold')).grid(row=9, column=0, columnspan=3, pady=6)

    def select_folder(self):
        """Select save folder"""
        folder = filedialog.askdirectory(title="Select Save Folder")
        if folder:
            self.folder_path.set(folder)

    def validate_hotkey(self, event):
        """Validate hotkey when user finishes typing"""
        entry = event.widget
        text = entry.get().strip().lower()
        if not text:
            messagebox.showerror("Error", "Hotkey cannot be empty!")
            return

    def test_hotkeys(self):
        """Test hotkeys functionality"""
        try:
            messagebox.showinfo("Test", "Press the hotkeys you assigned. If the app responds, they work.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def manual_capture(self):
        """Trigger manual capture"""
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select a save folder!")
            return
        self.screenshot_engine.manual_capture()

    def start_background(self):
        """Start background capture process"""
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select a save folder!")
            return
        
        if self.screenshot_engine.start_background_capture():
            self.root.withdraw()

    def start_recording(self):
        """Start screen recording"""
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select a save folder!")
            return
        self.recording_controller.start_recording()

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

    def update_memory_usage(self):
        """Update memory usage display"""
        memory_info = self.screenshot_engine.get_memory_usage()
        self.memory_var.set(memory_info)
        self.root.after(5000, self.update_memory_usage)

    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()


if __name__ == "__main__":
    app = ScreenshotGUI()
    app.run()
