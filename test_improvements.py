#!/usr/bin/env python3
"""
Test script for AutoScreenshot improvements
Run this to verify the enhanced features work correctly
"""

import sys
import os
import time
import subprocess

def test_dependencies():
    """Test if all required dependencies are available"""
    print("🔍 Testing dependencies...")
    
    required_packages = [
        'mss', 'cv2', 'numpy', 'sounddevice', 
        'keyboard', 'pystray', 'PIL', 'psutil'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies available!")
    return True

def test_ffmpeg():
    """Test if ffmpeg is available for video processing"""
    print("\n🎥 Testing FFmpeg availability...")
    
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("  ✅ FFmpeg available - High quality video processing enabled")
            return True
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    print("  ⚠️  FFmpeg not found - Basic video recording will work, but quality may be limited")
    print("     Install FFmpeg for best results: https://ffmpeg.org/download.html")
    return False

def test_screen_capture():
    """Test screen capture functionality"""
    print("\n📸 Testing screen capture...")
    
    try:
        import mss
        with mss.mss() as sct:
            # Test capturing primary monitor
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            print(f"  ✅ Screen capture working - Resolution: {screenshot.width}x{screenshot.height}")
            return True
    except Exception as e:
        print(f"  ❌ Screen capture failed: {e}")
        return False

def test_audio_input():
    """Test audio input functionality"""
    print("\n🎤 Testing audio input...")
    
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        
        if input_devices:
            print(f"  ✅ Audio input available - {len(input_devices)} input device(s) found")
            print(f"      Default device: {sd.query_devices(kind='input')['name']}")
            return True
        else:
            print("  ⚠️  No audio input devices found")
            return False
    except Exception as e:
        print(f"  ❌ Audio test failed: {e}")
        return False

def test_hotkey_system():
    """Test hotkey system"""
    print("\n⌨️  Testing hotkey system...")
    
    try:
        import keyboard
        print("  ✅ Keyboard monitoring available")
        print("  ℹ️  Enhanced hotkey capture interface will allow easy key combination setup")
        return True
    except Exception as e:
        print(f"  ❌ Hotkey system test failed: {e}")
        return False

def performance_tips():
    """Display performance optimization tips"""
    print("\n🚀 Performance Tips:")
    print("  • Screenshot Quality: Set to 90-95% for best balance of quality/file size")
    print("  • Video FPS: 30 FPS recommended for smooth recording")
    print("  • Video Quality: CRF 18-23 for high quality (lower = better)")
    print("  • Audio: Use 44100 Hz, Stereo for best quality")
    print("  • For large recordings: Ensure sufficient disk space")

def main():
    """Run all tests"""
    print("🔧 AutoScreenshot Optimization Test Suite")
    print("=" * 50)
    
    tests = [
        test_dependencies,
        test_ffmpeg,
        test_screen_capture,
        test_audio_input,
        test_hotkey_system
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Test failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    passed = sum(results)
    total = len(results)
    print(f"  Passed: {passed}/{total}")
    
    if passed == total:
        print("  🎉 All tests passed! AutoScreenshot is ready for optimized performance.")
    elif passed >= total - 1:
        print("  ✅ Most tests passed. AutoScreenshot will work with minor limitations.")
    else:
        print("  ⚠️  Some issues detected. Check the output above for details.")
    
    performance_tips()
    
    print("\n🚀 Key Improvements in this version:")
    print("  • Enhanced hotkey capture - Click 'Set Hotkey' and press key combination")
    print("  • Better video timing - No more 1.5x speed issues")
    print("  • Higher quality screenshots using MSS library")
    print("  • Improved video quality with configurable CRF settings")
    print("  • Better UI with tabbed interface for advanced settings")
    print("  • Real-time recording feedback with frame count and FPS")

if __name__ == "__main__":
    main()
