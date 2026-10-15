import { Drawer } from 'expo-router/drawer';
import { StatusBar } from 'expo-status-bar';
import { View, StyleSheet, TouchableOpacity, Text } from 'react-native';
import { WebSocketProvider } from '../context/WebSocketContext';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { AssistantProvider, useAssistant } from '../context/AssistantContext';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation, useRouter } from 'expo-router';
import { DrawerActions } from '@react-navigation/native';
import { ChatHistoryDrawer } from '../components/ChatHistoryDrawer';
import { Feather } from '@expo/vector-icons';
import notifee, { EventType } from '@notifee/react-native';
import { useShareIntent } from 'expo-share-intent';
import { ShareOverlay } from '../components/ShareOverlay';
import { BlurView } from 'expo-blur';

// Mantiene el proceso vivo en segundo plano
notifee.registerForegroundService((notification) => {
  return new Promise((resolve) => {
    // Escuchar eventos para resolver y liberar la promesa cuando se detenga el servicio
    notifee.onForegroundEvent(({ type, detail }) => {
      if (type === EventType.DISMISSED || (type === EventType.ACTION_PRESS && detail.pressAction?.id === 'stop')) {
        resolve(null as any);
      }
    });
  });
});

function MainLayout() {
  const { isAssistantMode } = useAssistant();
  const navigation = useNavigation();
  const router = useRouter();
  const { hasShareIntent, shareIntent, resetShareIntent } = useShareIntent();

  if (hasShareIntent && (shareIntent.text || shareIntent.webUrl || (shareIntent.files && shareIntent.files.length > 0))) {
    return (
      <ShareOverlay shareIntent={shareIntent} resetShareIntent={resetShareIntent} />
    );
  }

  if (isAssistantMode) {
    // Transparent overlay mode
    return (
      <GestureHandlerRootView style={{ flex: 1 }}>
        <WebSocketProvider>
          <View style={styles.transparentContainer}>
            <StatusBar style="light" />
            <Drawer
              screenOptions={{
                headerShown: false,
                sceneStyle: { backgroundColor: 'transparent' },
              }}>
              <Drawer.Screen name="index" options={{ title: 'Assistant' }} />
              <Drawer.Screen name="devices" options={{ title: 'Devices' }} />
            </Drawer>
            {/* We will let index.tsx render the bottom sheet. We pass a prop or use a context? 
                Actually, index.tsx can read getIntentAction itself or use a global context.
                For simplicity, we'll just let index.tsx be transparent. */}
          </View>
        </WebSocketProvider>
      </GestureHandlerRootView>
    );
  }

  // Full app mode with Drawer
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <WebSocketProvider>
        <View style={styles.container}>
          <StatusBar style="light" />
          <Drawer
            drawerContent={(props) => <ChatHistoryDrawer {...props} />}
            screenOptions={{
              drawerPosition: 'right',
              drawerType: 'slide',
              drawerStyle: {
                backgroundColor: '#111',
                width: 280,
              },
              headerStyle: {
                backgroundColor: '#050505',
                borderBottomWidth: 1,
                borderBottomColor: '#333',
              },
              headerTintColor: '#fff',
              headerTitleStyle: {
                fontFamily: 'monospace',
                fontWeight: 'bold',
                fontSize: 16,
              },
              sceneStyle: { backgroundColor: '#050505' },
            }}>
            <Drawer.Screen 
              name="index" 
              options={({ navigation }) => ({ 
                title: 'MIKU SYSTEM',
                headerShown: true,
                drawerLabel: 'Current Chat',
                headerRight: () => (
                  <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    <TouchableOpacity onPress={() => router.push('/settings' as any)} style={{ marginRight: 15 }}>
                      <Ionicons name="settings-outline" size={22} color="#fff" />
                    </TouchableOpacity>
                    <TouchableOpacity onPress={() => router.push('/diagnostics' as any)} style={{ marginRight: 15 }}>
                      <Ionicons name="pulse-outline" size={22} color="#fff" />
                    </TouchableOpacity>
                    <TouchableOpacity onPress={() => router.push('/devices')} style={{ marginRight: 15 }}>
                      <Feather name="smartphone" size={24} color="#fff" />
                    </TouchableOpacity>
                    <TouchableOpacity 
                      style={{ marginRight: 15 }} 
                      onPress={() => navigation.dispatch(DrawerActions.toggleDrawer())}
                    >
                      <Ionicons name="menu" size={24} color="#fff" />
                    </TouchableOpacity>
                  </View>
                )
              })} 
            />
            <Drawer.Screen 
              name="devices" 
              options={{ 
                title: 'DEVICES',
                drawerLabel: 'Settings / Devices',
                headerLeft: () => (
                  <TouchableOpacity onPress={() => router.back()} style={{ marginLeft: 15 }}>
                    <Ionicons name="arrow-back" size={24} color="#fff" />
                  </TouchableOpacity>
                )
              }} 
            />
            <Drawer.Screen 
              name="diagnostics" 
              options={{ 
                title: 'SYSTEM MONITOR',
                drawerLabel: 'System Monitor',
                headerLeft: () => (
                  <TouchableOpacity onPress={() => router.back()} style={{ marginLeft: 15 }}>
                    <Ionicons name="arrow-back" size={24} color="#fff" />
                  </TouchableOpacity>
                )
              }} 
            />
            <Drawer.Screen 
              name="settings" 
              options={{ 
                title: 'AI SETTINGS',
                drawerLabel: 'Configuración IA',
                headerLeft: () => (
                  <TouchableOpacity onPress={() => router.back()} style={{ marginLeft: 15 }}>
                    <Ionicons name="arrow-back" size={24} color="#fff" />
                  </TouchableOpacity>
                )
              }} 
            />
          </Drawer>
        </View>
      </WebSocketProvider>
    </GestureHandlerRootView>
  );
}

export default function RootLayout() {
  return (
    <AssistantProvider>
      <MainLayout />
    </AssistantProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000', // System background base
  },
  transparentContainer: {
    flex: 1,
    backgroundColor: 'transparent',
  },
});
