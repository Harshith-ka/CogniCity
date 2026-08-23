import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useApp } from '../../context/AppContext';

export const ToastContainer: React.FC = () => {
  const { toasts, dismissToast } = useApp();

  if (toasts.length === 0) return null;

  const getBorderColor = (severity: 'critical' | 'warning' | 'info' | 'success') => {
    switch (severity) {
      case 'critical': return '#e11d48';
      case 'warning': return '#d97706';
      case 'success': return '#059669';
      default: return '#4f46e5';
    }
  };

  const getBgColor = (severity: 'critical' | 'warning' | 'info' | 'success') => {
    switch (severity) {
      case 'critical': return 'rgba(76, 5, 25, 0.95)';
      case 'warning': return 'rgba(69, 26, 3, 0.95)';
      case 'success': return 'rgba(6, 78, 59, 0.95)';
      default: return 'rgba(15, 23, 42, 0.95)';
    }
  };

  return (
    <View style={styles.container} pointerEvents="box-none">
      {toasts.map((toast) => (
        <View
          key={toast.id}
          style={[
            styles.toastBox,
            {
              backgroundColor: getBgColor(toast.severity),
              borderColor: getBorderColor(toast.severity),
            },
          ]}
        >
          <View style={styles.toastContent}>
            <Text style={styles.toastTitle}>{toast.title}</Text>
            <Text style={styles.toastMessage}>{toast.message}</Text>
          </View>
          <TouchableOpacity
            onPress={() => dismissToast(toast.id)}
            style={styles.closeBtn}
          >
            <Text style={styles.closeText}>✕</Text>
          </TouchableOpacity>
        </View>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 55,
    left: 12,
    right: 12,
    zIndex: 999,
    gap: 8,
  },
  toastBox: {
    padding: 12,
    borderRadius: 16,
    borderWidth: 1,
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  toastContent: {
    flex: 1,
    marginRight: 8,
  },
  toastTitle: {
    fontSize: 12,
    fontWeight: '800',
    color: '#ffffff',
    marginBottom: 2,
  },
  toastMessage: {
    fontSize: 11,
    color: '#f1f5f9',
    lineHeight: 15,
  },
  closeBtn: {
    padding: 4,
  },
  closeText: {
    color: '#94a3b8',
    fontSize: 12,
  },
});
