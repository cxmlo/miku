import * as TaskManager from 'expo-task-manager';
import * as SecureStore from 'expo-secure-store';
import { getWsUrl } from '../utils/network';

const BACKGROUND_WS_TASK = 'MIKU_BACKGROUND_WS';
const SERVER_IP_KEY = 'miku_server_ip';
const API_KEY = 'miku_secure_key_2026';

// Define the background task
TaskManager.defineTask(BACKGROUND_WS_TASK, async () => {
  try {
    const serverIp = await SecureStore.getItemAsync(SERVER_IP_KEY);
    if (!serverIp) return;

    // Simple ping to keep connection alive
    const response = await fetch(`http://${serverIp}:8000/api/desktop/info`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    
    if (response.ok) {
      console.log('[MikuBG] Keep-alive ping successful');
    } else {
      console.log('[MikuBG] Server responded with:', response.status);
    }
  } catch (error) {
    console.error('[MikuBG] Keep-alive failed:', error);
  }
});

export const TASK_NAME = BACKGROUND_WS_TASK;
