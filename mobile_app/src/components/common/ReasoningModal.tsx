import React from 'react';
import { View, Text, StyleSheet, Modal, TouchableOpacity, ScrollView } from 'react-native';
import { useApp } from '../../context/AppContext';

export const ReasoningModal: React.FC = () => {
  const { 
    inspectReasoningId, 
    setInspectReasoningId, 
    reasoningChains 
  } = useApp();

  if (!inspectReasoningId) return null;

  const currentChain = reasoningChains[inspectReasoningId] || reasoningChains['traffic_agent'];

  const getStepIcon = (type: string) => {
    switch (type) {
      case 'observation': return '👁️';
      case 'evaluation': return '🧠';
      case 'action': return '⚡';
      case 'reward': return '📈';
      case 'goal': return '🎯';
      case 'options': return '❓';
      case 'decision': return '✅';
      case 'reason': return '💡';
      default: return '🧠';
    }
  };

  return (
    <Modal
      visible={!!inspectReasoningId}
      animationType="slide"
      transparent={true}
      onRequestClose={() => setInspectReasoningId(null)}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.sheetContainer}>
          {/* Header */}
          <View style={styles.headerRow}>
            <View style={styles.titleIconRow}>
              <View style={styles.iconBox}>
                <Text style={styles.iconText}>🧠</Text>
              </View>
              <View>
                <Text style={styles.modalTitle}>Agent Reasoning Inspector</Text>
                <Text style={styles.modalSub}>
                  {currentChain.entityName} • {(currentChain.confidence * 100).toFixed(0)}% Confidence
                </Text>
              </View>
            </View>
            <TouchableOpacity onPress={() => setInspectReasoningId(null)} style={styles.closeBtn}>
              <Text style={styles.closeText}>✕</Text>
            </TouchableOpacity>
          </View>

          {/* Context Banner */}
          <View style={styles.contextBanner}>
            <Text style={styles.contextLabel}>OBJECTIVE:</Text>
            <Text style={styles.contextText}>{currentChain.goalOrContext}</Text>
          </View>

          {/* Steps Trace Scroll */}
          <ScrollView style={styles.stepsScroll} showsVerticalScrollIndicator={false}>
            {currentChain.steps.map((step, idx) => {
              const isLast = idx === currentChain.steps.length - 1;
              return (
                <View key={step.id} style={styles.stepBlock}>
                  <View style={styles.stepCard}>
                    <View style={styles.stepTopRow}>
                      <View style={styles.stepTitleRow}>
                        <Text style={styles.stepIcon}>{getStepIcon(step.type)}</Text>
                        <Text style={styles.stepTitle}>{step.title}</Text>
                      </View>
                      <View style={styles.stepMetaRow}>
                        <Text style={styles.stepTypeBadge}>{step.type.toUpperCase()}</Text>
                        <Text style={styles.stepTime}>{step.timestamp}</Text>
                      </View>
                    </View>

                    <Text style={styles.stepDesc}>{step.description}</Text>

                    {step.detail && (
                      <View style={styles.detailBox}>
                        <Text style={styles.detailText}>{step.detail}</Text>
                      </View>
                    )}

                    {step.metricChange && (
                      <View style={styles.metricBox}>
                        <Text style={styles.metricText}>📈 {step.metricChange}</Text>
                      </View>
                    )}
                  </View>

                  {!isLast && (
                    <View style={styles.arrowContainer}>
                      <Text style={styles.arrowText}>↓</Text>
                    </View>
                  )}
                </View>
              );
            })}
          </ScrollView>

          {/* Footer */}
          <View style={styles.footer}>
            <Text style={styles.footerText}>
              Explainable AI (XAI) cognitive graph generated from live simulation runtime.
            </Text>
          </View>
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
    maxHeight: '90%',
    borderTopWidth: 1,
    borderTopColor: '#334155',
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
    paddingBottom: 12,
    marginBottom: 10,
  },
  titleIconRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  iconBox: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: '#3b0764',
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconText: {
    fontSize: 18,
  },
  modalTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#ffffff',
  },
  modalSub: {
    fontSize: 11,
    color: '#c084fc',
    marginTop: 1,
  },
  closeBtn: {
    backgroundColor: '#1e293b',
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeText: {
    color: '#cbd5e1',
    fontSize: 14,
    fontWeight: '700',
  },
  contextBanner: {
    backgroundColor: '#1e1b4b',
    padding: 10,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#4338ca',
    marginBottom: 12,
  },
  contextLabel: {
    fontSize: 9,
    fontWeight: '800',
    color: '#818cf8',
    letterSpacing: 0.5,
  },
  contextText: {
    fontSize: 11,
    color: '#e0e7ff',
    marginTop: 2,
    fontWeight: '500',
  },
  stepsScroll: {
    maxHeight: 420,
  },
  stepBlock: {
    alignItems: 'center',
  },
  stepCard: {
    width: '100%',
    backgroundColor: 'rgba(30, 41, 59, 0.6)',
    borderRadius: 16,
    padding: 12,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  stepTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  stepTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  stepIcon: {
    fontSize: 14,
  },
  stepTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#ffffff',
  },
  stepMetaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  stepTypeBadge: {
    fontSize: 9,
    fontFamily: 'monospace',
    fontWeight: '700',
    color: '#c084fc',
    backgroundColor: '#3b0764',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  stepTime: {
    fontSize: 9,
    fontFamily: 'monospace',
    color: '#64748b',
  },
  stepDesc: {
    fontSize: 12,
    color: '#cbd5e1',
    lineHeight: 16,
  },
  detailBox: {
    backgroundColor: '#090d16',
    borderRadius: 8,
    padding: 8,
    marginTop: 6,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  detailText: {
    fontSize: 10,
    fontFamily: 'monospace',
    color: '#94a3b8',
    lineHeight: 14,
  },
  metricBox: {
    backgroundColor: 'rgba(6, 78, 59, 0.5)',
    borderRadius: 8,
    padding: 6,
    marginTop: 6,
  },
  metricText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#34d399',
    fontFamily: 'monospace',
  },
  arrowContainer: {
    paddingVertical: 4,
  },
  arrowText: {
    fontSize: 14,
    color: '#6366f1',
    fontWeight: '900',
  },
  footer: {
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#1e293b',
    alignItems: 'center',
  },
  footerText: {
    fontSize: 10,
    color: '#64748b',
    textAlign: 'center',
  },
});
