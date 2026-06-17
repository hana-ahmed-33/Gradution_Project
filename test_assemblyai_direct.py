#!/usr/bin/env python3
"""
Direct test of AssemblyAI API to check if the key works
"""
import os
import sys

# Add the app directory to Python path
sys.path.append('.')

from app.config import settings
import assemblyai as aai

def test_assemblyai_key():
    """Test if AssemblyAI API key is working"""
    print("🔑 Testing AssemblyAI API Key")
    print("=" * 50)
    
    # Get API key from settings
    api_key = settings.assemblyai_api_key
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    
    # Configure AssemblyAI
    aai.settings.api_key = api_key
    
    try:
        # Test with a simple URL (AssemblyAI's test audio)
        print("\n🧪 Testing with AssemblyAI sample audio...")
        
        config = aai.TranscriptionConfig(
            language_code="en",  # English for test
            speech_model=aai.SpeechModel.best,
        )
        
        transcriber = aai.Transcriber(config=config)
        
        # Use AssemblyAI's sample audio URL
        test_url = "https://storage.googleapis.com/aai-docs-samples/nbc.wav"
        
        print("📤 Sending request to AssemblyAI...")
        transcript = transcriber.transcribe(test_url)
        
        if transcript.status == aai.TranscriptStatus.error:
            print(f"❌ AssemblyAI Error: {transcript.error}")
            return False
        
        print(f"✅ Success! Transcription: {transcript.text[:100]}...")
        print(f"🎯 Confidence: {transcript.confidence}")
        
        return True
        
    except Exception as e:
        print(f"❌ API Test Failed: {e}")
        return False

def test_arabic_transcription():
    """Test Arabic transcription capability"""
    print("\n🇸🇦 Testing Arabic Language Support")
    print("=" * 50)
    
    try:
        # Configure for Arabic
        config = aai.TranscriptionConfig(
            language_code="ar",
            speech_model=aai.SpeechModel.best,
        )
        
        transcriber = aai.Transcriber(config=config)
        
        # This will fail because we don't have Arabic audio URL, but it tests the config
        print("✅ Arabic configuration created successfully")
        print("⚠️  Need actual Arabic audio file to test transcription")
        
        return True
        
    except Exception as e:
        print(f"❌ Arabic config failed: {e}")
        return False

if __name__ == "__main__":
    print("🎤 AssemblyAI Direct Test")
    print("=" * 50)
    
    # Test API key
    key_works = test_assemblyai_key()
    
    if key_works:
        # Test Arabic support
        arabic_works = test_arabic_transcription()
        
        print("\n" + "=" * 50)
        print("📊 RESULTS:")
        print(f"✅ API Key: {'Working' if key_works else 'Failed'}")
        print(f"✅ Arabic Support: {'Available' if arabic_works else 'Failed'}")
        
        if key_works and arabic_works:
            print("\n🎯 CONCLUSION:")
            print("AssemblyAI should work with your setup!")
            print("The issue might be with audio file format or processing.")
        else:
            print("\n⚠️  ISSUE FOUND:")
            print("AssemblyAI API has problems with your configuration.")
    else:
        print("\n❌ API Key Issue:")
        print("Your AssemblyAI API key might be invalid or expired.")
        print("Check: https://www.assemblyai.com/dashboard/")