# System Audio Transcriber for Windows

A Python application that captures Windows system audio in real-time and converts it to text displayed in a floating popup window.

## Features

1. **Floating Popup Window**:
   - Displays real-time transcriptions of system audio.
   - Resizable and draggable.
   - Overlays other applications (always on top).
   - Minimizes to a small icon.

2. **Audio Capture & Transcription**:
   - Captures system audio (not microphone) using WASAPI loopback.
   - Provides real-time speech-to-text conversion.
   - Uses offline speech recognition for privacy.

## Technical Stack

- **Tkinter**: For UI development and cross-platform window management
- **PyAudio**: For system audio capture using WASAPI loopback
- **Vosk**: For offline speech recognition
- **NumPy**: For audio data processing

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Download a Vosk speech recognition model:
   ```
   python setup_models.py
   ```
   
   Or manually download a model from https://alphacephei.com/vosk/models

3. Run the application:
   ```
   python main.py
   ```

## Requirements

- Windows 10 or higher
- Python 3.8 or higher
- A system audio device that supports WASAPI loopback

## Usage

1. Select a Vosk model directory
2. Click "Start" to begin transcription
3. Drag the title bar to move the window
4. Right-click and drag any edge to resize the window
5. Use the minimize button to shrink to a small icon
6. Use the clear button to reset the transcription
