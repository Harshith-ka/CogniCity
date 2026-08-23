import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useApp } from '../../context/AppContext';

export const ReasoningInspectorView: React.FC = () => {
  const { reasoningChains } = useApp();
  const [activeEntityKey, setActiveEntityKey] = useState<string>('traffic_agent');

  const currentChain = reasoningChains[activeEntityKey] || reasoningChains['traffic_agent'];

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
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {/* Switcher */}
      <View style={styles.switcherRow}>
        <TouchableOpacity
          onPress={() => setActiveEntityKey('traffic_agent')}
          style={[styles.switchBtn, activeEntityKey === 'traffic_agent' && styles.switchBtnActiveIndigo]}
        >
          <Text style={[styles.switchText, activeEntityKey === 'traffic_agent' && styles.switchTextActive]}>
            🤖 Traffic Agent AI
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => setActiveEntityKey('citizen_4821')}
          style={[styles.switchBtn, activeEntityKey === 'citizen_4821' && styles.switchBtnActivePurple]}
        >
          <Text style={[styles.switchText, activeEntityKey === 'citizen_4821' && styles.switchTextActive]}>
            👩🏫 Citizen #4821
          </Text>
        </TouchableOpacity>
      </View>

      {/* Overview Context Box */}
      <View style={styles.contextCard}>
        <View style={styles.contextTop}>
          <View style={styles.entityNameRow}>
            <Text style={styles.entityIcon}>{activeEntityKey === 'traffic_agent' ? '🚦' : '👩🏫'}</Text>
            <View>
              <Text style={styles.entityNameText}>{currentChain.entityName}</Text>
              <Text style={styles.entityTypeBadge}>{currentChain.entityType.toUpperCase()}</Text>
            </View>
          </View>
          <View style={styles.confBox}>
            <Text style={styles.confLabel}>Confidence</Text>
            <Text style={styles.confVal}>{(currentChain.confidence * 100).toFixed(0)}%</Text>
          </View>
        </View>

        <View style={styles.goalSection}>
          <Text style={styles.goalLabel}>OBJECTIVE CONTEXT</Text>
          <Text style={styles.goalText}>{currentChain.goalOrContext}</Text>
        </View>
      </View>

      {/* Trace List */}
      <View style={styles.traceSection}>
        <Text style={styles.traceHeading}>COGNITIVE REASONING TRACE</Text>

        <View style={styles.stepsContainer}>
          {currentChain.steps.map((step, idx) => {
            const isLast = idx === currentChain.steps.length - 1;
            return (
              <View key={step.id} style={styles.stepBlock}>
                <View style={styles.stepCard}>
                  <View style={styles.stepHeader}>
                    <View style={styles.stepTitleRow}>
                      <Text style={styles.stepIcon}>{getStepIcon(step.type)}</Text>
                      <Text style={styles.stepTitle}>{step.title}</Text>
                    </View>
                    <View style={styles.stepMetaRow}>
                      <Text style={styles.stepType}>{step.type.toUpperCase()}</Text>
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
                  <View style={styles.arrowBox}>
                    <Text style={styles.arrowText}>↓</Text>
                  </View>
                )}
              </View>
            );
          })}
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#090d16',
  },
  contentContainer: {
    padding: 14,
    paddingBottom: 30,
    gap: 12,
  },
  switcherRow: {
    flexDirection: 'row',
    backgroundColor: '#0f172a',
    borderRadius: 16,
    padding: 4,
    borderWidth: 1,
    borderColor: '#1e293b',
    gap: 6,
  },
  switchBtn: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 12,
    alignItems: 'center',
  },
  switchBtnActiveIndigo: {
    backgroundColor: '#4f46e5',
  },
  switchBtnActivePurple: {
    backgroundColor: '#7c3aed',
  },
  switchText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#94a3b8',
  },
  switchTextActive: {
    color: '#ffffff',
    fontWeight: '800',
  },
  contextCard: {
    backgroundColor: 'rgba(15, 23, 42, 0.9)',
    borderRadius: 24,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  contextTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
    paddingBottom: 10,
  },
  entityNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  entityIcon: {
    fontSize: 22,
  },
  entityNameText: {
    fontSize: 14,
    fontWeight: '800',
    color: '#ffffff',
  },
  entityTypeBadge: {
    fontSize: 9,
    fontFamily: 'monospace',
    color: '#c084fc',
    marginTop: 2,
  },
  confBox: {
    alignItems: 'flex-end',
  },
  confLabel: {
    fontSize: 9,
    color: '#94a3b8',
  },
  confVal: {
    fontSize: 12,
    fontWeight: '800',
    color: '#34d399',
    fontFamily: 'monospace',
  },
  goalSection: {
    paddingTop: 10,
  },
  goalLabel: {
    fontSize: 9,
    fontWeight: '800',
    color: '#64748b',
    letterSpacing: 0.5,
  },
  goalText: {
    fontSize: 12,
    color: '#cbd5e1',
    marginTop: 2,
    lineHeight: 16,
  },
  traceSection: {
    marginTop: 4,
  },
  traceHeading: {
    fontSize: 11,
    fontWeight: '800',
    color: '#94a3b8',
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  stepsContainer: {
    gap: 2,
  },
  stepBlock: {
    alignItems: 'center',
  },
  stepCard: {
    width: '100%',
    backgroundColor: 'rgba(15, 23, 42, 0.9)',
    borderRadius: 20,
    padding: 14,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  stepHeader: {
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
  stepType: {
    fontSize: 9,
    fontFamily: 'monospace',
    fontWeight: '700',
    color: '#a5b4fc',
    backgroundColor: '#1e1b4b',
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
    borderRadius: 10,
    padding: 10,
    marginTop: 8,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  detailText: {
    fontSize: 11,
    fontFamily: 'monospace',
    color: '#94a3b8',
    lineHeight: 15,
  },
  metricBox: {
    backgroundColor: 'rgba(6, 78, 59, 0.5)',
    borderRadius: 8,
    padding: 8,
    marginTop: 8,
  },
  metricText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#34d399',
    fontFamily: 'monospace',
  },
  arrowBox: {
    paddingVertical: 4,
  },
  arrowText: {
    fontSize: 14,
    color: '#6366f1',
    fontWeight: '900',
  },
});
