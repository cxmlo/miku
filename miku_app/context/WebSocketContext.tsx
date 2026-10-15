import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import * as SecureStore from 'expo-secure-store';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { getBaseUrl, getWsUrl } from '../utils/network';
import { Audio } from 'expo-av';
import { AppState, AppStateStatus, Alert } from 'react-native';
import * as Clipboard from 'expo-clipboard';
import * as FileSystem from 'expo-file-system/legacy';
import { StorageAccessFramework } from 'expo-file-system/legacy';
import * as MediaLibrary from 'expo-media-library';
import * as IntentLauncher from 'expo-intent-launcher';
import { startMikuForegroundService, stopMikuForegroundService, updateForegroundNotification } from '../services/mikuForegroundService';

const SERVER_IP_KEY = 'miku_server_ip';
const API_KEY = 'miku_secure_key_2026';
const MIKU_DOWNLOADS_DIR = 'miku_downloads_dir';

type Message = { id: string; text: string; sender: string; image_url?: string };

type WidgetData = {
  type: string;
  args: any[];
} | null;

type WebSocketContextType = {
  ws: WebSocket | null;
  isConnected: boolean;
  messages: Message[];
  mikuState: string;
  statusText: string;
  widgetData: WidgetData;
  setWidgetData: React.Dispatch<React.SetStateAction<WidgetData>>;
  secretRequest: { active: boolean, service: string, fields: string[] } | null;
  setSecretRequest: React.Dispatch<React.SetStateAction<{ active: boolean, service: string, fields: string[] } | null>>;
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  sendMessage: (text: string) => Promise<void>;
  sendAudio: (uri: string) => Promise<void>;
  serverIp: string | null;
  setServerIp: React.Dispatch<React.SetStateAction<string | null>>;
  setStatusText: React.Dispatch<React.SetStateAction<string>>;
  connectWs: (ip: string) => void;
  sessionsList: {id: string, date: string, preview: string, pinned?: boolean, archived?: boolean, title?: string}[];
  loadSession: (id: string) => void;
  startNewSession: () => void;
  updateSession: (id: string, updates: Partial<{title: string, pinned: boolean, archived: boolean}>) => void;
  deleteSession: (id: string) => void;
};

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [mikuState, setMikuState] = useState('idle');
  const [statusText, setStatusText] = useState('> IDLE');
  const [serverIp, setServerIp] = useState<string | null>(null);
  const [widgetData, setWidgetData] = useState<WidgetData>(null);
  const [secretRequest, setSecretRequest] = useState<{ active: boolean, service: string, fields: string[] } | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const currentSoundRef = useRef<Audio.Sound | null>(null);
  const lastPlayedAudioRef = useRef<{ url: string, time: number }>({ url: '', time: 0 });
  const appState = useRef(AppState.currentState);
  const lastClip = useRef("");
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  const [sessionId, setSessionId] = useState(() => Date.now().toString());
  const [sessionsList, setSessionsList] = useState<{id: string, date: string, preview: string, pinned?: boolean, archived?: boolean, title?: string}[]>([]);

  useEffect(() => {
    Audio.setAudioModeAsync({
      playsInSilentModeIOS: true,
      staysActiveInBackground: true,
      shouldDuckAndroid: true,
    });
    
    AsyncStorage.getItem('miku_sessions_list').then(val => {
      if (val) setSessionsList(JSON.parse(val));
    });
  }, []);

  useEffect(() => {
    if (messages.length > 0) {
      AsyncStorage.setItem(`miku_chat_${sessionId}`, JSON.stringify(messages));
      setSessionsList(prev => {
        const existing = prev.find(s => s.id === sessionId);
        const previewText = messages[messages.length - 1].text.substring(0, 30) + '...';
        if (existing) {
           if (existing.preview === previewText) return prev;
           const newList = prev.map(s => s.id === sessionId ? { ...s, preview: previewText, date: new Date().toISOString() } : s);
           AsyncStorage.setItem('miku_sessions_list', JSON.stringify(newList));
           return newList;
        } else {
           const newList = [{ id: sessionId, date: new Date().toISOString(), preview: previewText }, ...prev];
           AsyncStorage.setItem('miku_sessions_list', JSON.stringify(newList));
           return newList;
        }
      });
    }
  }, [messages, sessionId]);

  const loadSession = async (id: string) => {
    const data = await AsyncStorage.getItem(`miku_chat_${id}`);
    if (data) {
       setSessionId(id);
       setMessages(JSON.parse(data));
    }
  };

  const startNewSession = () => {
    setSessionId(Date.now().toString());
    setMessages([]);
  };

  const updateSession = async (id: string, updates: Partial<{title: string, pinned: boolean, archived: boolean}>) => {
    const updatedList = sessionsList.map(s => s.id === id ? { ...s, ...updates } : s);
    setSessionsList(updatedList);
    await AsyncStorage.setItem('miku_sessions_list', JSON.stringify(updatedList));
  };

  const deleteSession = async (id: string) => {
    const updatedList = sessionsList.filter(s => s.id !== id);
    setSessionsList(updatedList);
    await AsyncStorage.setItem('miku_sessions_list', JSON.stringify(updatedList));
    await AsyncStorage.removeItem(`miku_session_${id}`);
    if (sessionId === id) {
      startNewSession();
    }
  };

  useEffect(() => {
    const initWS = async () => {
      const ip = await SecureStore.getItemAsync(SERVER_IP_KEY);
      if (ip) {
        setServerIp(ip);
        connectWs(ip);
      }
    };
    initWS();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      // Detener el foreground service al desmontar
      stopMikuForegroundService();
    };
  }, []);

  const reconnectAttempts = useRef(0);

  const connectWs = (ip: string) => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
    }
    
    const socket = new WebSocket(`${getWsUrl(ip)}/ws?token=${API_KEY}`);
    wsRef.current = socket;

    let pingInterval: ReturnType<typeof setInterval>;
    
    // Eliminamos el timeout estricto de 5s que causaba cierres prematuros en conexiones lentas

    socket.onopen = () => {
      setIsConnected(true);
      setWs(socket);
      reconnectAttempts.current = 0; // Reset backoff

      // Iniciar el Foreground Service para mantener la app viva en segundo plano
      startMikuForegroundService();

      // Fetch global daily history from server
      fetch(`${getBaseUrl(ip)}/history`, {
        headers: { 'x-api-key': API_KEY }
      })
      .then(res => res.json())
      .then(data => {
         if (data && data.messages && data.messages.length > 0) {
            setMessages(data.messages);
         }
      })
      .catch(e => console.error("[Miku] Error fetching history:", e));
      
      // Heartbeat ping every 10 seconds to keep connection alive safely
      pingInterval = setInterval(() => {
        if (socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: "ping" }));
        }
      }, 10000);
    };

    socket.onclose = () => {
      setIsConnected(false);
      setWs(null);
      if (pingInterval) clearInterval(pingInterval);
      
      // Actualizar la notificación para indicar reconexión silenciosa
      updateForegroundNotification('Reconectando con tu PC...');
      
      // Jitter & Exponential Backoff para reconexiones silenciosas (Máx 30s)
      const baseDelay = 3000;
      const attempt = reconnectAttempts.current;
      const delay = Math.min(baseDelay * Math.pow(1.5, attempt), 30000);
      reconnectAttempts.current += 1;
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      reconnectTimeoutRef.current = setTimeout(() => {
        if (serverIp || ip) connectWs(serverIp || ip);
      }, delay);
    };

    socket.onerror = (e) => {
      console.log("WebSocket Error", e);
    };

    socket.addEventListener('message', async (e: MessageEvent) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === "ui_command" && msg.action === "status_update" && msg.text) {
          if (msg.text.toLowerCase() === "idle") {
            setMikuState("idle");
            setStatusText("> IDLE");
          } else {
            setStatusText("> " + msg.text.toUpperCase());
            if (msg.text.toLowerCase().includes("hablando") || msg.text.toLowerCase().includes("escuchando")) {
              setMikuState("talking");
            } else {
              setMikuState("thinking");
            }
          }
        } else if (msg.type === "ui_command" && msg.action === "open_secrets_panel") {
            setSecretRequest({ active: true, service: msg.args[0], fields: msg.args[1] || [] });
        } else if (msg.type === "ui_command" && msg.action === "mobile_widget") {
            setWidgetData({ type: msg.args[0], args: msg.args.slice(1) });
        } else if (msg.type === "ui_command" && msg.action === "sync_clipboard" && msg.text) {
          try {
            if (msg.text !== lastClip.current) {
              lastClip.current = msg.text;
              await Clipboard.setStringAsync(msg.text);
            }
          } catch(e) {}
        } else if (msg.type === "ui_command" && msg.action === "download_file" && msg.filename) {
          try {
            const SAF = StorageAccessFramework;
            let directoryUri = await SecureStore.getItemAsync(MIKU_DOWNLOADS_DIR);
            
            if (!directoryUri) {
              Alert.alert('Configuración de Descargas', 'Por favor, selecciona la carpeta "Descargas" (Downloads). Miku creará automáticamente su propia carpeta adentro.');
              const permissions = await SAF.requestDirectoryPermissionsAsync();
              if (permissions.granted) {
                try {
                  // Miku crea su propia carpeta automáticamente
                  directoryUri = await SAF.makeDirectoryAsync(permissions.directoryUri, 'Miku');
                  await SecureStore.setItemAsync(MIKU_DOWNLOADS_DIR, directoryUri);
                } catch (e) {
                  // Si ya existe o hay error, usamos la raíz que escogió
                  directoryUri = permissions.directoryUri;
                  await SecureStore.setItemAsync(MIKU_DOWNLOADS_DIR, directoryUri);
                }
              } else {
                return;
              }
            } else {
              try {
                await SAF.readDirectoryAsync(directoryUri);
              } catch (e) {
                // Permiso perdido
                const permissions = await SAF.requestDirectoryPermissionsAsync();
                if (permissions.granted) {
                  try {
                    directoryUri = await SAF.makeDirectoryAsync(permissions.directoryUri, 'Miku');
                  } catch (err) {
                    directoryUri = permissions.directoryUri;
                  }
                  await SecureStore.setItemAsync(MIKU_DOWNLOADS_DIR, directoryUri);
                } else {
                  return;
                }
              }
            }

            const downloadDir = FileSystem.cacheDirectory + 'miku-link/';
            await FileSystem.makeDirectoryAsync(downloadDir, { intermediates: true }).catch(() => {});
            const localUri = downloadDir + msg.filename;
            
            const { uri } = await FileSystem.downloadAsync(
              `${getBaseUrl(ip)}/api/temp_media/${encodeURIComponent(msg.filename)}`,
              localUri
            );
            
            let mimeType = 'application/octet-stream';
            const fName = msg.filename.toLowerCase();
            if (fName.endsWith('.png')) mimeType = 'image/png';
            else if (fName.endsWith('.jpg') || fName.endsWith('.jpeg')) mimeType = 'image/jpeg';
            else if (fName.endsWith('.pdf')) mimeType = 'application/pdf';
            else if (fName.endsWith('.txt')) mimeType = 'text/plain';

            const newFileUri = await SAF.createFileAsync(directoryUri, msg.filename, mimeType);
            const base64Data = await FileSystem.readAsStringAsync(uri, { encoding: FileSystem.EncodingType.Base64 });
            await FileSystem.writeAsStringAsync(newFileUri, base64Data, { encoding: FileSystem.EncodingType.Base64 });
            
            await FileSystem.deleteAsync(uri, { idempotent: true }).catch(() => {});
            Alert.alert('Archivo guardado', `Se guardó exitosamente: ${msg.filename}`);
          } catch(e) {
            console.error('Error descargando archivo:', e);
            Alert.alert('Error', 'Hubo un error al guardar el archivo.');
          }
        } else if (msg.type === "ui_command" && msg.action === "ejecutar_intent_android") {
          try {
            const { intent_action, extras } = msg;
            if (intent_action) {
              await IntentLauncher.startActivityAsync(intent_action, { extra: extras || {} });
            }
          } catch(e) {
            console.error("Error ejecutando Intent de Android:", e);
          }
        } else if (msg.type === "ui_command" && msg.action === "play_audio" && msg.url) {
          try {
            const now = Date.now();
            if (lastPlayedAudioRef.current.url === msg.url && now - lastPlayedAudioRef.current.time < 2000) {
              console.log("Ignoring duplicate play_audio command");
              return;
            }
            lastPlayedAudioRef.current = { url: msg.url, time: now };
            
            if (currentSoundRef.current) {
              await currentSoundRef.current.stopAsync();
              await currentSoundRef.current.unloadAsync();
            }
            const { sound } = await Audio.Sound.createAsync({ uri: `${getBaseUrl(ip)}${msg.url}` });
            currentSoundRef.current = sound;
            await sound.playAsync();
          } catch (err) {
            console.error("Error playing audio: ", err);
          }
        } else if (msg.id && msg.text && msg.sender) {
          setMessages(prev => {
            const filtered = prev.filter(m => !m.text.includes('[🎤 Procesando audio...]'));
            if (filtered.find(m => m.id === msg.id)) return filtered;
            return [...filtered, msg];
          });
        }
      } catch (err) {}
    });
  };

  useEffect(() => {
    const subscription = AppState.addEventListener('change', (nextAppState: AppStateStatus) => {
      if (appState.current.match(/inactive|background/) && nextAppState === 'active') {
        console.log("App has come to the foreground, checking WebSocket...");
        if (!ws || ws.readyState !== WebSocket.OPEN) {
           if (serverIp) connectWs(serverIp);
        }
      }
      appState.current = nextAppState;
    });

    // Auto-sync clipboard
    const clipInterval = setInterval(async () => {
      if (!serverIp || appState.current !== 'active') return;
      try {
        if (await Clipboard.hasStringAsync()) {
          const text = await Clipboard.getStringAsync();
          if (text && text !== lastClip.current) {
            lastClip.current = text;
            fetch(`${getBaseUrl(serverIp)}/api/device/clipboard`, {
               method: "POST",
               headers: { "Content-Type": "application/json" },
               body: JSON.stringify({ text })
            }).catch(() => {}); // Ignorar fallos de red silenciosamente
          }
        }
      } catch(e) {}
    }, 2000);

    return () => {
      subscription.remove();
      clearInterval(clipInterval);
    };
  }, [serverIp, ws]);



  const sendMessage = async (text: string) => {
    if (!serverIp) return;
    try {
      const response = await fetch(`${getBaseUrl(serverIp)}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': API_KEY
        },
        body: JSON.stringify({ message: text, source: 'mobile' })
      });
      if (!response.ok) throw new Error('Error de conexión');
    } catch (e) {
      console.error(e);
    }
  };

  const sendAudio = async (uri: string) => {
    if (!serverIp) return;
    setStatusText("> PROCESANDO AUDIO...");
    setMessages(prev => [...prev, { id: Date.now().toString(), text: '[🎤 Procesando audio...]', sender: 'user' }]);
    
    try {
      const formData = new FormData();
      formData.append('file', {
        uri: uri,
        name: 'audio.m4a',
        type: 'audio/m4a',
      } as any);

      await fetch(`${getBaseUrl(serverIp)}/audio`, {
        method: 'POST',
        headers: {
          'x-api-key': API_KEY,
        },
        body: formData,
      });
    } catch (e) {
      console.error(e);
      setStatusText("> ERROR AL ENVIAR AUDIO");
    }
  };

  return (
    <WebSocketContext.Provider value={{
      ws,
      isConnected,
      messages,
      mikuState,
      statusText,
      widgetData,
      setWidgetData,
      secretRequest,
      setSecretRequest,
      setMessages,
      sendMessage,
      sendAudio,
      serverIp,
      setServerIp,
      setStatusText,
      connectWs,
      sessionsList,
      loadSession,
      startNewSession,
      updateSession,
      deleteSession
    }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
}
