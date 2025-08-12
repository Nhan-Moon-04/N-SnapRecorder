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

# New deps for recording
import mss
import cv2
import numpy as np
import sounddevice as sd
import queue
import wave
import subprocess


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
        self.capture_thread = None
        self.auto_capture_thread = None
        self.tray_icon = None

        # recording state
        self.is_recording = False
        self.record_thread = None
        self.audio_queue = queue.Queue()
        self.audio_stream = None

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
        self.auto_capture_enabled = tk.BooleanVar()
        self.auto_capture_interval = tk.IntVar(value=60)

        # recording variables
        self.record_hotkey = tk.StringVar(value="ctrl+shift+r")
        self.stop_record_hotkey = tk.StringVar(value="ctrl+shift+t")
        self.record_fps = tk.IntVar(value=20)
        self.record_format = tk.StringVar(value="mp4")
        self.record_area_mode = tk.StringVar(value="fullscreen")  # fullscreen or custom
        self.custom_x = tk.IntVar(value=0)
        self.custom_y = tk.IntVar(value=0)
        self.custom_w = tk.IntVar(value=800)
        self.custom_h = tk.IntVar(value=600)
        self.record_audio_enabled = tk.BooleanVar(value=True)
        self.audio_samplerate = tk.IntVar(value=44100)
        self.audio_channels = tk.IntVar(value=1)

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

                    # recording settings
                    self.record_hotkey.set(settings.get('record_hotkey', 'ctrl+shift+r'))
                    self.stop_record_hotkey.set(settings.get('stop_record_hotkey', 'ctrl+shift+t'))
                    self.record_fps.set(settings.get('record_fps', 20))
                    self.record_format.set(settings.get('record_format', 'mp4'))
                    self.record_area_mode.set(settings.get('record_area_mode', 'fullscreen'))
                    self.custom_x.set(settings.get('custom_x', 0))
                    self.custom_y.set(settings.get('custom_y', 0))
                    self.custom_w.set(settings.get('custom_w', 800))
                    self.custom_h.set(settings.get('custom_h', 600))
                    self.record_audio_enabled.set(settings.get('record_audio_enabled', True))
                    self.audio_samplerate.set(settings.get('audio_samplerate', 44100))
                    self.audio_channels.set(settings.get('audio_channels', 1))
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
                'auto_capture_interval': self.auto_capture_interval.get(),

                # recording settings
                'record_hotkey': self.record_hotkey.get(),
                'stop_record_hotkey': self.stop_record_hotkey.get(),
                'record_fps': self.record_fps.get(),
                'record_format': self.record_format.get(),
                'record_area_mode': self.record_area_mode.get(),
                'custom_x': self.custom_x.get(),
                'custom_y': self.custom_y.get(),
                'custom_w': self.custom_w.get(),
                'custom_h': self.custom_h.get(),
                'record_audio_enabled': self.record_audio_enabled.get(),
                'audio_samplerate': self.audio_samplerate.get(),
                'audio_channels': self.audio_channels.get()
            }
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
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

        # ----------------- Screenshot Tab (existing UI) -----------------
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

        # hotkeys and auto capture (kept compact)
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

        self.update_memory_usage()

        ToolTip(self.capture_entry, "Press key combination (e.g., ctrl+alt+s)")
        ToolTip(self.stop_entry, "Press a different key combination")
        ToolTip(self.interval_spin, "Time between auto captures")

        folder_entry.focus_set()

        # ----------------- Screen Recording Tab -----------------
        rec_frame = ttk.Frame(tab2, padding="10")
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
        folder = filedialog.askdirectory(title="Select Save Folder")
        if folder:
            self.folder_path.set(folder)

    def setup_hotkeys(self):
        """Set up global hotkeys"""
        try:
            keyboard.unhook_all()
            keyboard.add_hotkey(self.capture_hotkey.get(), self.manual_capture)
            keyboard.add_hotkey(self.stop_hotkey.get(), self.stop_all_capture)
            # recording hotkeys
            keyboard.add_hotkey(self.record_hotkey.get(), self.toggle_recording)
            keyboard.add_hotkey(self.stop_record_hotkey.get(), self.stop_recording)
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
        text = entry.get().strip().lower()
        if not text:
            messagebox.showerror("Error", "Hotkey cannot be empty!")
            return
        # minimal validation (user responsible for valid combos)

    def test_hotkeys(self):
        try:
            messagebox.showinfo("Test", "Press the hotkeys you assigned. If the app responds, they work.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def auto_capture_loop(self):
        while self.auto_capture_enabled.get() and self.is_capturing:
            try:
                self.manual_capture()
                for _ in range(self.auto_capture_interval.get()):
                    if not self.auto_capture_enabled.get() or not self.is_capturing:
                        break
                    time.sleep(1)
            except Exception as e:
                print(f"Auto capture error: {e}")
                time.sleep(1)

    def start_background(self):
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select a save folder!")
            return
        self.save_settings()
        self.setup_hotkeys()
        self.is_capturing = True
        if self.auto_capture_enabled.get():
            self.auto_capture_thread = threading.Thread(target=self.auto_capture_loop, daemon=True)
            self.auto_capture_thread.start()
        self.create_tray_icon()
        self.root.withdraw()
        self.status_var.set("Running in background...")

    def stop_all_capture(self):
        self.is_capturing = False
        self.auto_capture_enabled.set(False)
        self.status_var.set("Stopped")

    def create_tray_icon(self):
        image = Image.new('RGB', (64, 64), color='blue')
        draw = ImageDraw.Draw(image)
        draw.ellipse([16, 16, 48, 48], fill='white')
        menu = pystray.Menu(
            pystray.MenuItem("Show Window", self.show_window),
            pystray.MenuItem("Capture Now", self.manual_capture),
            pystray.MenuItem("Start Recording", self.start_recording),
            pystray.MenuItem("Stop Recording", self.stop_recording),
            pystray.MenuItem("Stop Auto", self.stop_all_capture),
            pystray.MenuItem("Exit", self.quit_app)
        )
        self.tray_icon = pystray.Icon("ScreenshotApp", image, "Screenshot Tool", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self, icon=None, item=None):
        self.root.deiconify()
        self.root.lift()

    def on_window_close(self):
        if self.is_capturing or self.is_recording:
            self.root.withdraw()
        else:
            self.quit_app()

    def quit_app(self, icon=None, item=None):
        self.is_capturing = False
        self.is_recording = False
        self.save_settings()
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except:
                pass
        keyboard.unhook_all()
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

    # ----------------- Recording logic -----------------
    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        if self.is_recording:
            return
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select a save folder!")
            return
        # start threads
        self.save_settings()
        self.is_recording = True
        self.rec_status_var.set("Starting...")
        self.record_thread = threading.Thread(target=self._record_worker, daemon=True)
        self.record_thread.start()
        # setup hotkeys again to ensure they're active
        self.setup_hotkeys()

    def stop_recording(self):
        if not self.is_recording:
            return
        self.is_recording = False
        self.rec_status_var.set("Stopping...")
        # wait for threads to finish
        if self.record_thread and self.record_thread.is_alive():
            self.record_thread.join(timeout=5)
        # if audio stream open, stop
        try:
            if self.audio_stream:
                self.audio_stream.close()
        except:
            pass
        self.rec_status_var.set("Idle")

    def _audio_callback(self, indata, frames, time_info, status):
        if not self.is_recording:
            return
        # put raw data into queue
        self.audio_queue.put(indata.copy())

    def _write_audio_to_wav(self, wav_path, samplerate, channels):
        # drain queue and write to wav
        wf = wave.open(wav_path, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(samplerate)
        try:
            while self.is_recording or not self.audio_queue.empty():
                try:
                    data = self.audio_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                # convert float32 to int16
                int_data = (data * 32767).astype(np.int16)
                wf.writeframes(int_data.tobytes())
        finally:
            wf.close()

    def _record_worker(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        basename = f"record_{timestamp}"
        folder = self.folder_path.get()
        video_path_raw = os.path.join(folder, basename + ".avi")
        audio_path = os.path.join(folder, basename + ".wav")
        final_path = os.path.join(folder, f"{basename}.{self.record_format.get()}")

        # determine capture region
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            if self.record_area_mode.get() == 'fullscreen':
                x = monitor['left']
                y = monitor['top']
                w = monitor['width']
                h = monitor['height']
            else:
                x = self.custom_x.get()
                y = self.custom_y.get()
                w = self.custom_w.get()
                h = self.custom_h.get()

        fps = max(1, int(self.record_fps.get()))
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(video_path_raw, fourcc, fps, (w, h))

        # start audio stream if enabled
        if self.record_audio_enabled.get():
            samplerate = int(self.audio_samplerate.get())
            channels = int(self.audio_channels.get())
            self.audio_queue = queue.Queue()
            try:
                self.audio_stream = sd.InputStream(samplerate=samplerate, channels=channels, callback=self._audio_callback)
                self.audio_stream.start()
                audio_thread = threading.Thread(target=self._write_audio_to_wav, args=(audio_path, samplerate, channels), daemon=True)
                audio_thread.start()
            except Exception as e:
                print('Audio input error:', e)
                self.record_audio_enabled.set(False)

        self.rec_status_var.set('Recording')
        start_time = time.time()
        frame_period = 1.0 / fps

        try:
            with mss.mss() as sct:
                region = {"left": x, "top": y, "width": w, "height": h}
                while self.is_recording:
                    t0 = time.time()
                    img = sct.grab(region)
                    frame = np.array(img)
                    # convert BGRA to BGR
                    if frame.shape[2] == 4:
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    out.write(frame)

                    # sleep to keep fps
                    elapsed = time.time() - t0
                    to_sleep = frame_period - elapsed
                    if to_sleep > 0:
                        time.sleep(to_sleep)
        except Exception as e:
            print('Recording error:', e)
        finally:
            out.release()
            # stop audio
            if self.record_audio_enabled.get() and self.audio_stream:
                try:
                    self.audio_stream.stop()
                except:
                    pass

            # try merge audio + video using ffmpeg if available
            merged = False
            if self.record_audio_enabled.get():
                try:
                    # check ffmpeg
                    subprocess.run(['ffmpeg', '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    cmd = [
                        'ffmpeg', '-y', '-i', video_path_raw, '-i', audio_path,
                        '-c:v', 'copy', '-c:a', 'aac', final_path
                    ]
                    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    merged = os.path.exists(final_path)
                except Exception as e:
                    print('ffmpeg merge failed or ffmpeg not installed:', e)

            if not merged:
                # if no merge, and user chose mp4, move raw avi to final_path if no audio
                if not self.record_audio_enabled.get():
                    # convert/rename .avi to desired extension if user requested mp4 and ffmpeg exists
                    if self.record_format.get() != 'avi':
                        try:
                            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            cmd = ['ffmpeg', '-y', '-i', video_path_raw, final_path]
                            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            if os.path.exists(final_path):
                                os.remove(video_path_raw)
                        except Exception:
                            # leave avi as-is
                            final_path = video_path_raw
                    else:
                        final_path = video_path_raw
                else:
                    # audio present but merge failed -> keep separate files
                    final_path = video_path_raw

            # final cleanup: if audio merged, remove intermediates
            if merged:
                try:
                    if os.path.exists(video_path_raw):
                        os.remove(video_path_raw)
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                except:
                    pass

            self.rec_status_var.set(f"Saved: {os.path.basename(final_path)}")
            gc.collect()

    # ----------------- end recording logic -----------------

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ScreenshotApp()
    app.run()
    