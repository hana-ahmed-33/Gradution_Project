#!/usr/bin/env python3
"""
Test script to verify audio processing fixes
"""
import requests
import io
import wave
import struct

def create_test_wav():
    """Create a simple test WAV file in memory"""
    # Create a simple sine wave
    sample_rate = 44100
    duration = 2  # seconds
    frequency = 440  # Hz (A note)
    
    # Generate samples
    samples = []
    for i in range(int(sample_rate * duration)):
        t = i / sample_rate
        sample = int(32767 * 0.5 * (1 + 0.5 * (t % 1)))  # Simple wave
        samples.append(struct.pack('<h', sample))
    
    # Create WAV file in memory
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b''.join(samples))
    
    wav_buffer.seek(0)
    return wav_buffer.getvalue()

def test_voice_endpoint():
    """Test the /voice endpoint with a generated WAV file"""
    print("🎵 Creating test WAV file...")
    wav_data = create_test_wav()
    print(f"✅ Created WAV file: {len(wav_data)} bytes")
    
    print("\n🚀 Testing /voice endpoint...")
    
    try:
        # Test the voice endpoint
        files = {'file': ('test_audio.wav', wav_data, 'audio/wav')}
        response = requests.post('http://localhost:8000/voice', files=files, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS! Voice analysis completed")
            print(f"📝 Transcription: {result['data']['transcription']}")
            print(f"🎯 Confidence: {result['data']['confidence_score']:.2f}")
            print(f"⏱️  Duration: {result['data']['audio_duration_seconds']:.2f}s")
            print(f"🔍 Analysis: {result['data']['analysis']['transaction_type']}")
            return True
        else:
            print(f"❌ FAILED with status {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_health_endpoint():
    """Test the health endpoint"""
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get('http://localhost:8000/health', timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Health check passed: {result['status']}")
            print(f"📊 Service: {result['service']} v{result['version']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Finance Analyzer - Audio Processing Test")
    print("=" * 50)
    
    # Test health first
    health_ok = test_health_endpoint()
    
    if health_ok:
        print("\n" + "=" * 50)
        # Test voice processing
        voice_ok = test_voice_endpoint()
        
        print("\n" + "=" * 50)
        if voice_ok:
            print("🎉 ALL TESTS PASSED! Audio processing is working correctly.")
        else:
            print("⚠️  Voice processing test failed. Check the logs above.")
    else:
        print("⚠️  Server health check failed. Make sure the server is running.")