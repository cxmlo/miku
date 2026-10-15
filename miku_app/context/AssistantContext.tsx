import React, { createContext, useContext, useState, useEffect } from 'react';
import { BackHandler } from 'react-native';
import { getIntentAction } from '../modules/miku-intent';

interface AssistantContextData {
  isAssistantMode: boolean;
  expandToFullApp: () => void;
  dismissOverlay: () => void;
}

const AssistantContext = createContext<AssistantContextData>({
  isAssistantMode: false,
  expandToFullApp: () => {},
  dismissOverlay: () => {},
});

export const AssistantProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAssistantMode, setIsAssistantMode] = useState(false);

  useEffect(() => {
    const action = getIntentAction();
    if (action === 'android.intent.action.ASSIST' || action === 'android.intent.action.VOICE_COMMAND') {
      setIsAssistantMode(true);
    }
  }, []);

  const expandToFullApp = () => {
    setIsAssistantMode(false);
  };

  const dismissOverlay = () => {
    // Close the overlay and go back to whatever the user was doing
    setIsAssistantMode(false);
    // On Android, simulate pressing Back to leave the activity
    BackHandler.exitApp();
  };

  return (
    <AssistantContext.Provider value={{ isAssistantMode, expandToFullApp, dismissOverlay }}>
      {children}
    </AssistantContext.Provider>
  );
};

export const useAssistant = () => useContext(AssistantContext);
