import React, { useEffect, useState, useRef } from 'react';
import { View, StyleSheet, Text, Animated, ActivityIndicator, BackHandler } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { getBaseUrl } from '../utils/network';
import * as SecureStore from 'expo-secure-store';

const SERVER_IP_KEY = 'miku_server_ip';
const DEVICE_KEY_NAME = 'miku_secret_identity';

export function ShareOverlay({ shareIntent, resetShareIntent }: any) {
  const [status, setStatus] = useState("Preparando y enviando a Miku...");
  const [success, setSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  
  const glowOpacity = useRef(new Animated.Value(0.4)).current;

  // Breathing animation
  useEffect(() => {
    const breathe = Animated.loop(
      Animated.sequence([
        Animated.timing(glowOpacity, { toValue: 1, duration: 1000, useNativeDriver: true }),
        Animated.timing(glowOpacity, { toValue: 0.3, duration: 1000, useNativeDriver: true }),
      ])
    );
    breathe.start();
    return () => breathe.stop();
  }, []);

  useEffect(() => {
    const processShare = async () => {
      try {
        const ip = await SecureStore.getItemAsync(SERVER_IP_KEY);
        const identityStr = await SecureStore.getItemAsync(DEVICE_KEY_NAME);
        
        if (!ip || !identityStr) {
          throw new Error("No hay dispositivo vinculado");
        }
        
        const identity = JSON.parse(identityStr);
        const deviceId = identity.deviceId;
        
        if (shareIntent.files && shareIntent.files.length > 0) {
          // It's a file or image
          const file = shareIntent.files[0]; 
          
          const formData = new FormData();
          formData.append("file", {
            uri: file.path,
            name: file.fileName || file.path.split('/').pop(),
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

          if (!res.ok) throw new Error("Error del servidor");

        } else if (shareIntent.text || shareIntent.webUrl) {
          // It's text or URL
          const text = shareIntent.text || shareIntent.webUrl;
          const res = await fetch(`${getBaseUrl(ip)}/api/device/clipboard`, {
            method: 'POST',
            headers: {
              'X-Device-Id': deviceId,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text })
          });
          
          if (!res.ok) throw new Error("Error del servidor");
        }

        setSuccess(true);
        setStatus("¡Enviado a Miku!");
        
        // Auto-close after 1.5s
        setTimeout(() => {
          resetShareIntent();
          BackHandler.exitApp();
        }, 1500);

      } catch (err: any) {
        setStatus("Error al enviar");
        setErrorMsg(err.message);
        setTimeout(() => {
          resetShareIntent();
          BackHandler.exitApp();
        }, 3000);
      }
    };

    if (shareIntent) {
      processShare();
    }
  }, [shareIntent]);

  return (
    <View style={styles.container}>
      <Animated.View style={[styles.glowBox, { opacity: glowOpacity }]}>
        <LinearGradient
          colors={errorMsg ? ['#ff4444', '#cc0000'] : success ? ['#00FF00', '#009900'] : ['#00d2ff', '#7b2ff7']}
          style={styles.gradient}
        />
      </Animated.View>
      <View style={styles.content}>
        {!success && !errorMsg && <ActivityIndicator size="large" color="#00d2ff" style={{ marginBottom: 20 }} />}
        <Text style={styles.title}>{status}</Text>
        {errorMsg ? <Text style={styles.error}>{errorMsg}</Text> : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.85)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  glowBox: {
    position: 'absolute',
    width: 200,
    height: 200,
    borderRadius: 100,
  },
  gradient: {
    flex: 1,
    borderRadius: 100,
  },
  content: {
    backgroundColor: '#111',
    padding: 30,
    borderRadius: 20,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#333',
    width: '80%',
  },
  title: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  error: {
    color: '#ff4444',
    marginTop: 10,
    textAlign: 'center',
  }
});
