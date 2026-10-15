import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl, TouchableOpacity } from 'react-native';
import { Ionicons, Feather } from '@expo/vector-icons';
import * as Clipboard from 'expo-clipboard';
import { useWebSocket } from '../context/WebSocketContext';
import { getBaseUrl } from '../utils/network';

type MCPServer = {
  name: string;
  command: string;
  connected: boolean;
  tools_count: number;
};

type SystemStatus = {
  hostname: string;
  platform: string;
  python_version: string;
  mcp_servers: MCPServer[];
  cloudflared_running: boolean | null;
  websocket_clients: number;
};

export default function DiagnosticsScreen() {
  const { serverIp, isConnected } = useWebSocket();
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [showAllMcp, setShowAllMcp] = useState(false);

  const deleteMcp = async (serverName: string) => {
    Alert.alert(
      "Eliminar MCP",
      `¿Estás seguro de que quieres eliminar el servidor '${serverName}'?`,
      [
        { text: "Cancelar", style: "cancel" },
        { 
          text: "Eliminar", 
          style: "destructive",
          onPress: async () => {
            if (!serverIp) return;
            try {
              addLog(`Eliminando MCP ${serverName}...`);
              const res = await fetch(`${getBaseUrl(serverIp)}/api/mcp/${serverName}`, { method: 'DELETE' });
              if (!res.ok) throw new Error('Error al eliminar');
              addLog(`MCP ${serverName} eliminado con éxito.`);
              fetchStatus();
            } catch (e: any) {
              addLog(`Error eliminando MCP: ${e.message}`);
              Alert.alert("Error", "No se pudo eliminar el servidor.");
            }
          }
        }
      ]
    );
  };

  const addLog = (msg: string) => {
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setLogs(prev => [`[${timestamp}] ${msg}`, ...prev].slice(0, 100));
  };

  const fetchStatus = useCallback(async () => {
    if (!serverIp) {
      setError('No hay servidor configurado');
      addLog('ERROR: No hay IP del servidor configurada.');
      return;
    }
    try {
      addLog('Consultando estado del sistema...');
      const res = await fetch(`${getBaseUrl(serverIp)}/api/desktop/status`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: SystemStatus = await res.json();
      setStatus(data);
      setError(null);
      
      const onlineCount = data.mcp_servers.filter(s => s.connected).length;
      addLog(`OK: ${onlineCount}/${data.mcp_servers.length} MCPs conectados. WS clients: ${data.websocket_clients}`);
    } catch (e: any) {
      setError(e.message);
      addLog(`ERROR al consultar estado: ${e.message}`);
    }
  }, [serverIp]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchStatus();
    setRefreshing(false);
  };

  const connectedServers = status?.mcp_servers.filter(s => s.connected).length ?? 0;
  const totalServers = status?.mcp_servers.length ?? 0;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#fff" />}
    >
      {/* Connection Banner */}
      <View style={[styles.banner, isConnected ? styles.bannerOk : styles.bannerError]}>
        <Ionicons name={isConnected ? "cloud-done-outline" : "cloud-offline-outline"} size={20} color="#fff" />
        <Text style={styles.bannerText}>
          {isConnected ? 'Conectado al servidor' : 'Sin conexion al servidor'}
        </Text>
      </View>

      {/* System Info Card */}
      {status && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>SISTEMA</Text>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Hostname</Text>
            <Text style={styles.infoValue}>{status.hostname}</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>OS</Text>
            <Text style={styles.infoValue}>{status.platform}</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Python</Text>
            <Text style={styles.infoValue}>{status.python_version}</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Tunel (Cloudflare)</Text>
            <View style={[styles.statusDot, status.cloudflared_running ? styles.dotGreen : styles.dotRed]} />
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Clientes WS</Text>
            <Text style={styles.infoValue}>{status.websocket_clients}</Text>
          </View>
        </View>
      )}

      {/* MCP Servers Card */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle}>SERVIDORES MCP</Text>
          <Text style={styles.cardBadge}>{connectedServers}/{totalServers}</Text>
        </View>
        {status?.mcp_servers.slice(0, showAllMcp ? undefined : 3).map((server, i) => (
          <View key={i} style={styles.mcpRow}>
            <View style={[styles.statusDot, server.connected ? styles.dotGreen : styles.dotRed]} />
            <View style={styles.mcpInfo}>
              <Text style={styles.mcpName}>{server.name}</Text>
              <Text style={styles.mcpDetail}>
                {server.connected ? `${server.tools_count} herramientas` : 'Desconectado'}
              </Text>
            </View>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
              <Ionicons 
                name={server.connected ? "checkmark-circle" : "close-circle"} 
                size={20} 
                color={server.connected ? "#4ade80" : "#f87171"} 
              />
              <TouchableOpacity onPress={() => deleteMcp(server.name)} style={{ padding: 5 }}>
                <Ionicons name="trash-outline" size={20} color="#f87171" />
              </TouchableOpacity>
            </View>
          </View>
        ))}
        {totalServers > 3 && (
          <TouchableOpacity 
            style={{ padding: 10, alignItems: 'center', marginTop: 5 }} 
            onPress={() => setShowAllMcp(!showAllMcp)}
          >
            <Text style={{ color: '#00d2ff', fontFamily: 'monospace' }}>
              {showAllMcp ? "Ocultar" : `Ver los ${totalServers} servidores...`}
            </Text>
          </TouchableOpacity>
        )}
        {totalServers === 0 && (
          <Text style={styles.emptyText}>No hay servidores MCP configurados.</Text>
        )}
      </View>

      {/* Console Log Card */}
      <View style={styles.card}>
        <View style={styles.consoleHeader}>
          <Text style={styles.cardTitle}>CONSOLA</Text>
          <View style={{ flexDirection: 'row', gap: 15 }}>
            <TouchableOpacity onPress={() => Clipboard.setStringAsync(logs.join('\n'))}>
              <Feather name="copy" size={20} color="#888" />
            </TouchableOpacity>
            <TouchableOpacity onPress={() => setLogs([])}>
              <Feather name="trash-2" size={20} color="#888" />
            </TouchableOpacity>
          </View>
        </View>
        <ScrollView style={styles.consoleScroll} nestedScrollEnabled={true}>
          {logs.length === 0 ? (
            <Text style={styles.logEmpty}>Sin logs recientes. Desliza hacia abajo para refrescar.</Text>
          ) : (
            logs.map((log, i) => (
              <Text key={i} style={[styles.logLine, log.includes('ERROR') && styles.logError]} selectable={true}>
                {log}
              </Text>
            ))
          )}
        </ScrollView>
      </View>

      {error && !status && (
        <View style={styles.errorCard}>
          <Ionicons name="warning-outline" size={24} color="#f87171" />
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#050505' },
  content: { padding: 16, paddingBottom: 40 },

  banner: { flexDirection: 'row', alignItems: 'center', padding: 14, borderRadius: 12, marginBottom: 16 },
  bannerOk: { backgroundColor: '#166534' },
  bannerError: { backgroundColor: '#991b1b' },
  bannerText: { color: '#fff', fontFamily: 'monospace', fontWeight: 'bold', marginLeft: 10, fontSize: 14 },

  card: { backgroundColor: '#111', borderRadius: 12, padding: 16, marginBottom: 16, borderWidth: 1, borderColor: '#222' },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  consoleHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  cardTitle: { color: '#888', fontFamily: 'monospace', fontSize: 12, fontWeight: 'bold' },
  cardBadge: { color: '#fff', fontFamily: 'monospace', fontSize: 12, backgroundColor: '#333', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6 },

  infoRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: '#1a1a1a' },
  infoLabel: { color: '#888', fontFamily: 'monospace', fontSize: 13 },
  infoValue: { color: '#fff', fontFamily: 'monospace', fontSize: 13 },

  statusDot: { width: 10, height: 10, borderRadius: 5, marginRight: 10 },
  dotGreen: { backgroundColor: '#4ade80' },
  dotRed: { backgroundColor: '#f87171' },

  mcpRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: '#1a1a1a' },
  mcpInfo: { flex: 1 },
  mcpName: { color: '#fff', fontFamily: 'monospace', fontWeight: 'bold', fontSize: 14 },
  mcpDetail: { color: '#666', fontFamily: 'monospace', fontSize: 12, marginTop: 2 },
  emptyText: { color: '#555', fontFamily: 'monospace', textAlign: 'center', paddingVertical: 20 },

  consoleScroll: {
    backgroundColor: '#0a0a0a',
    padding: 12,
    borderRadius: 8,
    minHeight: 150,
  },
  logLine: { color: '#888', fontFamily: 'monospace', fontSize: 11, marginBottom: 4 },
  logError: { color: '#f87171' },
  logEmpty: { color: '#444', fontFamily: 'monospace', fontSize: 11, textAlign: 'center' },

  errorCard: { backgroundColor: '#1a0a0a', borderRadius: 12, padding: 20, alignItems: 'center', borderWidth: 1, borderColor: '#991b1b' },
  errorText: { color: '#f87171', fontFamily: 'monospace', marginTop: 10, textAlign: 'center' },
});
