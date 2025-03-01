import os
import sys
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog
import pyaudio
import numpy as np
import wave
import tempfile
from vosk import Model, KaldiRecognizer

class FloatingTranscriptionWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("System Audio Transcriber")
        self.root.attributes('-topmost', True)  # Always on top
        self.root.overrideredirect(True)  # Remove window decorations
        
        self.width = 400
        self.height = 300
        self.x = 100
        self.y = 100
        
        # Set initial window position and size
        self.root.geometry(f"{self.width}x{self.height}+{self.x}+{self.y}")
        
        # Create a frame with a border
        self.frame = ttk.Frame(self.root, relief="raised", borderwidth=2)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a title bar
        self.title_bar = ttk.Frame(self.frame)
        self.title_bar.pack(fill=tk.X, side=tk.TOP)
        
        # Title label
        self.title_label = ttk.Label(self.title_bar, text="System Audio Transcription")
        self.title_label.pack(side=tk.LEFT, padx=5)
        
        # Control buttons
        self.min_button = ttk.Button(self.title_bar, text="—", width=2, 
                                    command=self.minimize)
        self.min_button.pack(side=tk.RIGHT)
        
        self.close_button = ttk.Button(self.title_bar, text="✕", width=2, 
                                      command=self.close_window)
        self.close_button.pack(side=tk.RIGHT)
        
        # Transcript text area
        self.text_frame = ttk.Frame(self.frame)
        self.text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.text_area = tk.Text(self.text_frame, wrap=tk.WORD, state=tk.NORMAL)
        self.text_area.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        self.scrollbar = ttk.Scrollbar(self.text_frame, command=self.text_area.yview)
        self.scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        
        self.text_area.config(yscrollcommand=self.scrollbar.set)
        
        # Write initialization message to text area
        self.text_area.insert(tk.END, "System Audio Transcriber initialized.\n")
        self.text_area.insert(tk.END, "1. Select a Vosk model directory using the 'Select Model' button.\n")
        self.text_area.insert(tk.END, "2. Click 'Start' to begin transcription.\n\n")
        self.text_area.see(tk.END)
        
        # Status bar
        self.status_bar = ttk.Frame(self.frame)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Control panel
        self.control_panel = ttk.Frame(self.frame)
        self.control_panel.pack(fill=tk.X, side=tk.BOTTOM, before=self.status_bar, pady=5)
        
        self.start_button = ttk.Button(self.control_panel, text="Start", command=self.start_transcription)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(self.control_panel, text="Stop", command=self.stop_transcription, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = ttk.Button(self.control_panel, text="Clear", command=self.clear_text)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        self.model_button = ttk.Button(self.control_panel, text="Select Model", command=self.select_model)
        self.model_button.pack(side=tk.LEFT, padx=5)
        
        # Debug button to list audio devices
        self.debug_button = ttk.Button(self.control_panel, text="List Devices", command=self.list_audio_devices)
        self.debug_button.pack(side=tk.LEFT, padx=5)
        
        # Bind event handlers for dragging
        self.title_bar.bind("<ButtonPress-1>", self.start_drag)
        self.title_bar.bind("<ButtonRelease-1>", self.stop_drag)
        self.title_bar.bind("<B1-Motion>", self.do_drag)
        
        # Bind event handlers for resizing
        self.root.bind("<ButtonPress-3>", self.start_resize)
        self.root.bind("<ButtonRelease-3>", self.stop_resize)
        self.root.bind("<B3-Motion>", self.do_resize)
        
        # Transcription variables
        self.is_transcribing = False
        self.transcription_thread = None
        self.audio_stream = None
        self.audio = None
        self.model = None
        self.recognizer = None
        self.model_path = None
        self.loopback_device_index = None
        
        # Initialize Audio
        self.initialize_audio()
        
    def start_drag(self, event):
        self.x_offset = event.x
        self.y_offset = event.y
    
    def stop_drag(self, event):
        self.x_offset = None
        self.y_offset = None
    
    def do_drag(self, event):
        if self.x_offset is not None and self.y_offset is not None:
            x = self.root.winfo_pointerx() - self.x_offset
            y = self.root.winfo_pointery() - self.y_offset
            self.root.geometry(f"+{x}+{y}")
    
    def start_resize(self, event):
        self.x_resize = event.x
        self.y_resize = event.y
    
    def stop_resize(self, event):
        self.x_resize = None
        self.y_resize = None
    
    def do_resize(self, event):
        if self.x_resize is not None and self.y_resize is not None:
            width = max(200, self.root.winfo_width() + (event.x - self.x_resize))
            height = max(150, self.root.winfo_height() + (event.y - self.y_resize))
            self.root.geometry(f"{width}x{height}")
            self.x_resize = event.x
            self.y_resize = event.y
    
    def minimize(self):
        self.root.withdraw()
        
        # Create a small icon in the system tray
        icon = tk.Toplevel(self.root)
        icon.overrideredirect(True)
        icon.attributes('-topmost', True)
        icon.geometry("30x30+0+0")
        
        icon_button = ttk.Button(icon, text="📝", command=lambda: self.restore(icon))
        icon_button.pack(fill=tk.BOTH, expand=True)
    
    def restore(self, icon):
        self.root.deiconify()
        icon.destroy()
    
    def close_window(self):
        self.stop_transcription()
        self.root.destroy()
        sys.exit()
    
    def clear_text(self):
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, "Transcription cleared.\n")
    
    def initialize_audio(self):
        try:
            self.audio = pyaudio.PyAudio()
            self.update_text("Audio system initialized.")
            self.find_loopback_device()
        except Exception as e:
            self.update_text(f"Error initializing audio: {str(e)}")
    
    def find_loopback_device(self):
        """Find and store the loopback device index"""
        found_devices = []
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            device_name = device_info.get('name', '')
            if device_info.get('maxInputChannels', 0) > 0:
                found_devices.append(f"Device {i}: {device_name} (in: {device_info.get('maxInputChannels')}, out: {device_info.get('maxOutputChannels')})")
                
                # Look for common loopback device names
                if any(keyword in device_name.lower() for keyword in ["stereo mix", "what u hear", "loopback", "wave out", "monitor"]):
                    self.loopback_device_index = i
                    self.update_text(f"Found loopback device: {device_name} (Device {i})")
                    return
        
        # Log all found devices
        self.update_text("All input devices:")
        for device in found_devices:
            self.update_text(device)
            
        # Default to default input if no loopback device found
        default_input = self.audio.get_default_input_device_info()
        self.loopback_device_index = default_input['index']
        self.update_text(f"No loopback device found. Using default input: {default_input['name']} (Device {self.loopback_device_index})")
        self.update_text("NOTE: Default device will likely capture microphone, not system audio.")
        self.update_text("Enable 'Stereo Mix' in Windows Sound settings or use a virtual audio cable.")
    
    def list_audio_devices(self):
        """Debug function to list all audio devices"""
        self.text_area.delete(1.0, tk.END)
        self.update_text("Available Audio Devices:")
        
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            device_name = device_info.get('name', '')
            inputs = device_info.get('maxInputChannels', 0)
            outputs = device_info.get('maxOutputChannels', 0)
            self.update_text(f"Device {i}: {device_name}")
            self.update_text(f"  Input channels: {inputs}, Output channels: {outputs}")
            self.update_text(f"  Default sample rate: {device_info.get('defaultSampleRate')}")
            
            if i == self.loopback_device_index:
                self.update_text(f"  ** SELECTED FOR CAPTURE **")
            
            self.update_text("")
        
        default_input = self.audio.get_default_input_device_info()
        default_output = self.audio.get_default_output_device_info()
        self.update_text(f"Default input: Device {default_input['index']} - {default_input['name']}")
        self.update_text(f"Default output: Device {default_output['index']} - {default_output['name']}")
        
        self.update_text("\nTo capture system audio, enable 'Stereo Mix' in Windows Sound settings")
        self.update_text("or use a virtual audio cable solution like VB-Cable.")
    
    def select_model(self):
        model_dir = filedialog.askdirectory(title="Select Vosk Model Directory")
        if model_dir:
            self.model_path = model_dir
            self.status_label.config(text=f"Model: {os.path.basename(model_dir)}")
            self.update_text(f"Selected model: {os.path.basename(model_dir)}")
    
    def update_text(self, text):
        """Add text to the transcription window and scroll to show it"""
        self.text_area.insert(tk.END, text + "\n")
        self.text_area.see(tk.END)
    
    def start_transcription(self):
        if self.is_transcribing:
            return
        
        if not self.model_path:
            self.update_text("Please select a Vosk model directory first.")
            return
        
        try:
            # Load the model
            self.update_text("Loading speech recognition model...")
            self.model = Model(self.model_path)
            self.recognizer = KaldiRecognizer(self.model, 16000)
            
            # Update UI
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_label.config(text="Transcribing...")
            
            # Start transcription in a separate thread
            self.is_transcribing = True
            self.transcription_thread = threading.Thread(target=self.transcribe)
            self.transcription_thread.daemon = True
            self.transcription_thread.start()
            
            self.update_text("Started transcription. Speaking will appear here...")
            
        except Exception as e:
            self.update_text(f"Error starting transcription: {str(e)}")
            self.status_label.config(text="Error")
    
    def stop_transcription(self):
        if not self.is_transcribing:
            return
        
        self.is_transcribing = False
        
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
        
        # Update UI
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Stopped")
        self.update_text("Transcription stopped.")
    
    def transcribe(self):
        try:
            # Setup audio capture parameters
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 16000
            CHUNK = 4000
            
            self.update_text(f"Opening audio stream from device {self.loopback_device_index}")
            
            # Open stream for capturing
            self.audio_stream = self.audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                input_device_index=self.loopback_device_index
            )
            
            self.update_text("Audio stream opened successfully")
            silent_chunks = 0
            
            while self.is_transcribing:
                # Read audio data
                try:
                    data = self.audio_stream.read(CHUNK, exception_on_overflow=False)
                    
                    # Simple check if audio data is not silent
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    if np.abs(audio_data).mean() < 100:
                        silent_chunks += 1
                        if silent_chunks >= 10:  # About 2.5 seconds of silence
                            silent_chunks = 0
                            self.root.after(0, lambda: self.status_label.config(text="Listening (silent)"))
                        continue
                    else:
                        silent_chunks = 0
                        self.root.after(0, lambda: self.status_label.config(text="Transcribing..."))
                    
                    # Process audio for transcription
                    if self.recognizer.AcceptWaveform(data):
                        result = self.recognizer.Result()
                        result_dict = json.loads(result)
                        if 'text' in result_dict and result_dict['text'].strip():
                            transcript_text = result_dict['text']
                            # Update UI from the main thread
                            self.root.after(0, lambda t=transcript_text: self.update_text(t))
                    else:
                        # Get partial results
                        partial = json.loads(self.recognizer.PartialResult())
                        if 'partial' in partial and partial['partial'].strip():
                            partial_text = partial['partial']
                            # Update status with partial text
                            self.root.after(0, lambda t=partial_text: self.status_label.config(text=f"Partial: {t[:20]}{'...' if len(t) > 20 else ''}"))
                            
                except IOError as e:
                    # Handle buffer overflow gracefully
                    if "Input overflowed" in str(e):
                        continue
                    else:
                        self.root.after(0, lambda e=e: self.update_text(f"Audio error: {str(e)}"))
                except Exception as e:
                    self.root.after(0, lambda e=e: self.update_text(f"Error processing audio: {str(e)}"))
                
        except Exception as e:
            self.root.after(0, lambda e=e: self.update_text(f"Transcription error: {str(e)}"))
            self.root.after(0, lambda: self.status_label.config(text="Error"))
            
        finally:
            # Clean up
            self.is_transcribing = False
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))

def main():
    root = tk.Tk()
    app = FloatingTranscriptionWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
