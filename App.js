import React, { useEffect, useState } from 'react';
import { View, Text, Button, StyleSheet, NativeEventEmitter, NativeModules } from 'react-native';
import { FloatingBubble } from 'react-native-floating-bubble';

const { SystemAudioModule } = NativeModules;
const eventEmitter = new NativeEventEmitter(SystemAudioModule);

const App = () => {
  const [transcription, setTranscription] = useState('');

  useEffect(() => {
    const subscription = eventEmitter.addListener('onAudioData', async (base64Audio) => {
      const text = await transcribeAudio(base64Audio);
      setTranscription(text);
    });

    return () => subscription.remove();
  }, []);

  const startTranscription = () => {
    SystemAudioModule.startCapture();
  };

  const stopTranscription = () => {
    SystemAudioModule.stopCapture();
  };

  const transcribeAudio = async (base64Audio) => {
    try {
      const response = await fetch('https://speech.googleapis.com/v1/speech:recognize?key=YOUR_GOOGLE_API_KEY', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          config: { encoding: 'LINEAR16', sampleRateHertz: 16000, languageCode: 'en-US' },
          audio: { content: base64Audio },
        }),
      });
      const json = await response.json();
      return json.results?.[0]?.alternatives?.[0]?.transcript || '';
    } catch (error) {
      console.error(error);
      return '';
    }
  };

  return (
    <View style={styles.container}>
      <Button title="Start" onPress={startTranscription} />
      <Button title="Stop" onPress={stopTranscription} />
      <FloatingBubble onPress={() => alert(transcription)}>
        <View style={styles.bubble}>
          <Text style={styles.text}>{transcription || 'Listening...'}</Text>
        </View>
      </FloatingBubble>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  bubble: { width: 150, height: 150, backgroundColor: 'white', borderRadius: 75, justifyContent: 'center', alignItems: 'center', elevation: 5 },
  text: { color: 'black', textAlign: 'center', padding: 10 },
});

export default App;
