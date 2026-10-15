import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Modal, TextInput, Vibration } from 'react-native';
import { DrawerContentScrollView } from '@react-navigation/drawer';
import { useWebSocket } from '../context/WebSocketContext';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

export function ChatHistoryDrawer(props: any) {
  const { sessionsList, loadSession, startNewSession, updateSession, deleteSession } = useWebSocket();
  const router = useRouter();

  const [showArchived, setShowArchived] = useState(false);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [isOptionsModalVisible, setOptionsModalVisible] = useState(false);
  
  // For Editing Title
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [newTitle, setNewTitle] = useState("");

  const handleSelectSession = (id: string) => {
    loadSession(id);
    props.navigation.closeDrawer();
    router.push('/');
  };

  const handleNewChat = () => {
    startNewSession();
    props.navigation.closeDrawer();
    router.push('/');
  };

  const handleLongPress = (id: string, currentTitle: string) => {
    Vibration.vibrate(50); // Haptic feedback
    setSelectedSessionId(id);
    setNewTitle(currentTitle);
    setOptionsModalVisible(true);
  };

  const handleAction = async (action: 'pin' | 'archive' | 'delete' | 'edit') => {
    if (!selectedSessionId) return;

    const session = sessionsList.find(s => s.id === selectedSessionId);
    if (!session) return;

    if (action === 'delete') {
      await deleteSession(selectedSessionId);
      setOptionsModalVisible(false);
    } else if (action === 'pin') {
      await updateSession(selectedSessionId, { pinned: !session.pinned });
      setOptionsModalVisible(false);
    } else if (action === 'archive') {
      await updateSession(selectedSessionId, { archived: !session.archived });
      setOptionsModalVisible(false);
    } else if (action === 'edit') {
      setIsEditingTitle(true);
      // We don't close the modal yet, we show the input
    }
  };

  const saveNewTitle = async () => {
    if (selectedSessionId) {
      await updateSession(selectedSessionId, { title: newTitle });
    }
    setIsEditingTitle(false);
    setOptionsModalVisible(false);
  };

  // Filter and sort sessions
  const displaySessions = sessionsList
    .filter(s => showArchived ? s.archived : !s.archived)
    .sort((a, b) => {
      if (a.pinned && !b.pinned) return -1;
      if (!a.pinned && b.pinned) return 1;
      return new Date(b.date).getTime() - new Date(a.date).getTime();
    });

  const selectedSession = sessionsList.find(s => s.id === selectedSessionId);

  return (
    <DrawerContentScrollView {...props} style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>CHAT HISTORY</Text>
      </View>
      
      <TouchableOpacity style={styles.newChatBtn} onPress={handleNewChat}>
        <Ionicons name="add" size={20} color="#000" />
        <Text style={styles.newChatText}>NEW CHAT</Text>
      </TouchableOpacity>

      <View style={styles.tabsContainer}>
        <TouchableOpacity 
          style={[styles.tab, !showArchived && styles.activeTab]} 
          onPress={() => setShowArchived(false)}
        >
          <Ionicons name="chatbubbles-outline" size={18} color={!showArchived ? "#fff" : "#666"} />
          <Text style={[styles.tabText, !showArchived && styles.activeTabText]}>Activos</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.tab, showArchived && styles.activeTab]} 
          onPress={() => setShowArchived(true)}
        >
          <Ionicons name="archive-outline" size={18} color={showArchived ? "#fff" : "#666"} />
          <Text style={[styles.tabText, showArchived && styles.activeTabText]}>Archivados</Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.list}>
        {displaySessions.map(session => (
          <TouchableOpacity 
            key={session.id} 
            style={styles.sessionItem}
            onPress={() => handleSelectSession(session.id)}
            onLongPress={() => handleLongPress(session.id, session.title || "")}
          >
            <View style={styles.sessionHeader}>
              <Text style={styles.sessionDate} numberOfLines={1}>
                {session.title || `${new Date(session.date).toLocaleDateString()} ${new Date(session.date).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`}
              </Text>
              {session.pinned && <Ionicons name="pin" size={14} color="#aaa" />}
            </View>
            <Text style={styles.sessionPreview} numberOfLines={2}>{session.preview}</Text>
          </TouchableOpacity>
        ))}
        {displaySessions.length === 0 && (
          <Text style={styles.emptyText}>No hay chats {showArchived ? 'archivados' : 'recientes'}.</Text>
        )}
      </ScrollView>

      {/* Bottom Sheet Modal for Options */}
      <Modal
        visible={isOptionsModalVisible}
        transparent={true}
        animationType="slide"
        onRequestClose={() => setOptionsModalVisible(false)}
      >
        <TouchableOpacity 
          style={styles.modalOverlay} 
          activeOpacity={1} 
          onPress={() => {
            setOptionsModalVisible(false);
            setIsEditingTitle(false);
          }}
        >
          <TouchableOpacity activeOpacity={1} style={styles.bottomSheet}>
            {isEditingTitle ? (
              <View style={styles.editTitleContainer}>
                <Text style={styles.sheetTitle}>Editar Título</Text>
                <TextInput
                  style={styles.input}
                  value={newTitle}
                  onChangeText={setNewTitle}
                  placeholder="Nombre de la conversación..."
                  placeholderTextColor="#666"
                  autoFocus
                />
                <View style={styles.editButtons}>
                  <TouchableOpacity style={styles.btnCancel} onPress={() => setIsEditingTitle(false)}>
                    <Text style={styles.btnText}>Cancelar</Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={styles.btnSave} onPress={saveNewTitle}>
                    <Text style={styles.btnTextDark}>Guardar</Text>
                  </TouchableOpacity>
                </View>
              </View>
            ) : (
              <>
                <View style={styles.sheetHandle} />
                <Text style={styles.sheetTitle}>Opciones del Chat</Text>
                
                <TouchableOpacity style={styles.sheetOption} onPress={() => handleAction('edit')}>
                  <Ionicons name="pencil-outline" size={22} color="#fff" />
                  <Text style={styles.sheetOptionText}>Renombrar</Text>
                </TouchableOpacity>

                <TouchableOpacity style={styles.sheetOption} onPress={() => handleAction('pin')}>
                  <Ionicons name={selectedSession?.pinned ? "pin-outline" : "pin"} size={22} color="#fff" />
                  <Text style={styles.sheetOptionText}>{selectedSession?.pinned ? "Desfijar" : "Fijar (Pin)"}</Text>
                </TouchableOpacity>

                <TouchableOpacity style={styles.sheetOption} onPress={() => handleAction('archive')}>
                  <Ionicons name={selectedSession?.archived ? "arrow-up-outline" : "archive-outline"} size={22} color="#fff" />
                  <Text style={styles.sheetOptionText}>{selectedSession?.archived ? "Desarchivar" : "Archivar"}</Text>
                </TouchableOpacity>

                <TouchableOpacity style={[styles.sheetOption, { borderBottomWidth: 0 }]} onPress={() => handleAction('delete')}>
                  <Ionicons name="trash-outline" size={22} color="#ff4444" />
                  <Text style={[styles.sheetOptionText, { color: '#ff4444' }]}>Eliminar</Text>
                </TouchableOpacity>
              </>
            )}
          </TouchableOpacity>
        </TouchableOpacity>
      </Modal>

    </DrawerContentScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#111' },
  header: { padding: 20, borderBottomWidth: 1, borderBottomColor: '#333' },
  title: { color: '#fff', fontFamily: 'monospace', fontWeight: 'bold', fontSize: 18 },
  newChatBtn: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#fff', margin: 15, padding: 12, borderRadius: 8, justifyContent: 'center' },
  newChatText: { fontFamily: 'monospace', fontWeight: 'bold', color: '#000', marginLeft: 10 },
  
  tabsContainer: { flexDirection: 'row', paddingHorizontal: 15, marginBottom: 10 },
  tab: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 10, borderBottomWidth: 2, borderBottomColor: 'transparent' },
  activeTab: { borderBottomColor: '#fff' },
  tabText: { color: '#666', fontFamily: 'monospace', marginLeft: 6, fontSize: 13 },
  activeTabText: { color: '#fff', fontWeight: 'bold' },

  list: { paddingHorizontal: 15 },
  sessionItem: { paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: '#222' },
  sessionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 },
  sessionDate: { color: '#888', fontSize: 12, fontFamily: 'monospace', flex: 1 },
  sessionPreview: { color: '#ddd', fontSize: 14 },
  emptyText: { color: '#555', fontFamily: 'monospace', textAlign: 'center', marginTop: 20 },

  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', justifyContent: 'flex-end' },
  bottomSheet: { backgroundColor: '#1a1a1a', borderTopLeftRadius: 20, borderTopRightRadius: 20, padding: 20, paddingBottom: 40 },
  sheetHandle: { width: 40, height: 4, backgroundColor: '#444', borderRadius: 2, alignSelf: 'center', marginBottom: 20 },
  sheetTitle: { color: '#888', fontFamily: 'monospace', fontSize: 12, textAlign: 'center', marginBottom: 15 },
  sheetOption: { flexDirection: 'row', alignItems: 'center', paddingVertical: 15, borderBottomWidth: 1, borderBottomColor: '#2a2a2a' },
  sheetOptionText: { color: '#fff', fontFamily: 'monospace', fontSize: 16, marginLeft: 15 },
  
  editTitleContainer: { marginTop: 10 },
  input: { backgroundColor: '#333', color: '#fff', padding: 12, borderRadius: 8, fontFamily: 'monospace', fontSize: 16, marginBottom: 15 },
  editButtons: { flexDirection: 'row', justifyContent: 'flex-end', gap: 10 },
  btnCancel: { padding: 10 },
  btnSave: { backgroundColor: '#fff', paddingHorizontal: 20, paddingVertical: 10, borderRadius: 8 },
  btnText: { color: '#fff', fontFamily: 'monospace', fontWeight: 'bold' },
  btnTextDark: { color: '#000', fontFamily: 'monospace', fontWeight: 'bold' }
});
