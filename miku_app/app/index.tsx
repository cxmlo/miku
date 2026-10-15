import React, { useState, useEffect, useRef } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, ScrollView, Switch, Image, Linking, Modal, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as IntentLauncher from 'expo-intent-launcher';
import { Audio } from 'expo-av';
import { useNavigation, useRouter } from 'expo-router';
import { FontAwesome5, Ionicons, Feather } from '@expo/vector-icons';
import { SvgUri } from 'react-native-svg';
import { getBaseUrl } from '../utils/network';
import { useWebSocket } from '../context/WebSocketContext';
import { useAssistant } from '../context/AssistantContext';
import { AssistantOverlay } from '../components/AssistantOverlay';

export default function App() {
  const { messages, mikuState, statusText, setStatusText, isConnected, sendMessage, sendAudio, serverIp, widgetData, setWidgetData, secretRequest, setSecretRequest } = useWebSocket();
  
  const [inputText, setInputText] = useState('');
  const [isAlwaysOn, setIsAlwaysOn] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  
  const [fullScreenImage, setFullScreenImage] = useState<string | null>(null);
  
  const [dots, setDots] = useState('');
  const scrollViewRef = useRef<ScrollView>(null);
  
  const navigation = useNavigation();
  const router = useRouter();

  const [secretValues, setSecretValues] = useState<{ [key: string]: string }>({});

  const submitSecret = async () => {
    if (!serverIp || Object.keys(secretValues).length === 0) return;
    
    let payload = { ...secretValues };
    if (payload.custom_key && payload.custom_value) {
      payload[payload.custom_key] = payload.custom_value;
      delete payload.custom_key;
      delete payload.custom_value;
    }

    try {
      const res = await fetch(`${getBaseUrl(serverIp)}/api/secrets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-api-key': 'miku_secure_key_2026' },
        body: JSON.stringify({ secrets: payload })
      });
      if (res.ok) {
        Alert.alert("Éxito", "Secretos guardados de forma segura.");
        setSecretRequest(null);
        setSecretValues({});
        sendMessage("Listo, ya he guardado las claves de forma segura en el panel.");
      } else {
        Alert.alert("Error", "No se pudo guardar el secreto.");
      }
    } catch(e) {
      Alert.alert("Error de red", "No se pudo conectar al servidor.");
    }
  };

  // --- Miku States & Weather Updates ---
  const { isAssistantMode, expandToFullApp, dismissOverlay } = useAssistant();

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (mikuState === 'thinking') {
      let count = 0;
      interval = setInterval(() => {
        count = (count + 1) % 4;
        setDots('.'.repeat(count));
      }, 500);
    } else {
      setDots('');
    }
    return () => clearInterval(interval);
  }, [mikuState]);

  // Removed navigation.setOptions override so layout handles header

  // Pedir permisos de audio y mostrar prompt de asistente
  useEffect(() => {
    (async () => {
      await Audio.requestPermissionsAsync();
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      // Prompt para Asistente Predeterminado
      try {
        const hasPrompted = await AsyncStorage.getItem('miku_assistant_prompted');
        if (!hasPrompted) {
          Alert.alert(
            "Asistente Predeterminado",
            "¿Quieres configurar a Miku como tu asistente principal de IA? Esto te permitirá llamarla manteniendo presionado el botón de inicio o deslizando desde la esquina inferior.",
            [
              { text: "Más tarde", onPress: () => AsyncStorage.setItem('miku_assistant_prompted', 'true'), style: "cancel" },
              { 
                text: "Configurar", 
                onPress: () => {
                  AsyncStorage.setItem('miku_assistant_prompted', 'true');
                  IntentLauncher.startActivityAsync('android.settings.VOICE_INPUT_SETTINGS').catch(() => {
                     // Fallback si VOICE_INPUT_SETTINGS no está en la versión de Android
                     IntentLauncher.startActivityAsync('android.settings.MANAGE_DEFAULT_APPS_SETTINGS').catch(() => {});
                  });
                } 
              }
            ]
          );
        }
      } catch (e) {}
    })();
  }, []);

  const sendMessageText = async (textToSend: string) => {
    if (textToSend.trim().length === 0) return;
    setInputText('');
    await sendMessage(textToSend);
  };

  const getWeatherIcon = (condition: string) => {
    if (!condition) return 'cloud';
    const c = condition.toLowerCase();
    if (c.includes('lluvia') || c.includes('rain')) return 'cloud-rain';
    if (c.includes('nube') || c.includes('nublado') || c.includes('cloud')) return 'cloud';
    if (c.includes('sol') || c.includes('despejado') || c.includes('sun') || c.includes('clear')) return 'sun';
    if (c.includes('nieve') || c.includes('snow')) return 'cloud-snow';
    if (c.includes('tormenta') || c.includes('storm') || c.includes('trueno')) return 'cloud-lightning';
    return 'cloud';
  };

  const startRecording = async () => {
    if (isRecording || recording) return;
    try {
      setIsRecording(true);
      setStatusText("> LISTENING...");
      const { recording } = await Audio.Recording.createAsync( Audio.RecordingOptionsPresets.HIGH_QUALITY );
      setRecording(recording);
    } catch (err) {
      console.error('Failed to start recording', err);
      setIsRecording(false);
      setStatusText("> IDLE");
    }
  };

  const stopRecordingAndSend = async () => {
    setIsRecording(false);
    if (!recording) return;

    try {
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      setRecording(null);
      
      if (!uri) return;
      await sendAudio(uri);
    } catch (err) {
      console.error('Error procesando audio', err);
    }
  };

  const handleAuthResponse = async (taskId: string, action: string) => {
    try {
      await fetch(`${getBaseUrl(serverIp || '127.0.0.1')}/api/mcp/auth_response/${taskId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action })
      });
      setWidgetData(null);
    } catch (e) {
      Alert.alert('Error', 'No se pudo enviar la respuesta.');
    }
  };

  // --- Rendering ---
  
  if (isAssistantMode) {
    return (
      <AssistantOverlay
        mikuState={mikuState}
        isRecording={isRecording}
        startRecording={startRecording}
        stopRecordingAndSend={stopRecordingAndSend}
        messages={messages}
        expandToFullApp={expandToFullApp}
        dismissOverlay={dismissOverlay}
        serverIp={serverIp}
        dots={dots}
      />
    );
  }

  return (
    <KeyboardAvoidingView 
      style={styles.container} 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={0}
    >
      {widgetData && (
        <View style={styles.floatingWidget}>
          <TouchableOpacity 
            style={styles.closeWidgetBtn}
            onPress={() => setWidgetData(null)}
          >
            <Feather name="x" size={20} color="#fff" />
          </TouchableOpacity>
          {widgetData.type === 'weather' && (
            <View style={{flexDirection: 'row', alignItems: 'center'}}>
              <View style={{marginRight: 15, marginLeft: 5}}>
                {widgetData.args[5] ? (
                  <SvgUri
                    width="60"
                    height="60"
                    uri={`${getBaseUrl(serverIp || '127.0.0.1')}${widgetData.args[5]}`}
                  />
                ) : (
                  <Feather name={getWeatherIcon(widgetData.args[2])} size={40} color="#fff" />
                )}
              </View>
              <View>
                <Text style={{color: '#fff', fontSize: 18, fontWeight: 'bold'}}>{widgetData.args[0]}</Text>
                <Text style={{color: '#aaa', fontSize: 14}}>{widgetData.args[1]} | {widgetData.args[2]} | {widgetData.args[3]}</Text>
                <Text style={{color: '#aaa', fontSize: 14}}>Humedad: {widgetData.args[4]}</Text>
              </View>
            </View>
          )}

          {widgetData.type === 'mcp_auth' && (
            <View style={{flexDirection: 'column', padding: 5}}>
              <Text style={{color: '#fff', fontSize: 16, fontWeight: 'bold', fontFamily: 'monospace', marginBottom: 10, textAlign: 'center', backgroundColor: '#300', padding: 5}}>
                ⚠️ AUTORIZACIÓN MCP ⚠️
              </Text>
              <Text style={{color: '#fff', fontFamily: 'monospace', fontSize: 12, marginBottom: 5}}>
                Miku solicita instalar: <Text style={{color: '#0ff'}}>{widgetData.args[1]}</Text>
              </Text>
              <Text style={{color: '#aaa', fontFamily: 'monospace', fontSize: 10, marginBottom: 10}}>
                Propósito: {widgetData.args[2]}
              </Text>
              <Text style={{color: '#aaa', fontFamily: 'monospace', fontSize: 10, marginBottom: 10}}>
                Comandos: {JSON.stringify(widgetData.args[4])}
              </Text>
              
              <View style={{flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', marginTop: 10}}>
                <TouchableOpacity 
                  style={{backgroundColor: '#000', padding: 8, borderWidth: 1, borderColor: '#fff', width: '48%', marginBottom: 10, alignItems: 'center'}}
                  onPress={() => Linking.openURL(widgetData.args[3])}
                >
                  <Text style={{color: '#fff', fontFamily: 'monospace', fontSize: 10}}>VER CÓDIGO</Text>
                </TouchableOpacity>
                <TouchableOpacity 
                  style={{backgroundColor: '#000', padding: 8, borderWidth: 1, borderColor: '#0f0', width: '48%', marginBottom: 10, alignItems: 'center'}}
                  onPress={() => handleAuthResponse(widgetData.args[0], 'approve')}
                >
                  <Text style={{color: '#0f0', fontFamily: 'monospace', fontSize: 10}}>✅ APROBAR</Text>
                </TouchableOpacity>
                <TouchableOpacity 
                  style={{backgroundColor: '#000', padding: 8, borderWidth: 1, borderColor: '#f00', width: '48%', alignItems: 'center'}}
                  onPress={() => handleAuthResponse(widgetData.args[0], 'reject')}
                >
                  <Text style={{color: '#f00', fontFamily: 'monospace', fontSize: 10}}>❌ RECHAZAR</Text>
                </TouchableOpacity>
                <TouchableOpacity 
                  style={{backgroundColor: '#000', padding: 8, borderWidth: 1, borderColor: '#0ff', width: '48%', alignItems: 'center'}}
                  onPress={() => handleAuthResponse(widgetData.args[0], 'search_another')}
                >
                  <Text style={{color: '#0ff', fontFamily: 'monospace', fontSize: 10}}>🔄 BUSCAR OTRO</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}
        </View>
      )}

      {/* Visualizer / Avatar Area */}
      <View style={styles.avatarContainer}>
        <View style={{ position: 'absolute', top: 10, right: 10, flexDirection: 'row', alignItems: 'center' }}>
          <View style={{ width: 10, height: 10, borderRadius: 5, backgroundColor: isConnected ? '#00ff00' : '#ff0000', marginRight: 5 }} />
          <Text style={{ color: '#fff', fontFamily: 'monospace', fontSize: 10 }}>{isConnected ? 'ONLINE' : 'OFFLINE'}</Text>
        </View>
        {serverIp && (
          <Image 
            source={{ uri: `${getBaseUrl(serverIp)}/api/desktop/miku_gif/${mikuState}` }} 
            style={styles.mikuGif}
          />
        )}
        <Text style={styles.statusText}>{statusText}</Text>
      </View>

      {/* Chat Area */}
      <ScrollView 
        ref={scrollViewRef}
        style={styles.chatContainer} 
        contentContainerStyle={{ padding: 10 }}
        onContentSizeChange={() => scrollViewRef.current?.scrollToEnd({ animated: true })}
      >
        {messages.map((msg) => (
          <View key={msg.id} style={[styles.messageBubble, msg.sender === 'user' ? styles.messageUser : styles.messageMiku]}>
            {msg.image_url && (
              <TouchableOpacity onPress={() => setFullScreenImage(`${getBaseUrl(serverIp || '127.0.0.1')}${msg.image_url}`)}>
                <Image source={{ uri: `${getBaseUrl(serverIp || '127.0.0.1')}${msg.image_url}` }} style={{ width: 250, height: 250, borderRadius: 5, marginBottom: 5 }} resizeMode="contain" />
              </TouchableOpacity>
            )}
            <Text style={[styles.messageText, msg.sender === 'user' ? styles.textUser : styles.textMiku]}>
              {msg.text}
            </Text>
          </View>
        ))}
        {mikuState === 'thinking' && (
          <View style={[styles.messageBubble, styles.messageMiku, { minWidth: 70, alignItems: 'center' }]}>
            <Text style={[styles.messageText, styles.textMiku, { fontSize: 20, lineHeight: 24 }]}>{dots}</Text>
          </View>
        )}
      </ScrollView>

      {/* Controls Area */}
      <View style={styles.controlsContainer}>
        
        {/* Toggle Always On Mic */}
        <View style={styles.toggleContainer}>
          <Text style={styles.retroText}>ALWAYS ON MIC:</Text>
          <Switch
            trackColor={{ false: '#333', true: '#fff' }}
            thumbColor={isAlwaysOn ? '#000' : '#888'}
            onValueChange={setIsAlwaysOn}
            value={isAlwaysOn}
          />
        </View>

        {/* Input & Push to Talk */}
        <View style={styles.inputRow}>
          <TextInput
            style={styles.textInput}
            placeholder="TYPE COMMAND..."
            placeholderTextColor="#666"
            value={inputText}
            onChangeText={setInputText}
            onSubmitEditing={() => sendMessageText(inputText)}
          />
          
          {isAlwaysOn ? (
            <View style={{flexDirection: 'row'}}>
              <TouchableOpacity style={styles.sendBtn} onPress={() => sendMessageText(inputText)}>
                <Text style={styles.sendBtnText}>SEND</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.sendBtn, {backgroundColor: '#300', borderColor: '#f00', marginLeft: 10}]}
                onPress={async () => {
                  try {
                    await fetch(`${getBaseUrl(serverIp || '127.0.0.1')}/api/stop`, { method: 'POST', headers: { 'x-api-key': 'miku_secure_key_2026' }});
                  } catch (e) {}
                }}
              >
                <Text style={[styles.sendBtnText, {color: '#f00'}]}>STOP</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <View style={{flexDirection: 'row'}}>
              <TouchableOpacity 
                style={[styles.micBtn, isRecording && styles.micBtnActive]}
                onPressIn={startRecording}
                onPressOut={stopRecordingAndSend}
              >
                <Text style={styles.micBtnText}>{isRecording ? 'REC' : 'MIC'}</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.micBtn, {backgroundColor: '#300', borderColor: '#f00', marginLeft: 10}]}
                onPress={async () => {
                  try {
                    await fetch(`${getBaseUrl(serverIp || '127.0.0.1')}/api/stop`, { method: 'POST', headers: { 'x-api-key': 'miku_secure_key_2026' }});
                  } catch (e) {}
                }}
              >
                <Text style={[styles.micBtnText, {color: '#f00'}]}>STOP</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

      </View>

      {/* Full Screen Image Modal */}
      <Modal visible={!!fullScreenImage} transparent={true} animationType="fade" onRequestClose={() => setFullScreenImage(null)}>
        <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.9)', justifyContent: 'center', alignItems: 'center' }}>
          <TouchableOpacity style={{ position: 'absolute', top: 40, right: 20, zIndex: 10, padding: 10 }} onPress={() => setFullScreenImage(null)}>
            <Feather name="x" size={32} color="#fff" />
          </TouchableOpacity>
          {fullScreenImage && (
            <Image source={{ uri: fullScreenImage }} style={{ width: '100%', height: '100%' }} resizeMode="contain" />
          )}
        </View>
      </Modal>

      {/* Secret Request Modal */}
      <Modal visible={!!secretRequest?.active} transparent={true} animationType="slide" onRequestClose={() => setSecretRequest(null)}>
        <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.8)', justifyContent: 'center', alignItems: 'center' }}>
          <View style={{ width: '85%', backgroundColor: '#111', padding: 20, borderRadius: 5, borderWidth: 1, borderColor: '#333' }}>
            <Text style={{ color: '#fff', fontFamily: 'monospace', fontSize: 16, marginBottom: 15, textAlign: 'center' }}>
              🔑 Gestor de Secretos
            </Text>
            <Text style={{ color: '#aaa', fontFamily: 'monospace', fontSize: 12, marginBottom: 20, textAlign: 'center' }}>
              Miku necesita credenciales para: {secretRequest?.service}
            </Text>
            
            {secretRequest?.fields?.length > 0 ? (
              secretRequest.fields.map((field) => (
                <TextInput
                  key={field}
                  style={[styles.textInput, { marginBottom: 15, width: '100%' }]}
                  placeholder={`Valor para ${field}`}
                  placeholderTextColor="#555"
                  value={secretValues[field] || ''}
                  onChangeText={(val) => setSecretValues(prev => ({...prev, [field]: val}))}
                />
              ))
            ) : (
              <>
                <TextInput
                  style={[styles.textInput, { marginBottom: 15, width: '100%' }]}
                  placeholder="Nombre de la Variable (ej. API_KEY)"
                  placeholderTextColor="#555"
                  value={secretValues['custom_key'] || ''}
                  onChangeText={(val) => setSecretValues(prev => ({...prev, custom_key: val}))}
                  autoCapitalize="characters"
                />
                <TextInput
                  style={[styles.textInput, { marginBottom: 20, width: '100%' }]}
                  placeholder="Valor del secreto / token"
                  placeholderTextColor="#555"
                  value={secretValues['custom_value'] || ''}
                  onChangeText={(val) => setSecretValues(prev => ({...prev, custom_value: val}))}
                />
              </>
            )}
            
            <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
              <TouchableOpacity onPress={() => setSecretRequest(null)} style={{ padding: 10 }}>
                <Text style={{ color: '#ff5555', fontFamily: 'monospace' }}>Cancelar</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={submitSecret} style={{ backgroundColor: '#fff', padding: 10, borderRadius: 2 }}>
                <Text style={{ color: '#000', fontFamily: 'monospace', fontWeight: 'bold' }}>Guardar Seguro</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  floatingWidget: {
    position: 'absolute',
    top: 10,
    left: 10,
    right: 10,
    backgroundColor: 'rgba(20, 20, 20, 0.95)',
    borderRadius: 15,
    padding: 15,
    zIndex: 9999,
    borderWidth: 1,
    borderColor: '#333',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.5,
    shadowRadius: 5,
    elevation: 10,
  },
  closeWidgetBtn: {
    position: 'absolute',
    top: 5,
    right: 5,
    padding: 5,
    zIndex: 10,
  },

  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  avatarContainer: {
    height: 250,
    justifyContent: 'center',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#333',
    backgroundColor: '#050505',
  },
  mikuGif: {
    width: 150,
    height: 150,
    resizeMode: 'contain',
    marginBottom: 10,
  },
  statusText: {
    color: '#fff',
    fontFamily: 'monospace',
    fontSize: 12,
  },
  chatContainer: {
    flex: 1,
    backgroundColor: '#000000',
  },
  messageBubble: {
    padding: 12,
    marginVertical: 4,
    maxWidth: '80%',
    borderWidth: 1,
    borderRadius: 2,
  },
  messageUser: {
    alignSelf: 'flex-end',
    backgroundColor: '#fff',
    borderColor: '#fff',
  },
  messageMiku: {
    alignSelf: 'flex-start',
    backgroundColor: '#000',
    borderColor: '#fff',
  },
  messageText: {
    fontFamily: 'monospace',
    fontSize: 14,
  },
  textUser: {
    color: '#000',
  },
  textMiku: {
    color: '#fff',
  },
  controlsContainer: {
    padding: 15,
    borderTopWidth: 1,
    borderTopColor: '#333',
    backgroundColor: '#050505',
  },
  toggleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  retroText: {
    color: '#fff',
    fontFamily: 'monospace',
    fontSize: 12,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  textInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#fff',
    color: '#fff',
    fontFamily: 'monospace',
    padding: 10,
    height: 45,
    marginRight: 10,
  },
  micBtn: {
    borderWidth: 1,
    borderColor: '#fff',
    width: 60,
    height: 45,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000',
  },
  micBtnActive: {
    backgroundColor: '#fff',
  },
  micBtnText: {
    color: '#fff',
    fontFamily: 'monospace',
    fontWeight: 'bold',
  },
  sendBtn: {
    borderWidth: 1,
    borderColor: '#fff',
    width: 60,
    height: 45,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
  },
  sendBtnText: {
    color: '#000',
    fontFamily: 'monospace',
    fontWeight: 'bold',
  }
});
