# recording_controller.py
# Controller for recording engine with hotkey support
# This bridges the gap between recording_engine and keyboard handling

import os
import keyboard
from recording_engine import RecordingEngine


class RecordingController:
    def __init__(self):
        self.engine = RecordingEngine()
        self.hotkey_settings = {
            'record_hotkey': 'ctrl+shift+r',
            'stop_record_hotkey': 'ctrl+shift+t'
        }

    def set_status_callback(self, callback):
        """Set callback for status updates"""
        self.engine.set_status_callback(callback)

    def update_setting(self, key, value):
        """Update a setting"""
        if key in self.hotkey_settings:
            self.hotkey_settings[key] = value
        else:
            self.engine.update_setting(key, value)

    def get_setting(self, key):
        """Get a setting value"""
        if key in self.hotkey_settings:
            return self.hotkey_settings.get(key)
        return self.engine.get_setting(key)

    def setup_hotkeys(self):
        """Setup recording hotkeys"""
        try:
            # Remove existing hotkeys for recording
            try:
                keyboard.remove_hotkey(self.hotkey_settings['record_hotkey'])
            except:
                pass
            try:
                keyboard.remove_hotkey(self.hotkey_settings['stop_record_hotkey'])
            except:
                pass
            
            # Add new hotkeys
            keyboard.add_hotkey(self.hotkey_settings['record_hotkey'], self.engine.toggle_recording)
            keyboard.add_hotkey(self.hotkey_settings['stop_record_hotkey'], self.engine.stop_recording)
        except Exception as e:
            print(f"Error setting up recording hotkeys: {e}")

    def start_recording(self):
        """Start recording and setup hotkeys"""
        result = self.engine.start_recording()
        if result:
            self.setup_hotkeys()
        return result

    def stop_recording(self):
        """Stop recording"""
        return self.engine.stop_recording()

    def toggle_recording(self):
        """Toggle recording"""
        return self.engine.toggle_recording()

    @property
    def is_recording(self):
        """Check if recording"""
        return self.engine.is_recording

    def pause_recording(self):
        """Pause recording"""
        return self.engine.pause_recording()

    def resume_recording(self):
        """Resume recording"""
        return self.engine.resume_recording()

    def toggle_pause(self):
        """Toggle pause/resume"""
        return self.engine.toggle_pause()

    def cleanup(self):
        """Cleanup resources"""
        try:
            keyboard.remove_hotkey(self.hotkey_settings['record_hotkey'])
        except:
            pass
        try:
            keyboard.remove_hotkey(self.hotkey_settings['stop_record_hotkey'])
        except:
            pass
        self.engine.cleanup()
