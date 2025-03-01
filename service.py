"""
Android background service for system audio transcription
This module handles the service that runs in the background to capture 
and transcribe system audio on Android.
"""

from jnius import autoclass
from android.permissions import check_permission, Permission

import threading
import time
import os
import json

# Android classes
Service = autoclass('android.app.Service')
Intent = autoclass('android.content.Intent')
PendingIntent = autoclass('android.app.PendingIntent')
Notification = autoclass('android.app.Notification')
NotificationChannel = autoclass('android.app.NotificationChannel')
NotificationManager = autoclass('android.app.NotificationManager')
Context = autoclass('android.content.Context')
MediaProjectionManager = autoclass('android.media.projection.MediaProjectionManager')
AudioPlaybackCaptureConfiguration = autoclass('android.media.AudioPlaybackCaptureConfiguration')
AudioFormat = autoclass('android.media.AudioFormat')
AudioRecord = autoclass('android.media.AudioRecord')
File = autoclass('java.io.File')
Environment = autoclass('android.os.Environment')
Build = autoclass('android.os.Build')
AudioAttributes = autoclass('android.media.AudioAttributes')

# For speech recognition
from vosk import Model, KaldiRecognizer

# Python activity for bridging Python and Java
PythonActivity = autoclass('org.kivy.android.PythonActivity')


class TranscriptionService:
    """Android service for capturing and transcribing system audio"""
    
    # Singleton instance
    _instance = None
    
    # Class initializer
    def __init__(self):
        self.service = None
        self.notification_manager = None
        self.media_projection = None
        self.projection_code = -1
        self.projection_data = None
        self.transcriber = None
        self.audio_record = None
        self.running = False
        self.transcription_callback = None
        self.current_text = "Waiting for audio..."
        
    @classmethod
    def get_instance(cls):
        """Get or create the service singleton"""
        if cls._instance is None:
            cls._instance = TranscriptionService()
        return cls._instance
    
    def start(self, projection_code, projection_data, callback=None):
        """
        Start the transcription service with the media projection
        
        Args:
            projection_code: Result code from media projection request
            projection_data: Intent data from media projection request
            callback: Function to call with transcription updates
        """
        self.projection_code = projection_code
        self.projection_data = projection_data
        self.transcription_callback = callback
        
        # Create a notification channel (required for Android 8+)
        self._create_notification_channel()
        
        # Start service in foreground
        self._start_foreground()
        
        # Start transcription in a separate thread
        self.running = True
        threading.Thread(target=self._capture_audio).start()
    
    def stop(self):
        """Stop the transcription service"""
        self.running = False
        
        if self.audio_record:
            self.audio_record.stop()
            self.audio_record.release()
            self.audio_record = None
        
        # Stop foreground service
        if self.service:
            self.service.stopForeground(True)
            self.service.stopSelf()
    
    def _create_notification_channel(self):
        """Create notification channel for the service"""
        # Get notification manager
        context = PythonActivity.mActivity.getApplicationContext()
        self.notification_manager = context.getSystemService(Context.NOTIFICATION_SERVICE)
        
        # Create channel (Android 8+)
        if Build.VERSION.SDK_INT >= 26:
            channel = NotificationChannel(
                "transcription_service", 
                "Audio Transcription", 
                NotificationManager.IMPORTANCE_LOW
            )
            channel.setDescription("Used for the system audio transcription service")
            self.notification_manager.createNotificationChannel(channel)
    
    def _start_foreground(self):
        """Start the service in foreground with a notification"""
        # Get current context
        context = PythonActivity.mActivity.getApplicationContext()
        
        # Create pending intent for notification
        intent = Intent(context, PythonActivity)
        intent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP)
        pending_intent = PendingIntent.getActivity(context, 0, intent, PendingIntent.FLAG_IMMUTABLE)
        
        # Create notification
        if Build.VERSION.SDK_INT >= 26:
            builder = Notification.Builder(context, "transcription_service")
        else:
            builder = Notification.Builder(context)
        
        notification = builder.setContentTitle("System Audio Transcription") \
            .setContentText("Transcribing system audio...") \
            .setContentIntent(pending_intent) \
            .setOngoing(True) \
            .build()
            
        # Start foreground service
        self.service = PythonActivity.mActivity
        self.service.startForeground(1, notification)
    
    def _capture_audio(self):
        """Capture and transcribe system audio"""
        try:
            # Get media projection manager
            context = PythonActivity.mActivity.getApplicationContext()
            projection_manager = context.getSystemService(Context.MEDIA_PROJECTION_SERVICE)
            
            # Get media projection from saved code and data
            media_projection = projection_manager.getMediaProjection(
                self.projection_code, 
                self.projection_data
            )
            
            if media_projection is None:
                self._update_transcription("Failed to start media projection")
                return
            
            # Setup for Vosk speech recognition
            model_path = PythonActivity.mActivity.getExternalFilesDir(None).getAbsolutePath() + "/vosk-model-small-en-us"
            if not os.path.exists(model_path):
                self._update_transcription("Speech recognition model not found!")
                return
                
            model = Model(model_path)
            self.transcriber = KaldiRecognizer(model, 16000)
            
            # Calculate minimum buffer size
            min_buffer_size = AudioRecord.getMinBufferSize(
                16000,  # Sample rate
                AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT
            )
            
            # Create configuration for capturing playback
            config = AudioPlaybackCaptureConfiguration.Builder(media_projection).build()
            
            # Create an audio format for recording
            audio_format = AudioFormat.Builder() \
                .setSampleRate(16000) \
                .setChannelMask(AudioFormat.CHANNEL_IN_MONO) \
                .setEncoding(AudioFormat.ENCODING_PCM_16BIT) \
                .build()
                
            # Set up audio record with playback capture configuration
            builder = AudioRecord.Builder() \
                .setAudioFormat(audio_format) \
                .setBufferSizeInBytes(min_buffer_size * 2)
                
            # Set the audio capture configuration
            builder.setAudioPlaybackCaptureConfig(config)
            
            # Build the audio record
            self.audio_record = builder.build()
            
            # Start recording
            self.audio_record.startRecording()
            
            # Process audio in chunks
            buffer_size = min_buffer_size
            buffer = bytearray(buffer_size)
            
            while self.running:
                # Read audio data
                read_size = self.audio_record.read(buffer, 0, buffer_size)
                
                if read_size > 0:
                    # Process audio with Vosk
                    if self.transcriber.AcceptWaveform(bytes(buffer[:read_size])):
                        result = json.loads(self.transcriber.Result())
                        if 'text' in result and result['text']:
                            self._update_transcription(result['text'])
                    else:
                        # Get partial results
                        partial = json.loads(self.transcriber.PartialResult())
                        if 'partial' in partial and partial['partial']:
                            self._update_transcription(f"[...] {partial['partial']}")
                
                # Short sleep to prevent thread from hogging CPU
                time.sleep(0.01)
                
            # Clean up
            if self.audio_record:
                self.audio_record.stop()
                self.audio_record.release()
                self.audio_record = None
                
        except Exception as e:
            self._update_transcription(f"Error: {str(e)}")
    
    def _update_transcription(self, text):
        """Update current transcription and notify callback"""
        self.current_text = text
        
        # Notify callback if available
        if self.transcription_callback:
            self.transcription_callback(text)


def start_service(projection_code, projection_data, callback=None):
    """Start the transcription service"""
    service = TranscriptionService.get_instance()
    service.start(projection_code, projection_data, callback)
    return service


def stop_service():
    """Stop the transcription service"""
    service = TranscriptionService.get_instance()
    service.stop()
