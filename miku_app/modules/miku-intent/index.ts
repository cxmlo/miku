import { requireNativeModule } from 'expo-modules-core';

let MikuIntent: any = null;

try {
  MikuIntent = requireNativeModule('MikuIntent');
} catch (e) {
  // Graceful fallback during Expo Go or when not built natively
  console.warn("MikuIntent module not available, fallback to null");
}

export function getIntentAction(): string | null {
  if (MikuIntent) {
    return MikuIntent.getIntentAction();
  }
  return null;
}
