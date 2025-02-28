package com.systemaudiotranscriber;

import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.media.audiofx.AudioPlaybackCaptureConfiguration;
import android.os.Build;
import android.util.Base64;
import androidx.annotation.NonNull;
import androidx.annotation.RequiresApi;
import com.facebook.react.bridge.ReactApplicationContext;
import com.facebook.react.bridge.ReactContextBaseJavaModule;
import com.facebook.react.bridge.ReactMethod;
import com.facebook.react.modules.core.DeviceEventManagerModule;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

@RequiresApi(api = Build.VERSION_CODES.Q)
public class SystemAudioModule extends ReactContextBaseJavaModule {
    private static final int SAMPLE_RATE = 16000;
    private final ReactApplicationContext reactContext;
    private AudioRecord audioRecord;
    private boolean isRecording = false;

    public SystemAudioModule(ReactApplicationContext context) {
        super(context);
        this.reactContext = context;
    }

    @NonNull
    @Override
    public String getName() {
        return "SystemAudioModule";
    }

    @ReactMethod
    public void startCapture() {
        AudioPlaybackCaptureConfiguration config = new AudioPlaybackCaptureConfiguration.Builder(getReactApplicationContext())
                .addMatchingUsage(AudioFormat.ENCODING_PCM_16BIT)
                .build();

        audioRecord = new AudioRecord.Builder()
                .setAudioFormat(new AudioFormat.Builder()
                        .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                        .setSampleRate(SAMPLE_RATE)
                        .setChannelMask(AudioFormat.CHANNEL_IN_MONO)
                        .build())
                .setAudioPlaybackCaptureConfig(config)
                .build();

        audioRecord.startRecording();
        isRecording = true;

        new Thread(() -> {
            ByteBuffer buffer = ByteBuffer.allocateDirect(4096).order(ByteOrder.LITTLE_ENDIAN);
            while (isRecording) {
                int result = audioRecord.read(buffer, buffer.capacity());
                if (result > 0) {
                    byte[] audioData = new byte[result];
                    buffer.get(audioData, 0, result);
                    buffer.clear();

                    String base64Audio = Base64.encodeToString(audioData, Base64.NO_WRAP);
                    sendEvent("onAudioData", base64Audio);
                }
            }
        }).start();
    }

    @ReactMethod
    public void stopCapture() {
        if (audioRecord != null) {
            isRecording = false;
            audioRecord.stop();
            audioRecord.release();
            audioRecord = null;
        }
    }

    private void sendEvent(String eventName, String data) {
        reactContext.getJSModule(DeviceEventManagerModule.RCTDeviceEventEmitter.class).emit(eventName, data);
    }
}
