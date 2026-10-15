import React, { useState, useEffect, useCallback } from 'react';
import {
  StyleSheet, Text, View, TouchableOpacity, TextInput,
  ScrollView, ActivityIndicator, Alert, RefreshControl,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import * as SecureStore from 'expo-secure-store';
import { getBaseUrl } from '../utils/network';

const SERVER_IP_KEY = 'miku_server_ip';
const API_KEY = 'miku_secure_key_2026';

type KeyInfo = {
  value_masked: string;
  is_set: boolean;
};

// Mapeo de nombres internos a labels amigables
const KEY_LABELS: Record<string, { label: string; placeholder: string; description: string }> = {
  GROQ_API_KEY: {
    label: 'Groq API Key',
    placeholder: 'gsk_...',
    description: 'Para modelos Llama y Gemma ultra-rápidos',
  },
  NVIDIA_API_KEY: {
    label: 'NVIDIA API Key',
    placeholder: 'nvapi-...',
    description: 'Para modelos NVIDIA NIM',
  },
  GOOGLE_CLOUD_PROJECT: {
    label: 'Google Cloud Project ID',
    placeholder: 'mi-proyecto-123',
    description: 'ID de tu proyecto en Google Cloud (Vertex AI)',
  },
  GOOGLE_CLOUD_LOCATION: {
    label: 'Google Cloud Location',
    placeholder: 'us-central1',
    description: 'Región de Vertex AI',
  },
  ELEVENLABS_API_KEY: {
    label: 'ElevenLabs API Key',
    placeholder: 'sk_...',
    description: 'Para voces premium de ElevenLabs (opcional)',
  },
  SPOTIFY_CLIENT_ID: {
    label: 'Spotify Client ID',
    placeholder: 'abc123...',
    description: 'Desde developer.spotify.com',
  },
  SPOTIFY_CLIENT_SECRET: {
    label: 'Spotify Client Secret',
    placeholder: 'xyz789...',
    description: 'Desde developer.spotify.com',
  },
};

export default function SettingsScreen() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [keys, setKeys] = useState<Record<string, KeyInfo>>({});
  const [editValues, setEditValues] = useState<Record<string, string>>({});
  const [expandedKey, setExpandedKey] = useState<string | null>(null);
  const [serverIp, setServerIp] = useState<string | null>(null);

  const fetchKeys = useCallback(async () => {
    try {
      const ip = await SecureStore.getItemAsync(SERVER_IP_KEY);
      if (!ip) return;
      setServerIp(ip);

      const res = await fetch(`${getBaseUrl(ip)}/api/config/keys`, {
        headers: { 'x-api-key': API_KEY },
      });
      const data = await res.json();
      if (data.keys) {
        setKeys(data.keys);
        // Inicializar edit values con los valores enmascarados
        const initial: Record<string, string> = {};
        for (const k of Object.keys(data.keys)) {
          initial[k] = ''; // Campo vacío = no cambiar
        }
        setEditValues(initial);
      }
    } catch (e) {
      console.error('Error fetching keys:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchKeys();
  }, [fetchKeys]);

  const handleSave = async () => {
    if (!serverIp) return;

    // Filtrar solo las keys que el usuario realmente cambió (no vacías)
    const changedKeys: Record<string, string> = {};
    for (const [k, v] of Object.entries(editValues)) {
      if (v.trim() && !v.startsWith('*')) {
        changedKeys[k] = v.trim();
      }
    }

    if (Object.keys(changedKeys).length === 0) {
      Alert.alert('Sin cambios', 'No has modificado ninguna clave.');
      return;
    }

    setSaving(true);
    try {
      const res = await fetch(`${getBaseUrl(serverIp)}/api/config/keys`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': API_KEY,
        },
        body: JSON.stringify({ keys: changedKeys }),
      });
      const data = await res.json();
      if (data.status === 'ok') {
        Alert.alert('✓ Guardado', data.message);
        // Refrescar las keys
        setLoading(true);
        await fetchKeys();
        setExpandedKey(null);
      } else {
        Alert.alert('Error', data.detail || 'Error desconocido');
      }
    } catch (e) {
      Alert.alert('Error', 'No se pudo conectar con el servidor.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color="#00ffcc" size="large" />
        <Text style={styles.loadingText}>Cargando configuración...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={fetchKeys} tintColor="#00ffcc" />}
    >
      <Text style={styles.sectionTitle}>Configuración de IA</Text>
      <Text style={styles.sectionSub}>
        Gestiona las API Keys que Miku usa para funcionar. Los cambios se aplican al instante en el servidor.
      </Text>

      {Object.entries(keys).map(([keyName, info]) => {
        const meta = KEY_LABELS[keyName] || { label: keyName, placeholder: '', description: '' };
        const isExpanded = expandedKey === keyName;

        return (
          <TouchableOpacity
            key={keyName}
            activeOpacity={0.8}
            onPress={() => setExpandedKey(isExpanded ? null : keyName)}
            style={[styles.keyCard, isExpanded && styles.keyCardExpanded]}
          >
            <View style={styles.keyHeader}>
              <View style={styles.keyHeaderLeft}>
                <View style={[styles.statusDot, { backgroundColor: info.is_set ? '#00ff88' : '#ff4444' }]} />
                <Text style={styles.keyLabel}>{meta.label}</Text>
              </View>
              <Feather name={isExpanded ? 'chevron-up' : 'chevron-down'} size={18} color="#888" />
            </View>

            {!isExpanded && info.is_set && (
              <Text style={styles.maskedValue}>{info.value_masked}</Text>
            )}

            {isExpanded && (
              <View style={styles.expandedContent}>
                <Text style={styles.keyDescription}>{meta.description}</Text>
                <Text style={styles.currentLabel}>
                  {info.is_set ? `Actual: ${info.value_masked}` : 'No configurada'}
                </Text>
                <TextInput
                  style={styles.input}
                  placeholder={meta.placeholder}
                  placeholderTextColor="#555"
                  value={editValues[keyName] || ''}
                  onChangeText={(text) => setEditValues((prev) => ({ ...prev, [keyName]: text }))}
                  autoCapitalize="none"
                  autoCorrect={false}
                  secureTextEntry={keyName.includes('KEY') || keyName.includes('SECRET')}
                />
              </View>
            )}
          </TouchableOpacity>
        );
      })}

      <TouchableOpacity style={styles.saveBtn} onPress={handleSave} disabled={saving}>
        {saving ? (
          <ActivityIndicator color="#000" />
        ) : (
          <Text style={styles.saveBtnText}>Guardar Cambios</Text>
        )}
      </TouchableOpacity>

      <View style={styles.footer}>
        <Feather name="info" size={14} color="#555" />
        <Text style={styles.footerText}>
          Los campos vacíos no se modifican. Solo se actualizan las claves que introduzcas.
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#050505',
  },
  content: {
    padding: 20,
    paddingBottom: 40,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#050505',
  },
  loadingText: {
    color: '#888',
    marginTop: 12,
    fontFamily: 'monospace',
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 22,
    fontWeight: '700',
    fontFamily: 'monospace',
    marginBottom: 6,
  },
  sectionSub: {
    color: '#777',
    fontSize: 13,
    fontFamily: 'monospace',
    marginBottom: 20,
    lineHeight: 18,
  },
  keyCard: {
    backgroundColor: '#111',
    borderRadius: 12,
    padding: 16,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#222',
  },
  keyCardExpanded: {
    borderColor: '#00ffcc33',
  },
  keyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  keyHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  keyLabel: {
    color: '#eee',
    fontSize: 14,
    fontWeight: '600',
    fontFamily: 'monospace',
  },
  maskedValue: {
    color: '#555',
    fontSize: 12,
    fontFamily: 'monospace',
    marginTop: 6,
    marginLeft: 18,
  },
  expandedContent: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#222',
  },
  keyDescription: {
    color: '#888',
    fontSize: 12,
    fontFamily: 'monospace',
    marginBottom: 8,
  },
  currentLabel: {
    color: '#00ffcc',
    fontSize: 11,
    fontFamily: 'monospace',
    marginBottom: 10,
  },
  input: {
    backgroundColor: '#1a1a1a',
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: '#fff',
    fontFamily: 'monospace',
    fontSize: 13,
    borderWidth: 1,
    borderColor: '#333',
  },
  saveBtn: {
    backgroundColor: '#00ffcc',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 20,
  },
  saveBtnText: {
    color: '#000',
    fontSize: 15,
    fontWeight: '700',
    fontFamily: 'monospace',
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 16,
    paddingHorizontal: 4,
  },
  footerText: {
    color: '#555',
    fontSize: 11,
    fontFamily: 'monospace',
    flex: 1,
  },
});
