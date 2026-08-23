import React, { useState } from 'react';
import { View, Text, StyleSheet, Modal, TouchableOpacity, TextInput, ActivityIndicator } from 'react-native';
import { useApp } from '../../context/AppContext';

interface Props {
  visible: boolean;
  onClose: () => void;
}

export const BackendSettingsModal: React.FC<Props> = ({ visible, onClose }) => {
  const { 
    backendUrl, 
    setBackendUrl, 
    isBackendConnected, 
    checkBackendHealth,
    showToast 
  } = useApp();

  const [inputUrl, setInputUrl] = useState(backendUrl);
  const [testing, setTesting] = useState(false);

  const handleSaveAndTest = async () => {
    setTesting(true);
    setBackendUrl(inputUrl);
    const success = await checkBackendHealth();
    setTesting(false);
    if (success) {
      onClose();
    } else {
      showToast('Connection Failed', 'Could not reach backend at this URL. Make sure uvicorn server is running.', 'warning');
    }
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={true}
      onRequestClose={onClose}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.sheetContainer}>
          {/* Header */}
          <View style={styles.headerRow}>
            <View style={styles.titleRow}>
              <View style={styles.iconBox}>
                <Text style={styles.iconEmoji}>🔌</Text>
              </View>
              <View>
                <Text style={styles.titleText}>Backend Server Config</Text>
                <Text style={styles.subText}>FastAPI + WebSocket Connection</Text>
              </View>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
              <Text style={styles.closeText}>✕</Text>
            </TouchableOpacity>
          </View>

          {/* Current Status Pill */}
          <View style={[styles.statusBanner, isBackendConnected ? styles.statusConnected : styles.statusOffline]}>
            <View style={[styles.statusDot, isBackendConnected ? styles.dotGreen : styles.dotAmber]} />
            <Text style={[styles.statusTitle, isBackendConnected ? styles.textGreen : styles.textAmber]}>
              {isBackendConnected ? 'Backend Connected & Synced' : 'Offline / Standalone Simulator'}
            </Text>
          </View>

          {/* URL Input */}
          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>FastAPI Server URL / Host</Text>
            <TextInput
              style={styles.textInput}
              value={inputUrl}
              onChangeText={setInputUrl}
              placeholder="http://localhost:8000 or http://10.20.132.39:8000"
              placeholderTextColor="#64748b"
              autoCapitalize="none"
              autoCorrect={false}
            />
            <Text style={styles.inputHint}>
              On physical phone: Use your local WiFi IP (e.g. http://10.20.132.39:8000)
            </Text>
          </View>

          {/* Quick Preset Buttons */}
          <View style={styles.presetsGroup}>
            <Text style={styles.presetsLabel}>Quick Presets:</Text>
            <View style={styles.presetButtonsRow}>
              <TouchableOpacity
                onPress={() => setInputUrl('http://localhost:8000')}
                style={styles.presetBtn}
              >
                <Text style={styles.presetBtnText}>localhost:8000</Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => setInputUrl('http://10.20.132.39:8000')}
                style={styles.presetBtn}
              >
                <Text style={styles.presetBtnText}>LAN (10.20.132.39)</Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => setInputUrl('http://10.0.2.2:8000')}
                style={styles.presetBtn}
              >
                <Text style={styles.presetBtnText}>Android Emulator</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Test & Connect Button */}
          <TouchableOpacity
            onPress={handleSaveAndTest}
            disabled={testing}
            style={styles.connectBtn}
          >
            {testing ? (
              <ActivityIndicator color="#ffffff" size="small" />
            ) : (
              <Text style={styles.connectBtnText}>Test & Connect to Server</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'flex-end',
  },
  sheetContainer: {
    backgroundColor: '#0f172a',
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#334155',
    gap: 12,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
    paddingBottom: 10,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  iconBox: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: '#1e1b4b',
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconEmoji: {
    fontSize: 18,
  },
  titleText: {
    fontSize: 15,
    fontWeight: '800',
    color: '#ffffff',
  },
  subText: {
    fontSize: 10,
    color: '#94a3b8',
    marginTop: 1,
  },
  closeBtn: {
    backgroundColor: '#1e293b',
    width: 30,
    height: 30,
    borderRadius: 15,
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeText: {
    color: '#cbd5e1',
    fontSize: 12,
    fontWeight: '700',
  },
  statusBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 10,
    borderRadius: 12,
    gap: 8,
    borderWidth: 1,
  },
  statusConnected: {
    backgroundColor: 'rgba(6, 78, 59, 0.5)',
    borderColor: '#065f46',
  },
  statusOffline: {
    backgroundColor: 'rgba(120, 53, 15, 0.5)',
    borderColor: '#92400e',
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  dotGreen: {
    backgroundColor: '#10b981',
  },
  dotAmber: {
    backgroundColor: '#f59e0b',
  },
  statusTitle: {
    fontSize: 12,
    fontWeight: '700',
  },
  textGreen: {
    color: '#34d399',
  },
  textAmber: {
    color: '#fcd34d',
  },
  inputGroup: {
    gap: 4,
  },
  inputLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#cbd5e1',
  },
  textInput: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: '#ffffff',
    fontSize: 12,
    fontFamily: 'monospace',
    borderWidth: 1,
    borderColor: '#334155',
  },
  inputHint: {
    fontSize: 9,
    color: '#64748b',
    marginTop: 2,
  },
  presetsGroup: {
    gap: 6,
  },
  presetsLabel: {
    fontSize: 10,
    color: '#94a3b8',
    fontWeight: '600',
  },
  presetButtonsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  presetBtn: {
    backgroundColor: '#1e293b',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#334155',
  },
  presetBtnText: {
    fontSize: 10,
    color: '#cbd5e1',
    fontFamily: 'monospace',
  },
  connectBtn: {
    backgroundColor: '#4f46e5',
    paddingVertical: 12,
    borderRadius: 14,
    alignItems: 'center',
    marginTop: 4,
  },
  connectBtnText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '800',
  },
});
