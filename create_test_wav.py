#!/usr/bin/env python3
"""
Create a simple test WAV file for testing
"""
import wave
import struct
import math

def create_test_wav_file():
    """Create a simple test WAV file"""
    filename = "test_voice.wav"
    
    # Audio parameters
    sample_rate = 44100
    duration = 2  # seconds
    frequency = 440  # Hz (A note)
    
    # Generate samples
    samples = []
    for i in range(int(sample_rate * duration)):
        t = i / sample_rate
        # Create a simple sine wave
        sample = int(32767 * 0.3 * math.sin(2 * math.pi * frequency * t))
        samples.append(struct.pack('<h', sample))
    
    # Write WAV file
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b''.join(samples))
    
    print(f"✅ Created test WAV file: {filename}")
    print(f"📊 Duration: {duration}s, Sample Rate: {sample_rate}Hz")
    
    # Get file size
    import os
    size = os.path.getsize(filename)
    print(f"📁 File size: {size} bytes ({size/1024:.1f} KB)")
    
    return filename

if __name__ == "__main__":
    create_test_wav_file()