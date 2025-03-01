from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.utils import platform

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout

import threading
import time
import os

# Import platform-specific modules conditionally
if platform == 'android':
    from jnius import autoclass
    from android.permissions import request_permissions, check_permission, Permission
    from android import mActivity
    
    # Android classes needed for media projection
    Intent = autoclass('android.content.Intent')
    MediaProjectionManager = autoclass('android.media.projection.MediaProjectionManager')
    Context = autoclass('android.content.Context')
    
    # For speech recognition using Vosk
    try:
        from vosk import Model, KaldiRecognizer
        import json
    except ImportError:
        pass
    
    # Import our service implementation
    from service import start_service, stop_service


class PatternLock(MDBoxLayout):
    """Pattern Lock screen for authentication"""
    def __init__(self, unlock_callback, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.unlock_callback = unlock_callback
        self.pattern = []
        self.correct_pattern = [1, 5, 9, 6, 3]  # Example pattern: diagonal + L shape
        
        # Title
        self.add_widget(Label(
            text='Draw Pattern to Unlock',
            size_hint=(1, 0.2)
        ))
        
        # Pattern grid
        self.grid_layout = BoxLayout(
            orientation='vertical',
            size_hint=(1, 0.6)
        )
        
        # Create 3x3 grid of buttons
        for i in range(3):
            row = BoxLayout()
            for j in range(3):
                btn_id = i * 3 + j + 1  # Button IDs: 1-9
                btn = Button(
                    text=str(btn_id),
                    on_press=lambda x, id=btn_id: self.add_to_pattern(id)
                )
                row.add_widget(btn)
            self.grid_layout.add_widget(row)
            
        self.add_widget(self.grid_layout)
        
        # Status label
        self.status_label = Label(
            text='Draw your pattern',
            size_hint=(1, 0.1)
        )
        self.add_widget(self.status_label)
        
        # Control buttons
        controls = BoxLayout(size_hint=(1, 0.1))
        
        clear_btn = Button(
            text='Clear',
            on_press=self.clear_pattern
        )
        controls.add_widget(clear_btn)
        
        submit_btn = Button(
            text='Submit',
            on_press=self.check_pattern
        )
        controls.add_widget(submit_btn)
        
        self.add_widget(controls)
    
    def add_to_pattern(self, btn_id):
        """Add button to current pattern sequence"""
        self.pattern.append(btn_id)
        # Update status to show progress
        self.status_label.text = f'Pattern: {"* " * len(self.pattern)}'
    
    def clear_pattern(self, instance):
        """Clear the current pattern"""
        self.pattern = []
        self.status_label.text = 'Pattern cleared'
    
    def check_pattern(self, instance):
        """Verify if pattern matches the correct one"""
        if self.pattern == self.correct_pattern:
            self.status_label.text = 'Pattern correct!'
            # Call the unlock callback after successful authentication
            self.unlock_callback()
        else:
            self.status_label.text = 'Incorrect pattern. Try again.'
            self.pattern = []


class TranscriptionPopup(FloatLayout):
    """Floating popup that displays transcription text"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Background with some transparency
        self.size_hint = (0.8, 0.3)
        self.pos_hint = {'center_x': 0.5, 'top': 0.9}
        
        # Main layout
        self.layout = BoxLayout(orientation='vertical')
        
        # Transcription text area
        self.transcription_label = Label(
            text='Waiting for audio...',
            halign='left',
            valign='top',
            size_hint=(1, 0.8),
            text_size=(Window.width * 0.75, None)
        )
        self.layout.add_widget(self.transcription_label)
        
        # Control panel
        controls = BoxLayout(
            size_hint=(1, 0.2),
            spacing=10
        )
        
        # Resize handles
        self.minimize_btn = Button(
            text='-',
            size_hint=(0.15, 1)
        )
        self.minimize_btn.bind(on_press=self.minimize)
        
        self.maximize_btn = Button(
            text='+',
            size_hint=(0.15, 1)
        )
        self.maximize_btn.bind(on_press=self.maximize)
        
        # Close button
        self.close_btn = Button(
            text='×',
            size_hint=(0.15, 1)
        )
        self.close_btn.bind(on_press=self.close)
        
        controls.add_widget(self.minimize_btn)
        controls.add_widget(self.maximize_btn)
        controls.add_widget(self.close_btn)
        
        self.layout.add_widget(controls)
        self.add_widget(self.layout)
        
        # For dragging the popup
        self.touch_start = None
    
    def on_touch_down(self, touch):
        """Handle touch events for dragging the popup"""
        if self.collide_point(*touch.pos):
            # Store touch position for dragging
            self.touch_start = touch.pos
            return True
        return super().on_touch_down(touch)
    
    def on_touch_move(self, touch):
        """Move popup when dragged"""
        if self.touch_start:
            # Calculate how much to move
            dx = touch.x - self.touch_start[0]
            dy = touch.y - self.touch_start[1]
            
            # Update position
            self.pos_hint = {
                'center_x': self.pos_hint['center_x'] + dx / Window.width,
                'top': self.pos_hint['top'] + dy / Window.height
            }
            
            # Update touch start position
            self.touch_start = touch.pos
            return True
        return super().on_touch_move(touch)
    
    def on_touch_up(self, touch):
        """Reset touch start position"""
        self.touch_start = None
        return super().on_touch_up(touch)
    
    def update_text(self, text):
        """Update the transcription text"""
        self.transcription_label.text = text
    
    def minimize(self, instance):
        """Reduce the size of the popup"""
        self.size_hint = (0.5, 0.2)
    
    def maximize(self, instance):
        """Increase the size of the popup"""
        self.size_hint = (0.8, 0.4)
    
    def close(self, instance):
        """Hide the popup"""
        self.parent.remove_widget(self)


class MainScreen(MDScreen):
    """Main application screen with pattern lock"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.popup = None
        self.service = None
        self.projection_manager = None
        
        # Media Projection request code
        self.MEDIA_PROJECTION_REQUEST = 1000
        
        # Start with pattern lock
        self.pattern_lock = PatternLock(
            unlock_callback=self.show_popup
        )
        self.add_widget(self.pattern_lock)
    
    def show_popup(self):
        """Show the transcription popup after successful authentication"""
        # Remove pattern lock
        self.remove_widget(self.pattern_lock)
        
        # Add a message about starting the service
        self.starting_label = Label(
            text="Starting transcription service...\nRequesting necessary permissions.",
            halign='center'
        )
        self.add_widget(self.starting_label)
        
        # Request necessary permissions
        if platform == 'android':
            # Request permissions
            permissions = [
                Permission.RECORD_AUDIO,
                Permission.SYSTEM_ALERT_WINDOW,
                'android.permission.FOREGROUND_SERVICE',
                'android.permission.CAPTURE_AUDIO_OUTPUT'
            ]
            request_permissions(permissions, self._on_permissions)
        else:
            # Skip permission check on non-Android platforms
            self._create_popup()
    
    def _on_permissions(self, permissions, grants):
        """Callback for permission requests"""
        # Check if all permissions were granted
        if all(grants):
            # Request media projection permission
            self._request_media_projection()
        else:
            # Show error if permissions were denied
            self.clear_widgets()
            error_label = Label(
                text="Cannot start transcription without required permissions.",
                halign='center'
            )
            retry_button = Button(
                text="Try Again",
                size_hint=(0.5, 0.1),
                pos_hint={'center_x': 0.5, 'center_y': 0.4}
            )
            retry_button.bind(on_press=lambda x: self.__init__())
            
            self.add_widget(error_label)
            self.add_widget(retry_button)
    
    def _request_media_projection(self):
        """Request MediaProjection permission from the user"""
        if platform == 'android':
            # Get the MediaProjectionManager
            context = mActivity.getApplicationContext()
            self.projection_manager = context.getSystemService(Context.MEDIA_PROJECTION_SERVICE)
            
            # Create media projection intent
            intent = self.projection_manager.createScreenCaptureIntent()
            
            # Set up activity result handling
            def on_activity_result(request_code, result_code, data):
                if request_code == self.MEDIA_PROJECTION_REQUEST:
                    if result_code == -1:  # RESULT_OK
                        # Media projection permission granted
                        self._create_popup_with_service(result_code, data)
                    else:
                        # Permission denied
                        self.clear_widgets()
                        error_label = Label(
                            text="Media projection permission denied. Cannot transcribe system audio.",
                            halign='center'
                        )
                        retry_button = Button(
                            text="Try Again",
                            size_hint=(0.5, 0.1),
                            pos_hint={'center_x': 0.5, 'center_y': 0.4}
                        )
                        retry_button.bind(on_press=lambda x: self._request_media_projection())
                        
                        self.add_widget(error_label)
                        self.add_widget(retry_button)
            
            # Register activity result callback
            from android import activity
            activity.bind(on_activity_result=on_activity_result)
            
            # Start activity for result
            mActivity.startActivityForResult(intent, self.MEDIA_PROJECTION_REQUEST)
        else:
            # Create popup directly on non-Android platforms
            self._create_popup()
    
    def _create_popup_with_service(self, projection_code, projection_data):
        """Create and show the transcription popup with service started"""
        # Clear the main screen
        self.clear_widgets()
        
        # Create floating popup
        self.popup = TranscriptionPopup()
        self.add_widget(self.popup)
        
        # Start the transcription service with media projection data
        if platform == 'android':
            self.service = start_service(
                projection_code,
                projection_data,
                callback=self.update_transcription
            )
        else:
            self.popup.update_text("System audio transcription only works on Android")
    
    def _create_popup(self):
        """Create popup for non-Android platforms (for development)"""
        # Clear the main screen
        self.clear_widgets()
        
        # Create floating popup
        self.popup = TranscriptionPopup()
        self.add_widget(self.popup)
        
        # Set demo text
        self.popup.update_text("System audio transcription only works on Android")
    
    def update_transcription(self, text):
        """Update transcription text in the popup"""
        if self.popup:
            def update_ui(*args):
                self.popup.update_text(text)
            
            # Update UI on the main thread
            Clock.schedule_once(update_ui)
    
    def on_pause(self):
        """Allow the app to pause without stopping"""
        return True
    
    def on_resume(self):
        """Handle app resumption"""
        pass
    
    def on_stop(self):
        """Stop transcription when app is closed"""
        if platform == 'android' and self.service:
            stop_service()


class SystemAudioTranscriberApp(MDApp):
    """Main application class"""
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Dark"
        return MainScreen()


if __name__ == '__main__':
    SystemAudioTranscriberApp().run()
