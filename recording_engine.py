# recording_engine.py
# Engine for screen recording functionality
# Dependencies: mss, opencv-python, sounddevice, numpy

import os
import time
import threading
from datetime import datetime
import gc

# Recording dependencies
import mss
import cv2
import numpy as np
import sounddevice as sd
import queue
import wave
import subprocess


class RecordingEngine:
    def __init__(self):
        # recording state
        self.is_recording = False
        self.record_thread = None
        self.audio_queue = queue.Queue()
        self.audio_stream = None

        # Default recording settings
        self.settings = {
            'folder_path': '',
            'record_fps': 20,
            'record_format': 'mp4',
            'record_area_mode': 'fullscreen',  # fullscreen or custom
            'custom_x': 0,
            'custom_y': 0,
            'custom_w': 800,
            'custom_h': 600,
            'record_audio_enabled': True,
            'audio_samplerate': 44100,
            'audio_channels': 1
        }

        # Callback for UI updates
        self.status_callback = None

    def set_status_callback(self, callback):
        """Set callback function for status updates"""
        self.status_callback = callback

    def update_status(self, message):
        """Update status and call callback if set"""
        if self.status_callback:
            self.status_callback(message)

    def update_setting(self, key, value):
        """Update a single setting"""
        self.settings[key] = value

    def get_setting(self, key):
        """Get a setting value"""
        return self.settings.get(key)

    def update_settings(self, new_settings):
        """Update multiple settings at once"""
        self.settings.update(new_settings)

    def start_recording(self):
        """Start screen recording"""
        if self.is_recording:
            return False
        
        if not self.settings['folder_path']:
            print("Error: Please select a save folder!")
            return False

        self.is_recording = True
        self.update_status("Starting...")
        self.record_thread = threading.Thread(target=self._record_worker, daemon=True)
        self.record_thread.start()
        return True

    def stop_recording(self):
        """Stop screen recording"""
        if not self.is_recording:
            return False
        
        self.is_recording = False
        self.update_status("Stopping...")
        
        if self.record_thread and self.record_thread.is_alive():
            self.record_thread.join(timeout=5)
        
        try:
            if self.audio_stream:
                self.audio_stream.close()
        except:
            pass
        
        self.update_status("Idle")
        return True

    def toggle_recording(self):
        """Toggle recording state"""
        if self.is_recording:
            return self.stop_recording()
        else:
            return self.start_recording()

    def _audio_callback(self, indata, frames, time_info, status):
        """Audio callback for recording"""
        if not self.is_recording:
            return
        self.audio_queue.put(indata.copy())

    def _write_audio_to_wav(self, wav_path, samplerate, channels):
        """Write audio data to WAV file"""
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
        """Main recording worker thread"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        basename = f"record_{timestamp}"
        folder = self.settings['folder_path']
        video_path_raw = os.path.join(folder, basename + ".avi")
        audio_path = os.path.join(folder, basename + ".wav")
        final_path = os.path.join(folder, f"{basename}.{self.settings['record_format']}")

        # determine capture region
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            if self.settings['record_area_mode'] == 'fullscreen':
                x = monitor['left']
                y = monitor['top']
                w = monitor['width']
                h = monitor['height']
            else:
                x = self.settings['custom_x']
                y = self.settings['custom_y']
                w = self.settings['custom_w']
                h = self.settings['custom_h']

        fps = max(1, int(self.settings['record_fps']))
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(video_path_raw, fourcc, fps, (w, h))

        # start audio stream if enabled
        if self.settings['record_audio_enabled']:
            samplerate = int(self.settings['audio_samplerate'])
            channels = int(self.settings['audio_channels'])
            self.audio_queue = queue.Queue()
            try:
                self.audio_stream = sd.InputStream(
                    samplerate=samplerate, 
                    channels=channels, 
                    callback=self._audio_callback
                )
                self.audio_stream.start()
                audio_thread = threading.Thread(
                    target=self._write_audio_to_wav, 
                    args=(audio_path, samplerate, channels), 
                    daemon=True
                )
                audio_thread.start()
            except Exception as e:
                print('Audio input error:', e)
                self.settings['record_audio_enabled'] = False

        self.update_status('Recording')
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
            if self.settings['record_audio_enabled'] and self.audio_stream:
                try:
                    self.audio_stream.stop()
                except:
                    pass

            # try merge audio + video using ffmpeg if available
            merged = False
            if self.settings['record_audio_enabled'] and os.path.exists(audio_path):
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
                if not self.settings['record_audio_enabled']:
                    # convert/rename .avi to desired extension if user requested mp4 and ffmpeg exists
                    if self.settings['record_format'] != 'avi':
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

            self.update_status(f"Saved: {os.path.basename(final_path)}")
            gc.collect()

    def cleanup(self):
        """Cleanup resources"""
        self.is_recording = False
        try:
            if self.audio_stream:
                self.audio_stream.close()
        except:
            pass
