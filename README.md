# System Audio Transcriber

A Kivy-based Android application that captures system audio in real-time and converts it to text displayed in a floating popup.

## Features

1. **Main Screen**:
   - Pattern lock authentication to access the popup.

2. **Floating Popup**:
   - Displays real-time transcriptions of system audio.
   - Resizable and adjustable.
   - Overlays other applications.

3. **Audio Capture & Transcription**:
   - Uses Android's AudioPlaybackCapture API.
   - Provides real-time speech-to-text conversion.

## Technical Stack

- **Kivy & KivyMD**: For UI development
- **Pyjnius**: For Android API integration
- **Vosk**: For offline speech recognition
- **Plyer**: For overlay and permission management

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Build for Android:
   ```
   buildozer android debug deploy run
   ```

## Permissions Required

- RECORD_AUDIO
- SYSTEM_ALERT_WINDOW
- FOREGROUND_SERVICE
- CAPTURE_AUDIO_OUTPUT
