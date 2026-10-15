import React, { useEffect, useRef, useState } from 'react';
import { 
  View, StyleSheet, TouchableOpacity, TouchableWithoutFeedback,
  Text, Image, Animated, Dimensions, PanResponder, BackHandler 
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { BlurView } from 'expo-blur';
import { Feather } from '@expo/vector-icons';
import { getBaseUrl } from '../utils/network';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');
const SHEET_HEIGHT = 300;
const DISMISS_THRESHOLD = 80; // pixels to swipe down to dismiss
const EXPAND_THRESHOLD = -120; // pixels to swipe up to expand

interface AssistantOverlayProps {
  mikuState: string;
  isRecording: boolean;
  startRecording: () => void;
  stopRecordingAndSend: () => void;
  messages: any[];
  expandToFullApp: () => void;
  dismissOverlay: () => void;
  serverIp: string | null;
  dots: string;
}

export function AssistantOverlay({
  mikuState,
  isRecording,
  startRecording,
  stopRecordingAndSend,
  messages,
  expandToFullApp,
  dismissOverlay,
  serverIp,
  dots,
}: AssistantOverlayProps) {

  const latestMessage = messages.length > 0 ? messages[messages.length - 1] : null;
  
  // --- Animations ---
  const slideAnim = useRef(new Animated.Value(SHEET_HEIGHT)).current; // starts off-screen
  const borderAnim = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const pressAnim = useRef(new Animated.Value(1)).current;
  const glowOpacity = useRef(new Animated.Value(0.4)).current;
  const panY = useRef(new Animated.Value(0)).current;
  const hintOpacity = useRef(new Animated.Value(1)).current;
  const hintFloat = useRef(new Animated.Value(0)).current;
  const [showHint, setShowHint] = useState(true);

  // Slide in on mount
  useEffect(() => {
    Animated.spring(slideAnim, {
      toValue: 0,
      tension: 60,
      friction: 12,
      useNativeDriver: true,
    }).start();
  }, []);

  // Breathing glow animation
  useEffect(() => {
    const breathe = Animated.loop(
      Animated.sequence([
        Animated.timing(glowOpacity, { toValue: 1, duration: 1500, useNativeDriver: true }),
        Animated.timing(glowOpacity, { toValue: 0.3, duration: 1500, useNativeDriver: true }),
      ])
    );
    breathe.start();
    return () => breathe.stop();
  }, []);

  // Color cycling for border
  useEffect(() => {
    const cycle = Animated.loop(
      Animated.timing(borderAnim, { toValue: 1, duration: 4000, useNativeDriver: false })
    );
    cycle.start();
    return () => cycle.stop();
  }, []);

  // Pulse mic when recording
  useEffect(() => {
    if (isRecording) {
      const pulse = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, { toValue: 1.15, duration: 500, useNativeDriver: true }),
          Animated.timing(pulseAnim, { toValue: 1, duration: 500, useNativeDriver: true }),
        ])
      );
      pulse.start();
      return () => pulse.stop();
    } else {
      pulseAnim.setValue(1);
    }
  }, [isRecording]);

  // Floating hint animation
  useEffect(() => {
    const float = Animated.loop(
      Animated.sequence([
        Animated.timing(hintFloat, { toValue: -5, duration: 800, useNativeDriver: true }),
        Animated.timing(hintFloat, { toValue: 0, duration: 800, useNativeDriver: true }),
      ])
    );
    float.start();
    return () => float.stop();
  }, []);

  // Auto-start recording on mount
  useEffect(() => {
    // Only start if not already recording (just in case)
    if (!isRecording) {
      startRecording();
    }
  }, []);

  // Back button closes overlay
  useEffect(() => {
    const backHandler = BackHandler.addEventListener('hardwareBackPress', () => {
      dismissOverlay();
      return true;
    });
    return () => {
      if (backHandler && backHandler.remove) {
        backHandler.remove();
      }
    };
  }, []);

  // Pan responder for swipe up (expand) / swipe down (dismiss)
  const panResponder = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: (_, gestureState) => Math.abs(gestureState.dy) > 10,
      onPanResponderMove: (_, gestureState) => {
        if (gestureState.dy > 0) {
          panY.setValue(gestureState.dy); // drag down
        } else {
          // Block upward dragging visually to prevent revealing transparent background
          panY.setValue(0);
        }
      },
      onPanResponderRelease: (_, gestureState) => {
        if (gestureState.dy > DISMISS_THRESHOLD) {
          // Swipe down -> dismiss
          Animated.timing(slideAnim, {
            toValue: SHEET_HEIGHT + 50,
            duration: 200,
            useNativeDriver: true,
          }).start(() => dismissOverlay());
        } else if (gestureState.dy < EXPAND_THRESHOLD) {
          // Swipe up -> expand to full app
          expandToFullApp();
        } else {
          // Snap back
          Animated.spring(panY, {
            toValue: 0,
            useNativeDriver: true,
          }).start();
        }
      },
    })
  ).current;

  // Interpolate border colors based on state
  const getBorderColors = () => {
    if (isRecording) return ['#ffffff', '#888888', '#ffffff'] as const;
    if (mikuState === 'thinking') return ['#00ffff', '#ffffff', '#00ffff'] as const;
    if (mikuState === 'talking') return ['#ffffff', '#00ffff', '#ffffff'] as const;
    return ['#555555', '#222222', '#555555'] as const; // idle
  };

  const borderColor1 = borderAnim.interpolate({
    inputRange: [0, 0.33, 0.66, 1],
    outputRange: ['#ffffff', '#00ffff', '#888888', '#ffffff'],
  });

  const stateLabel = mikuState === 'thinking' ? 'Pensando...' 
    : mikuState === 'talking' ? 'Hablando' 
    : isRecording ? 'Escuchando...' 
    : 'Miku';

  return (
    <View style={styles.fullScreen}>
      {/* Tap outside to DISMISS (not expand) */}
      <TouchableWithoutFeedback onPress={dismissOverlay}>
        <View style={styles.backdrop} />
      </TouchableWithoutFeedback>

      {/* Bottom Sheet */}
      <Animated.View style={[styles.sheet, { transform: [{ translateY: slideAnim }] }]}>
        <Animated.View style={{ transform: [{ translateY: panY }] }}>
          <View style={styles.sheetGlowWrapper}>
            {/* Animated background gradient for the border */}
            <Animated.View style={[StyleSheet.absoluteFill, { opacity: glowOpacity, borderRadius: 35, overflow: 'hidden' }]}>
              <LinearGradient
                colors={getBorderColors() as any}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={StyleSheet.absoluteFill}
              />
            </Animated.View>

            <View style={styles.sheetInner}>
          {/* Drag Handle with PanResponder restricted only here */}
          <View style={styles.handleContainer} {...panResponder.panHandlers}>
            <View style={styles.handle} />
          </View>

          {/* State Label */}
          <Text style={styles.stateLabel}>{stateLabel}</Text>

          {/* Main Content Row */}
          <View style={styles.contentRow}>
            {/* Avatar */}
            <View style={styles.avatarWrap}>
              {serverIp ? (
                <Image 
                  source={{ uri: `${getBaseUrl(serverIp)}/api/desktop/miku_gif/${mikuState}` }} 
                  style={styles.avatar}
                />
              ) : (
                <View style={[styles.avatar, { backgroundColor: '#222' }]} />
              )}
            </View>

            {/* Message */}
            <View style={styles.textWrap}>
              {mikuState === 'thinking' ? (
                <View style={styles.dotsContainer}>
                  <Text style={styles.dotsText}>{dots || '...'}</Text>
                </View>
              ) : (
                <Text style={styles.messageText} numberOfLines={3}>
                  {latestMessage && latestMessage.sender === 'miku' 
                    ? latestMessage.text 
                    : latestMessage && latestMessage.sender === 'user'
                      ? '...'
                      : "Hola, soy Miku. ¿En qué te ayudo?"}
                </Text>
              )}
            </View>

            {/* Mic Button */}
            <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
              <Animated.View style={{ transform: [{ scale: pressAnim }] }}>
                <TouchableOpacity 
                  style={[
                    styles.micBtn, 
                    isRecording && styles.micBtnActive
                  ]}
                  hitSlop={{ top: 50, bottom: 50, left: 50, right: 50 }}
                  onPressIn={() => {
                    Animated.spring(pressAnim, {
                      toValue: 0.85,
                      useNativeDriver: true,
                    }).start();
                    startRecording();
                  }}
                  onPressOut={() => {
                    Animated.spring(pressAnim, {
                      toValue: 1,
                      friction: 4,
                      tension: 40,
                      useNativeDriver: true,
                    }).start();
                    stopRecordingAndSend();
                  }}
                  activeOpacity={1}
                >
                  <Feather 
                    name="mic" 
                    size={28} 
                    color={isRecording ? "#000" : "#fff"} 
                  />
                </TouchableOpacity>
              </Animated.View>
            </Animated.View>
          </View>

          {/* Animated Hint Pill */}
          <Animated.View 
            style={[
              styles.hintPill, 
              { opacity: hintOpacity, transform: [{ translateY: hintFloat }] }
            ]}
            pointerEvents="none"
          >
            <Feather name="chevron-up" size={14} color="#888" />
            <Text style={styles.hintText}>Desliza para abrir</Text>
          </Animated.View>
        </View>
          </View>
        </Animated.View>
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  fullScreen: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'transparent',
  },

  // Sheet
  sheet: {
    borderTopLeftRadius: 15,
    borderTopRightRadius: 15,
    shadowColor: '#00ffff',
    shadowOffset: { width: 0, height: -5 },
    shadowOpacity: 0.9,
    shadowRadius: 50,
    elevation: 30,
    zIndex: 50,
  },
  sheetGlowWrapper: {
    borderTopLeftRadius: 15,
    borderTopRightRadius: 15,
    paddingTop: 4,
    paddingHorizontal: 4,
    backgroundColor: 'transparent',
  },
  sheetInner: {
    backgroundColor: 'rgba(5, 5, 5, 0.95)',
    borderTopLeftRadius: 12,
    borderTopRightRadius: 12,
    paddingHorizontal: 20,
    paddingBottom: 45,
    paddingTop: 12,
    overflow: 'hidden',
  },

  // Handle
  handleContainer: {
    alignItems: 'center',
    marginBottom: 12,
    paddingVertical: 10, // increase hit area
  },
  handle: {
    width: 40,
    height: 5,
    backgroundColor: 'rgba(255, 255, 255, 0.25)', // iOS grabber color
    borderRadius: 2.5,
  },

  // State
  stateLabel: {
    color: '#666',
    fontFamily: 'monospace',
    fontSize: 11,
    textAlign: 'center',
    marginBottom: 16,
    letterSpacing: 2,
    textTransform: 'uppercase',
  },

  // Content
  contentRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatarWrap: {
    marginRight: 14,
  },
  avatar: {
    width: 60,
    height: 60,
    borderRadius: 30,
    resizeMode: 'contain',
  },
  textWrap: {
    flex: 1,
    marginRight: 14,
  },
  dotsContainer: {
    height: 40,
    justifyContent: 'center',
  },
  dotsText: {
    color: '#00d2ff', // iOS System Blue
    fontFamily: 'monospace',
    fontSize: 28,
    fontWeight: 'bold',
  },
  messageText: {
    color: '#eee',
    fontFamily: 'monospace',
    fontSize: 15,
    lineHeight: 21,
  },

  // Mic
  micBtn: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: 'rgba(255,255,255,0.08)', // Glassy look
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: 'rgba(255,255,255,0.15)',
  },
  micBtnActive: {
    backgroundColor: '#ffffff', 
    borderColor: '#00ffff',
  },

  // Hint Pill
  hintPill: {
    flexDirection: 'row',
    alignSelf: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.06)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    marginTop: 18,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  hintText: {
    color: '#888',
    fontFamily: 'monospace',
    fontSize: 10,
    marginLeft: 4,
  },
});
