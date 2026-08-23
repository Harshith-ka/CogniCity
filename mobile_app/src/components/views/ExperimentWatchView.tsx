import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useApp } from '../../context/AppContext';

export const ExperimentWatchView: React.FC = () => {
  const { experiments, setIsCreateExpOpen, setActiveTab } = useApp();

  const activeExp = experiments.find((e) => e.status === 'running') || experiments[0];
  const completedExps = experiments.filter((e) => e.status === 'completed');

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {/* Watch Hero Card */}
      <View style={styles.watchHeroCard}>
        <View style={styles.watchTop}>
          <View style={styles.watchTagRow}>
            <Text style={styles.watchTagText}>EXPERIMENT WATCH HUD</Text>
            <View style={styles.pulseDot} />
          </View>
          <View style={styles.cloudBadge}>
            <Text style={styles.cloudBadgeText}>Cloud Engine Live</Text>
          </View>
        </View>

        {/* Progress Display */}
        <View style={styles.progressRow}>
          <View style={styles.progressCircleBox}>
            <Text style={styles.progressNumberText}>{activeExp.progressPercent}%</Text>
          </View>

          <View style={styles.expInfoBox}>
            <Text style={styles.expTitle} numberOfLines={1}>{activeExp.title}</Text>
            <Text style={styles.agentName}>Agent: {activeExp.agentName}</Text>
            <Text style={styles.agentHours}>⚡ {activeExp.agentHoursProcessed}</Text>
          </View>
        </View>

        {/* ETA Bar */}
        <View style={styles.etaBar}>
          <Text style={styles.etaLabel}>⏱️ Estimated Remaining:</Text>
          <Text style={styles.etaValue}>{activeExp.estimatedRemaining}</Text>
        </View>

        {/* Action Buttons */}
        <View style={styles.actionRow}>
          <TouchableOpacity
            onPress={() => setActiveTab('comparison')}
            style={styles.compareBtn}
          >
            <Text style={styles.compareBtnText}>Compare with Baseline ➔</Text>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={() => setIsCreateExpOpen(true)}
            style={styles.newExpBtn}
          >
            <Text style={styles.newExpBtnText}>+ New</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Cloud Notification Simulator Card */}
      <View style={styles.pushCard}>
        <View style={styles.pushHeader}>
          <Text style={styles.pushTitle}>🔔 Mobile Push Alerts Enabled</Text>
          <View style={styles.activeTag}>
            <Text style={styles.activeTagText}>Active</Text>
          </View>
        </View>
        <Text style={styles.pushDesc}>
          Your device will automatically trigger a push alert when the 10 million agent-hour run reaches 100% completion. You can safely close your laptop or browser.
        </Text>
      </View>

      {/* Completed Runs List */}
      <View style={styles.completedSection}>
        <Text style={styles.completedHeading}>COMPLETED CLOUD RUNS</Text>
        <View style={styles.completedList}>
          {completedExps.map((exp) => (
            <TouchableOpacity
              key={exp.id}
              onPress={() => setActiveTab('comparison')}
              style={styles.completedCard}
            >
              <View style={styles.completedLeft}>
                <View style={styles.checkIconBox}>
                  <Text style={styles.checkIcon}>✓</Text>
                </View>
                <View>
                  <Text style={styles.completedTitle}>{exp.title}</Text>
                  <Text style={styles.completedSub}>
                    {exp.environment} • Score: {exp.metrics?.accuracy ?? 94}%
                  </Text>
                </View>
              </View>
              <Text style={styles.resultsLink}>Results ➔</Text>
            </TouchableOpacity>
          ))}
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
  watchHeroCard: {
    backgroundColor: 'rgba(15, 23, 42, 0.9)',
    borderRadius: 24,
    padding: 16,
    borderWidth: 1,
    borderColor: '#312e81',
    gap: 12,
  },
  watchTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  watchTagRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  watchTagText: {
    fontSize: 9,
    fontFamily: 'monospace',
    fontWeight: '800',
    color: '#818cf8',
    letterSpacing: 0.8,
  },
  pulseDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#10b981',
  },
  cloudBadge: {
    backgroundColor: 'rgba(6, 78, 59, 0.5)',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  cloudBadgeText: {
    fontSize: 9,
    fontFamily: 'monospace',
    fontWeight: '700',
    color: '#34d399',
  },
  progressRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    marginVertical: 4,
  },
  progressCircleBox: {
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: '#1e1b4b',
    borderWidth: 4,
    borderColor: '#6366f1',
    alignItems: 'center',
    justifyContent: 'center',
  },
  progressNumberText: {
    fontSize: 18,
    fontWeight: '900',
    color: '#ffffff',
    fontFamily: 'monospace',
  },
  expInfoBox: {
    flex: 1,
  },
  expTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: '#ffffff',
  },
  agentName: {
    fontSize: 11,
    color: '#94a3b8',
    marginTop: 2,
  },
  agentHours: {
    fontSize: 11,
    fontWeight: '700',
    color: '#34d399',
    fontFamily: 'monospace',
    marginTop: 4,
  },
  etaBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#090d16',
    borderRadius: 12,
    padding: 10,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  etaLabel: {
    fontSize: 11,
    color: '#cbd5e1',
    fontWeight: '600',
  },
  etaValue: {
    fontSize: 11,
    fontWeight: '800',
    color: '#fbbf24',
    fontFamily: 'monospace',
  },
  actionRow: {
    flexDirection: 'row',
    gap: 8,
  },
  compareBtn: {
    flex: 1,
    backgroundColor: '#4f46e5',
    paddingVertical: 12,
    borderRadius: 14,
    alignItems: 'center',
  },
  compareBtnText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '800',
  },
  newExpBtn: {
    backgroundColor: '#1e293b',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#334155',
    alignItems: 'center',
  },
  newExpBtnText: {
    color: '#f8fafc',
    fontSize: 12,
    fontWeight: '700',
  },
  pushCard: {
    backgroundColor: '#0f172a',
    borderRadius: 20,
    padding: 14,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  pushHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  pushTitle: {
    fontSize: 12,
    fontWeight: '800',
    color: '#ffffff',
  },
  activeTag: {
    backgroundColor: 'rgba(6, 78, 59, 0.5)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  activeTagText: {
    fontSize: 9,
    fontWeight: '800',
    color: '#34d399',
  },
  pushDesc: {
    fontSize: 11,
    color: '#94a3b8',
    lineHeight: 15,
  },
  completedSection: {
    gap: 8,
  },
  completedHeading: {
    fontSize: 11,
    fontWeight: '800',
    color: '#94a3b8',
    letterSpacing: 0.8,
  },
  completedList: {
    gap: 8,
  },
  completedCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: 'rgba(15, 23, 42, 0.9)',
    borderRadius: 18,
    padding: 12,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  completedLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
  },
  checkIconBox: {
    width: 32,
    height: 32,
    borderRadius: 10,
    backgroundColor: 'rgba(6, 78, 59, 0.6)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkIcon: {
    fontSize: 14,
    color: '#34d399',
    fontWeight: '900',
  },
  completedTitle: {
    fontSize: 12,
    fontWeight: '800',
    color: '#ffffff',
  },
  completedSub: {
    fontSize: 10,
    color: '#94a3b8',
    fontFamily: 'monospace',
    marginTop: 1,
  },
  resultsLink: {
    fontSize: 11,
    fontWeight: '800',
    color: '#818cf8',
  },
});
