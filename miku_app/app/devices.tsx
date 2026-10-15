import React, { useState, useEffect, useRef } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, Image, Alert, ActivityIndicator, Animated, AppState, Modal, ScrollView, RefreshControl } from 'react-native';
import { getBaseUrl } from '../utils/network';
import { Camera, CameraView } from 'expo-camera';
import * as SecureStore from 'expo-secure-store';
import * as Crypto from 'expo-crypto';
import * as DocumentPicker from 'expo-document-picker';
import * as Clipboard from 'expo-clipboard';
import * as FileSystem from 'expo-file-system/legacy';
import { StorageAccessFramework } from 'expo-file-system/legacy';
import * as Sharing from 'expo-sharing';
import * as IntentLauncher from 'expo-intent-launcher';
import { Feather } from '@expo/vector-icons';
import { useWebSocket } from '../context/WebSocketContext';

const DEVICE_KEY_NAME = 'miku_secret_identity';
const SERVER_IP_KEY = 'miku_server_ip';

export default function DevicesScreen() {
  const { ws, isConnected: wsConnected, mikuState, serverIp, setServerIp, connectWs } = useWebSocket() as any;

  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [isPaired, setIsPaired] = useState(false);
  const [localServerIp, setLocalServerIp] = useState<string | null>(null);
  const [pcName, setPcName] = useState<string | null>(null);
  const [wallpaperTimestamp, setWallpaperTimestamp] = useState<number>(Date.now());
  const [isScanning, setIsScanning] = useState(false);
  const [loading, setLoading] = useState(true);
  const [mikuStatus, setMikuStatus] = useState("En línea, conexión segura");
  const [toast, setToast] = useState<{title: string, message: string, type: 'success'|'error'} | null>(null);
  const [recentItems, setRecentItems] = useState<{id: string, icon: any, title: string, sub: string}[]>([]);
  const [fadeAnim] = useState(new Animated.Value(0));
  
  // Refresh & Archivos locales
  const [refreshing, setRefreshing] = useState(false);
  const [showFilesModal, setShowFilesModal] = useState(false);
  const [localFiles, setLocalFiles] = useState<{uri: string, name: string}[]>([]);
  
  const MIKU_DOWNLOADS_DIR = 'miku_downloads_dir';

  const onRefresh = React.useCallback(async () => {
    setRefreshing(true);
    setWallpaperTimestamp(Date.now());
    try {
      await loadLocalFiles();
    } catch (e) {}
    
    setTimeout(() => {
      setRefreshing(false);
    }, 1000);
  }, []);

  useEffect(() => {
    const loadRecents = async () => {
      try {
        const stored = await SecureStore.getItemAsync('MIKU_RECENT_ITEMS');
        if (stored) {
          setRecentItems(JSON.parse(stored));
        }
      } catch (e) {}
    };
    loadRecents();
  }, []);

  const addRecent = (icon: any, title: string, sub: string) => {
    setRecentItems(prev => {
      const newItems = [{id: Math.random().toString(), icon, title, sub}, ...prev].slice(0, 3);
      SecureStore.setItemAsync('MIKU_RECENT_ITEMS', JSON.stringify(newItems)).catch(()=>{});
      return newItems;
    });
  };

  const showToast = (title: string, message: string, type: 'success'|'error' = 'success') => {
    setToast({ title, message, type });
    Animated.timing(fadeAnim, { toValue: 1, duration: 300, useNativeDriver: true }).start();
    setTimeout(() => {
      Animated.timing(fadeAnim, { toValue: 0, duration: 300, useNativeDriver: true }).start(() => setToast(null));
    }, 4000);
  };
  
  useEffect(() => {
    (async () => {
      try {
        // Ejecutar obtención de credenciales rápidamente
        const savedIp = await SecureStore.getItemAsync(SERVER_IP_KEY);
        const savedPcName = await SecureStore.getItemAsync('miku_pc_name');
        if (savedPcName) setPcName(savedPcName);
        const savedIdentity = await SecureStore.getItemAsync(DEVICE_KEY_NAME);
        
        if (savedIp && savedIdentity) {
          setLocalServerIp(savedIp);
          setIsPaired(true);
        }
      } catch (e) {
        console.error("Error loading device info:", e);
      } finally {
        setLoading(false);
      }

      // Pedir permisos de cámara en segundo plano sin bloquear el render principal
      try {
        const { status } = await Camera.requestCameraPermissionsAsync();
        setHasPermission(status === 'granted');
      } catch (e) {
        console.log("Cámara ignorada/error:", e);
      }
    })();
  }, []);

  // Escuchar si la app pasa a primer plano para sincronizar el portapapeles
  useEffect(() => {
    const subscription = AppState.addEventListener('change', nextAppState => {
      if (nextAppState === 'active' && isPaired && (serverIp || localServerIp)) {
        loadLocalFiles(true);
        if (wsConnected) {
          handleSyncClipboard(true);
        }
      }
    });
    return () => {
      subscription.remove();
    };
  }, [isPaired, serverIp, localServerIp, wsConnected]);

  useEffect(() => {
    if (!ws || !isPaired) return;
    
    if (wsConnected) {
      setMikuStatus("En línea, conexión segura");
    } else {
      setMikuStatus("Time Out / Sin conexión");
    }
    
    const handleMessage = async (e: any) => {
      try {
        const data = JSON.parse(e.data);
        if (data.action === "sync_clipboard") {
          await Clipboard.setStringAsync(data.text);
          showToast("Copiado desde Miku Desktop", "Texto en el portapapeles", "success");
          addRecent("copy", "Texto Copiado", "Recibido de la PC");
        }
      } catch (err) {
        console.error("Error WS parse:", err);
      }
    };
    
    ws.addEventListener('message', handleMessage);
    
    return () => {
      ws.removeEventListener('message', handleMessage);
    };
  }, [ws, wsConnected, isPaired, serverIp, localServerIp]);

  // AUTO-SYNC CLIPBOARD (AppState)
  const appState = useRef(AppState.currentState);
  useEffect(() => {
    const subscription = AppState.addEventListener('change', nextAppState => {
      if (appState.current.match(/inactive|background/) && nextAppState === 'active') {
        if (isPaired && (serverIp || localServerIp)) {
          handleSyncClipboard(true); // silent sync
        }
      }
      appState.current = nextAppState;
    });

    return () => {
      subscription.remove();
    };
  }, [isPaired, serverIp, localServerIp]);

  const handleBarCodeScanned = async ({ type, data }: { type: string; data: string }) => {
    setIsScanning(false);
    
    // Validar miku://pair?s={session}&ip={ip}
    if (!data.startsWith('miku://pair?')) {
      showToast('QR Inválido', 'Este no es un código QR de Miku.', 'error');
      return;
    }
    
    try {
      const urlParams = new URLSearchParams(data.split('?')[1]);
      const session = urlParams.get('s');
      const ip = urlParams.get('ip');
      
      if (!session || !ip) throw new Error("Faltan parámetros en el QR");
      
      const baseUrl = getBaseUrl(ip);
      showToast("Conectando...", `Intentando ${baseUrl}`, "success");
      
      // Pre-check: test basic connectivity first
      try {
        const testController = new AbortController();
        const testTimeout = setTimeout(() => testController.abort(), 8000);
        const testRes = await fetch(`${baseUrl}/api/desktop/info`, { 
          signal: testController.signal 
        });
        clearTimeout(testTimeout);
        if (!testRes.ok) throw new Error(`Server responded ${testRes.status}`);
      } catch (testErr: any) {
        if (testErr.name === 'AbortError') {
          throw new Error(`Timeout: No se pudo alcanzar ${baseUrl} en 8s. ¿Están en la misma red WiFi?`);
        }
        throw new Error(`No se puede alcanzar el servidor (${baseUrl}): ${testErr.message}`);
      }
      
      // Generar Identidad
      const deviceId = Crypto.randomUUID();
      const publicKey = await Crypto.digestStringAsync(Crypto.CryptoDigestAlgorithm.SHA256, deviceId + Date.now().toString());
      
      // Enviar Handshake al servidor
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 10000);
      
      const res = await fetch(`${baseUrl}/api/pair/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: session,
          device_id: deviceId,
          name: "Miku Mobile",
          public_key: publicKey
        }),
        signal: controller.signal
      });
      clearTimeout(timeout);
      
      if (!res.ok) {
        const d = await res.json();
        throw new Error(d.detail || "Error de red");
      }
      
      // Guardar identidad en el enclave seguro del teléfono
      await SecureStore.setItemAsync(DEVICE_KEY_NAME, JSON.stringify({ deviceId, publicKey }));
      await SecureStore.setItemAsync(SERVER_IP_KEY, ip);
      
      setLocalServerIp(ip);
      if (setServerIp) setServerIp(ip);
      if (connectWs) connectWs(ip);
      
      // Fetch PC Name
      fetch(`${baseUrl}/api/desktop/info`)
        .then(res => res.json())
        .then(data => {
          if (data.hostname) {
            setPcName(data.hostname);
            SecureStore.setItemAsync('miku_pc_name', data.hostname);
          }
        })
        .catch(e => console.log('Error fetching pc name:', e));
        
      setIsPaired(true);
      showToast("¡Éxito!", "Dispositivo vinculado correctamente con la PC.", "success");
      
    } catch (e: any) {
      const errMsg = e.name === 'AbortError' 
        ? 'Timeout: El servidor no respondió a tiempo. ¿Están en la misma WiFi?'
        : (e.message || "No se pudo conectar a la PC.");
      showToast("Error de Vinculación", errMsg, "error");
      console.error("Pairing error details:", e);
    }
  };

  const handleUnpair = async () => {
    Alert.alert(
      "Desvincular Dispositivo",
      "¿Estás seguro que deseas romper la conexión segura con la PC? Deberás volver a escanear el QR.",
      [
        { text: "Cancelar", style: "cancel" },
        { text: "Desvincular", style: "destructive", onPress: async () => {
            await SecureStore.deleteItemAsync(DEVICE_KEY_NAME);
            await SecureStore.deleteItemAsync(SERVER_IP_KEY);
            await SecureStore.deleteItemAsync('miku_pc_name');
            setIsPaired(false);
            setLocalServerIp(null);
            setPcName(null);
            if (setServerIp) setServerIp(null);
        }}
      ]
    );
  };

  const handleLockPC = async () => {
    try {
      const identity = await SecureStore.getItemAsync(DEVICE_KEY_NAME);
      const ip = serverIp || localServerIp;
      if (!identity || !ip) return;
      const { deviceId } = JSON.parse(identity);
      
      const res = await fetch(`${getBaseUrl(ip)}/api/device/lock`, {
        method: 'POST',
        headers: { 'X-Device-Id': deviceId }
      });
      if (!res.ok) throw new Error("PC rechazó el comando o está offline.");
      showToast("Bloqueo", "La PC ha sido bloqueada.", "success");
    } catch (e: any) {
      showToast("Error", e.message, "error");
    }
  };

  const handleSendFile = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({ copyToCacheDirectory: true });
      if (result.canceled || !result.assets || result.assets.length === 0) return;
      
      const file = result.assets[0];
      const identity = await SecureStore.getItemAsync(DEVICE_KEY_NAME);
      const ip = serverIp || localServerIp;
      if (!identity || !ip) return;
      const { deviceId } = JSON.parse(identity);

      const formData = new FormData();
      formData.append("file", {
        uri: file.uri,
        name: file.name,
        type: file.mimeType || 'application/octet-stream'
      } as any);

      const res = await fetch(`${getBaseUrl(ip)}/api/device/upload`, {
        method: 'POST',
        headers: {
          'X-Device-Id': deviceId,
          'Content-Type': 'multipart/form-data',
        },
        body: formData
      });

      if (!res.ok) throw new Error("Error enviando el archivo");
      showToast("Enviado", "El archivo se ha enviado y abierto en Miku.", "success");
      addRecent("upload", file.name, "Enviado a la PC");
    } catch (e: any) {
      showToast("Error de Envío", e.message, "error");
    }
  };

  const handleSyncClipboard = async (silent = false) => {
    try {
      const identity = await SecureStore.getItemAsync(DEVICE_KEY_NAME);
      const ip = serverIp || localServerIp;
      if (!identity || !ip) return;
      const { deviceId } = JSON.parse(identity);

      // 1. Intentar leer imagen del portapapeles primero (Requiere expo-clipboard avanzado)
      if (Clipboard.hasImageAsync) {
        const hasImage = await Clipboard.hasImageAsync();
        if (hasImage) {
          const imageResult = await Clipboard.getImageAsync({ format: 'png' });
          if (imageResult && imageResult.data) {
            const res = await fetch(`${getBaseUrl(ip)}/api/device/clipboard_image`, {
              method: 'POST',
              headers: {
                'X-Device-Id': deviceId,
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({ image: imageResult.data })
            });
            if (res.ok) {
              if (!silent) showToast("Imagen enviada", "Captura copiada a Windows", "success");
              return;
            }
          }
        }
      }

      // 2. Si no hay imagen, leer texto
      const text = await Clipboard.getStringAsync();
      if (!text) {
        if (!silent) showToast("Vacío", "El portapapeles está vacío.", "error");
        return;
      }
      
      const res = await fetch(`${getBaseUrl(ip)}/api/device/clipboard`, {
        method: 'POST',
        headers: {
          'X-Device-Id': deviceId,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text })
      });

      if (!res.ok) throw new Error("Error sincronizando");
      if (!silent) {
        showToast("Sincronizado", "Texto enviado a Windows", "success");
        addRecent("copy", "Texto Sincronizado", "Enviado a la PC");
      }
    } catch (e: any) {
      if (!silent) showToast("Error", e.message, "error");
    }
  };

  const loadLocalFiles = async (silent = true) => {
    try {
      const directoryUri = await SecureStore.getItemAsync(MIKU_DOWNLOADS_DIR);
      if (!directoryUri) {
        if (!silent) showToast("Aviso", "No has configurado la carpeta de descargas aún", "error");
        return;
      }
      const files = await StorageAccessFramework.readDirectoryAsync(directoryUri);
      
      const fileObjects = files.map(uri => {
        const decoded = decodeURIComponent(uri);
        const name = decoded.split('/').pop() || 'Archivo desconocido';
        return { uri, name };
      }).filter(f => !f.name.startsWith('.')); // Ignorar ocultos

      setLocalFiles(fileObjects);
      if (!silent) {
        setShowFilesModal(true);
      }
    } catch (e: any) {
      if (!silent) showToast("Error", "No se pudieron leer los archivos", "error");
    }
  };

  const openFilesModal = () => {
    loadLocalFiles(false);
  };

  const isImage = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    return ext === 'jpg' || ext === 'jpeg' || ext === 'png' || ext === 'gif' || ext === 'bmp' || ext === 'webp';
  };

  const openLocalFile = async (uri: string, filename: string) => {
    try {
      let mimeType = 'application/octet-stream';
      const ext = filename.split('.').pop()?.toLowerCase();
      if (ext === 'jpg' || ext === 'jpeg') mimeType = 'image/jpeg';
      else if (ext === 'png') mimeType = 'image/png';
      else if (ext === 'pdf') mimeType = 'application/pdf';
      else if (ext === 'txt') mimeType = 'text/plain';
      else if (ext === 'mp4') mimeType = 'video/mp4';

      await IntentLauncher.startActivityAsync('android.intent.action.VIEW', {
        data: uri,
        type: mimeType,
        flags: 1, // FLAG_GRANT_READ_URI_PERMISSION
      });
    } catch (e: any) {
      showToast("Error", "No se pudo abrir el archivo", "error");
    }
  };

  if (loading) {
    return <View style={styles.container}><ActivityIndicator color="#fff" size="large" /></View>;
  }

  // PANTALLA: No Emparejado (Scanner UI)
  if (isScanning) {
    return (
      <View style={styles.container}>
        <CameraView style={StyleSheet.absoluteFillObject} onBarcodeScanned={handleBarCodeScanned} />
        <TouchableOpacity style={styles.scanBtn} onPress={() => setIsScanning(false)}>
          <Text style={styles.scanBtnText}>Cancelar</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={{ flex: 1, backgroundColor: '#000' }}>
      <ScrollView 
        contentContainerStyle={styles.container}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#fff" />
        }
      >
        <View style={styles.header}>
          {!isPaired ? (
            <>
              <Text style={styles.title}>Vincular Dispositivo</Text>
              <Text style={styles.subtitle}>Escanea el código QR de Miku Desktop</Text>
              <TouchableOpacity style={styles.scanBtn} onPress={() => setIsScanning(true)}>
                <Feather name="monitor" size={48} color="#fff" />
                <Text style={styles.scanBtnText}>Tocar para Escanear QR</Text>
              </TouchableOpacity>
            </>
          ) : (
            <>
              <Image 
                source={{ uri: `${getBaseUrl(serverIp || localServerIp)}/api/desktop/wallpaper?t=${wallpaperTimestamp}` }} 
                style={styles.pcImage} 
              />
              <Text style={styles.pcName}>{pcName || `Miku Desktop (${serverIp || localServerIp})`}</Text>
              <View style={styles.statusRow}>
                <View style={[styles.statusDot, { backgroundColor: wsConnected ? '#00FF00' : '#ff4444' }]} />
                <Text style={styles.statusText}>{wsConnected ? mikuStatus : 'Time Out / Sin conexión'}</Text>
              </View>
            </>
          )}
        </View>

        {isPaired && (
          <>
            <View style={styles.actionsGrid}>
              <TouchableOpacity style={styles.actionBtn} onPress={handleLockPC}>
                <Feather name="lock" size={24} color="#fff" />
                <Text style={styles.actionText}>Lock PC</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.actionBtn} onPress={handleSendFile}>
                <Feather name="send" size={24} color="#fff" />
                <Text style={styles.actionText}>Send files</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.actionBtn}>
                <Feather name="monitor" size={24} color="#fff" />
                <Text style={styles.actionText}>Mirror</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.recentSection}>
              <View style={styles.recentHeader}>
                <Text style={styles.sectionTitle}>Recent</Text>
              </View>
              {recentItems.length === 0 ? (
                <Text style={{color: '#888', textAlign: 'center', marginVertical: 10}}>No hay actividad</Text>
              ) : (
                recentItems.map((item) => (
                  <View key={item.id} style={styles.recentItem}>
                    <Feather name={item.icon} size={20} color="#888" />
                    <View style={styles.recentTextContainer}>
                      <Text style={styles.recentTitle}>{item.title}</Text>
                      <Text style={styles.recentSub}>{item.sub}</Text>
                    </View>
                  </View>
                ))
              )}
            </View>

            <View style={styles.bottomList}>
              <TouchableOpacity style={styles.listItem} onPress={openFilesModal}>
                <Feather name="folder" size={20} color="#fff" />
                <Text style={styles.listText}>Archivos recibidos</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.listItem} onPress={() => handleSyncClipboard(false)}>
                <Feather name="copy" size={20} color="#fff" />
                <Text style={styles.listText}>Sync Clipboard</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.listItem, {marginTop: 20, borderColor: '#f00'}]} onPress={handleUnpair}>
                <Feather name="log-out" size={20} color="#ff4444" />
                <Text style={[styles.listText, {color: '#ff4444'}]}>Desvincular</Text>
              </TouchableOpacity>
            </View>
          </>
        )}
      </ScrollView>
      
      <Modal visible={showFilesModal} animationType="slide" transparent={true}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Archivos</Text>
              <TouchableOpacity onPress={() => setShowFilesModal(false)}>
                <Feather name="x" size={24} color="#fff" />
              </TouchableOpacity>
            </View>
            <ScrollView>
              {localFiles.map((f, i) => (
                <TouchableOpacity key={i} style={styles.fileItem} onPress={() => openLocalFile(f.uri, f.name)}>
                  {isImage(f.name) ? (
                    <Image source={{ uri: f.uri }} style={styles.fileThumbnail} />
                  ) : (
                    <Feather name="file" size={20} color="#4facfe" />
                  )}
                  <Text style={styles.fileItemText} numberOfLines={1} ellipsizeMode="middle">{f.name}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        </View>
      </Modal>
      
      {toast && (
        <Animated.View style={[styles.toastContainer, { opacity: fadeAnim, borderLeftColor: toast.type === 'error' ? '#ff4444' : '#00FF00' }]}>
          <Text style={styles.toastTitle}>{toast.title}</Text>
          <Text style={styles.toastMessage}>{toast.message}</Text>
        </Animated.View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    paddingTop: 50,
    paddingHorizontal: 20,
    paddingBottom: 40,
  },
  header: {
    marginTop: 40,
    marginBottom: 40,
    alignItems: 'center'
  },
  title: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
  },
  subtitle: {
    color: '#888',
    marginTop: 8,
  },
  scannerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  camera: {
    width: 300,
    height: 300,
    borderRadius: 20,
    overflow: 'hidden',
  },
  scanBtn: {
    width: 250,
    height: 250,
    borderRadius: 20,
    backgroundColor: '#111',
    borderWidth: 1,
    borderColor: '#333',
    justifyContent: 'center',
    alignItems: 'center',
  },
  scanBtnText: {
    color: '#fff',
    marginTop: 20,
    fontSize: 16,
    fontWeight: '500',
  },
  // Paired UI Styles
  linkedHeader: {
    alignItems: 'center',
    marginTop: 20,
    marginBottom: 30,
  },
  pcImage: {
    width: 140,
    height: 100,
    borderRadius: 16,
    marginBottom: 16,
    borderWidth: 2,
    borderColor: '#333',
  },
  pcName: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
    marginTop: 12,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#00FF00',
    marginRight: 6,
  },
  statusText: {
    color: '#888',
    fontSize: 12,
  },
  actionsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 30,
  },
  actionBtn: {
    flex: 1,
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 4,
    alignItems: 'center',
  },
  actionText: {
    color: '#fff',
    marginTop: 8,
    fontSize: 12,
    fontWeight: '500',
  },
  recentSection: {
    backgroundColor: '#111',
    borderRadius: 16,
    padding: 16,
    marginBottom: 20,
  },
  recentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  seeMore: {
    color: '#4facfe',
    fontSize: 14,
  },
  recentItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  recentTextContainer: {
    marginLeft: 16,
  },
  recentTitle: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
  },
  recentSub: {
    color: '#888',
    fontSize: 12,
    marginTop: 2,
  },
  bottomList: {
    flex: 1,
  },
  listItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#111',
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
  },
  listText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '500',
    marginLeft: 16,
  },
  toastContainer: {
    position: 'absolute',
    bottom: 40,
    left: 20,
    right: 20,
    backgroundColor: '#1a1a1a',
    padding: 16,
    borderRadius: 12,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 5,
    elevation: 6,
  },
  toastTitle: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  toastMessage: {
    color: '#aaa',
    fontSize: 13,
    marginTop: 4,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#111',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    height: '60%',
    padding: 20,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  modalScroll: {
    flex: 1,
  },
  fileItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
    padding: 16,
    borderRadius: 12,
    marginBottom: 10,
  },
  fileItemText: {
    color: '#fff',
    marginLeft: 12,
    fontSize: 14,
    flex: 1,
  },
  fileThumbnail: {
    width: 32,
    height: 32,
    borderRadius: 6,
    backgroundColor: '#000',
  }
});
