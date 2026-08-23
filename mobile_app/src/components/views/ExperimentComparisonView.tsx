import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useApp } from '../../context/AppContext';

export const ExperimentComparisonView: React.FC = () => {
  const { experiments, compareExpIds, setCompareExpIds } = useApp();

  const expA = experiments.find((e) => e.id === compareExpIds[0]) || experiments[0];
  const expB = experiments.find((e) => e.id === compareExpIds[1]) || experiments[1] || experiments[0];

  const metricsRow = [
    {
      label: 'Accuracy',
      valA: `${expA.metrics?.accuracy ?? 91.0}%`,
      valB: `${expB.metrics?.accuracy ?? 94.2}%`,
      numA: expA.metrics?.accuracy ?? 91.0,
      numB: expB.metrics?.accuracy ?? 94.2,
      better: 'higher',
      icon: '🎯',
    },
    {
      label: 'Compute Cost',
      valA: `₹${expA.metrics?.costInr ?? 120}`,
      valB: `₹${expB.metrics?.costInr ?? 185}`,
      numA: expA.metrics?.costInr ?? 120,
      numB: expB.metrics?.costInr ?? 185,
      better: 'lower',
      icon: '💳',
    },
    {
      label: 'Robustness',
      valA: `${expA.metrics?.robustness ?? 78.0}%`,
      valB: `${expB.metrics?.robustness ?? 86.4}%`,
      numA: expA.metrics?.robustness ?? 78.0,
      numB: expB.metrics?.robustness ?? 86.4,
      better: 'higher',
      icon: '🛡️',
    },
    {
      label: 'Fairness',
      valA: `${expA.metrics?.fairness ?? 82.0}%`,
      valB: `${expB.metrics?.fairness ?? 79.2}%`,
      numA: expA.metrics?.fairness ?? 82.0,
      numB: expB.metrics?.fairness ?? 79.2,
      better: 'higher',
      icon: '⚖️',
    },
    {
      label: 'Inference Latency',
      valA: `${expA.metrics?.latencyMs ?? 120}ms`,
      valB: `${expB.metrics?.latencyMs ?? 210}ms`,
      numA: expA.metrics?.latencyMs ?? 120,
      numB: expB.metrics?.latencyMs ?? 210,
      better: 'lower',
      icon: '⚡',
    },
  ];

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.headerBox}>
        <View style={styles.titleRow}>
          <Text style={styles.headerTitle}>Experiment Comparison</Text>
          <Text style={styles.badgeText}>A / B MATRIX</Text>
        </View>
        <Text style={styles.headerSubtitle}>Side-by-side stress evaluation matrix</Text>
      </View>

      {/* Experiment Picker Cards */}
      <View style={styles.pickerGrid}>
        <View style={styles.pickerBox}>
          <Text style={styles.pickerLabelA}>EXPERIMENT A (CONTROL)</Text>
          <Text style={styles.pickerTitle} numberOfLines={1}>{expA.title}</Text>
          <Text style={styles.pickerEnv}>{expA.environment}</Text>
        </View>

        <View style={styles.pickerBox}>
          <Text style={styles.pickerLabelB}>EXPERIMENT B (CHALLENGER)</Text>
          <Text style={styles.pickerTitle} numberOfLines={1}>{expB.title}</Text>
          <Text style={styles.pickerEnv}>{expB.environment}</Text>
        </View>
      </View>

      {/* Comparison Matrix Table */}
      <View style={styles.tableCard}>
        <View style={styles.tableHeader}>
          <Text style={[styles.colHeader, { flex: 2 }]}>Metric</Text>
          <Text style={[styles.colHeader, styles.textCenter, { color: '#a5b4fc' }]}>Exp A</Text>
          <Text style={[styles.colHeader, styles.textCenter, { color: '#c084fc' }]}>Exp B</Text>
        </View>

        {metricsRow.map((row, idx) => {
          const aWon = row.better === 'higher' ? row.numA > row.numB : row.numA < row.numB;
          const bWon = row.better === 'higher' ? row.numB > row.numA : row.numB < row.numA;

          return (
            <View key={idx} style={styles.tableRow}>
              <View style={[styles.metricNameRow, { flex: 2 }]}>
                <Text style={styles.rowIcon}>{row.icon}</Text>
                <Text style={styles.rowLabel}>{row.label}</Text>
              </View>

              <Text style={[styles.cellVal, aWon ? styles.valGreen : styles.valMuted]}>
                {row.valA}
              </Text>

              <View style={styles.challengerCell}>
                <Text style={[styles.cellVal, bWon ? styles.valGreen : styles.valMuted]}>
                  {row.valB}
                </Text>
                {bWon && <Text style={styles.winnerBadge}>🏆</Text>}
              </View>
            </View>
          );
        })}
      </View>

      {/* Automated Verdict Card */}
      <View style={styles.verdictCard}>
        <Text style={styles.verdictTitle}>✨ Automated AI Executive Verdict</Text>
        <Text style={styles.verdictBody}>
          <Text style={{ fontWeight: '800', color: '#ffffff' }}>Experiment B</Text> outperforms Experiment A in accuracy (+3.2%) and robustness (+8.4%), but requires higher compute cost (+₹65) and has slightly higher latency.
        </Text>
        <View style={styles.verdictFooter}>
          <Text style={styles.recText}>Recommendation: <Text style={{ color: '#34d399', fontWeight: '800' }}>Deploy Model B</Text></Text>
          <Text style={styles.confScore}>96% Conf.</Text>
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
  headerBox: {
    marginBottom: 4,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#ffffff',
  },
  badgeText: {
    fontSize: 9,
    fontFamily: 'monospace',
    fontWeight: '800',
    color: '#a5b4fc',
    backgroundColor: '#1e1b4b',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  headerSubtitle: {
    fontSize: 11,
    color: '#94a3b8',
    marginTop: 2,
  },
  pickerGrid: {
    flexDirection: 'row',
    gap: 8,
  },
  pickerBox: {
    flex: 1,
    backgroundColor: 'rgba(15, 23, 42, 0.9)',
    borderRadius: 16,
    padding: 10,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  pickerLabelA: {
    fontSize: 8,
    fontFamily: 'monospace',
    fontWeight: '800',
    color: '#818cf8',
  },
  pickerLabelB: {
    fontSize: 8,
    fontFamily: 'monospace',
    fontWeight: '800',
    color: '#c084fc',
  },
  pickerTitle: {
    fontSize: 11,
    fontWeight: '800',
    color: '#ffffff',
    marginTop: 2,
  },
  pickerEnv: {
    fontSize: 9,
    color: '#94a3b8',
    marginTop: 2,
  },
  tableCard: {
    backgroundColor: 'rgba(15, 23, 42, 0.9)',
    borderRadius: 24,
    padding: 14,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  tableHeader: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
    paddingBottom: 8,
    marginBottom: 4,
  },
  colHeader: {
    fontSize: 11,
    fontWeight: '700',
    color: '#94a3b8',
    flex: 1,
  },
  textCenter: {
    textAlign: 'center',
  },
  tableRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#0f172a',
  },
  metricNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  rowIcon: {
    fontSize: 12,
  },
  rowLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: '#ffffff',
  },
  cellVal: {
    fontSize: 12,
    fontWeight: '800',
    fontFamily: 'monospace',
    flex: 1,
    textAlign: 'center',
  },
  valGreen: {
    color: '#34d399',
  },
  valMuted: {
    color: '#94a3b8',
  },
  challengerCell: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 2,
  },
  winnerBadge: {
    fontSize: 10,
  },
  verdictCard: {
    backgroundColor: '#1e1b4b',
    borderRadius: 20,
    padding: 14,
    borderWidth: 1,
    borderColor: '#4338ca',
  },
  verdictTitle: {
    fontSize: 12,
    fontWeight: '800',
    color: '#c7d2fe',
    marginBottom: 4,
  },
  verdictBody: {
    fontSize: 11,
    color: '#e0e7ff',
    lineHeight: 16,
  },
  verdictFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 10,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: 'rgba(99, 102, 241, 0.2)',
  },
  recText: {
    fontSize: 10,
    color: '#cbd5e1',
  },
  confScore: {
    fontSize: 10,
    fontFamily: 'monospace',
    color: '#818cf8',
    fontWeight: '700',
  },
});
