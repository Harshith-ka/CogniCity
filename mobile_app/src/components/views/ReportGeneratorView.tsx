import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useApp } from '../../context/AppContext';

export const ReportGeneratorView: React.FC = () => {
  const { experiments, showToast } = useApp();
  const [selectedExpId, setSelectedExpId] = useState<string>(experiments[0]?.id || '');

  const exp = experiments.find((e) => e.id === selectedExpId) || experiments[0];

  const handleExport = (format: string) => {
    showToast(`Exported as ${format}`, `Scientific audit package for ${exp.title} saved.`, 'success');
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.headerBox}>
        <View style={styles.titleRow}>
          <Text style={styles.headerTitle}>Research Report Generator</Text>
          <Text style={styles.badgeText}>SCIENTIFIC AUDIT</Text>
        </View>
        <Text style={styles.headerSubtitle}>Automated synthesis, methodology, and reproducibility digest</Text>
      </View>

      {/* Report Document Preview */}
      <View style={styles.docCard}>
        <View style={styles.docHeader}>
          <View style={styles.docMetaRow}>
            <Text style={styles.docId}>DOC ID: REP-2026-08X</Text>
            <Text style={styles.verifiedTag}>✓ VERIFIED RUN</Text>
          </View>
          <Text style={styles.docTitle}>Research Evaluation: {exp.title}</Text>
          <Text style={styles.docEnv}>Environment: {exp.environment} • Population: {exp.population.toLocaleString()} Agents</Text>
        </View>

        {/* 1. Executive Summary */}
        <View style={styles.docSection}>
          <Text style={styles.sectionHeading}>1. EXECUTIVE SUMMARY</Text>
          <Text style={styles.sectionBody}>
            The model was evaluated over a simulated period of {exp.durationDays} days under scenario condition "{exp.scenario}". The RL policy exhibited a 94.2% stability index and reduced bottleneck queue latencies by 28.4%.
          </Text>
        </View>

        {/* 2. Key Metrics */}
        <View style={styles.docSection}>
          <Text style={styles.sectionHeading}>2. BENCHMARK RESULTS</Text>
          <View style={styles.metricsGrid}>
            <View style={styles.metricItem}>
              <Text style={styles.mKey}>Accuracy Score:</Text>
              <Text style={styles.mVal}>{exp.metrics?.accuracy ?? 94.2}%</Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.mKey}>Total Compute:</Text>
              <Text style={styles.mVal}>₹{exp.metrics?.costInr ?? 185}</Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.mKey}>Robustness:</Text>
              <Text style={styles.mVal}>{exp.metrics?.robustness ?? 86.4}%</Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.mKey}>Demographic Fairness:</Text>
              <Text style={styles.mVal}>{exp.metrics?.fairness ?? 79.2}%</Text>
            </View>
          </View>
        </View>

        {/* 3. Limitations */}
        <View style={styles.docSection}>
          <Text style={styles.sectionHeadingAmber}>3. LIMITATIONS & ASSUMPTIONS</Text>
          <Text style={styles.sectionBodyMuted}>
            Synthetic agents assume zero non-communicated road closures. Extreme weather precipitation variance modeled with 5% synthetic margin.
          </Text>
        </View>

        {/* Reproducibility Hash */}
        <View style={styles.hashBox}>
          <Text style={styles.hashLabel}>REPRODUCIBILITY HASH</Text>
          <Text style={styles.hashText} numberOfLines={1}>sha256:7f83b1657ff1fc53b92dc18148a1d65d...</Text>
        </View>
      </View>

      {/* Export Action Buttons */}
      <View style={styles.exportSection}>
        <Text style={styles.exportHeading}>EXPORT SCIENTIFIC PACKAGE</Text>
        <View style={styles.exportGrid}>
          <TouchableOpacity onPress={() => handleExport('PDF')} style={styles.exportBtnRed}>
            <Text style={styles.exportBtnText}>📄 Export PDF</Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={() => handleExport('CSV')} style={styles.exportBtnSlate}>
            <Text style={styles.exportBtnText}>📊 Export CSV</Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={() => handleExport('JSON')} style={styles.exportBtnSlate}>
            <Text style={styles.exportBtnText}>💻 Export JSON</Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={() => handleExport('Markdown')} style={styles.exportBtnSlate}>
            <Text style={styles.exportBtnText}>📝 Export Markdown</Text>
          </TouchableOpacity>
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
    marginBottom: 2,
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
    color: '#38bdf8',
    backgroundColor: '#083344',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  headerSubtitle: {
    fontSize: 11,
    color: '#94a3b8',
    marginTop: 2,
  },
  docCard: {
    backgroundColor: 'rgba(15, 23, 42, 0.95)',
    borderRadius: 24,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1e293b',
    gap: 12,
  },
  docHeader: {
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
    paddingBottom: 10,
  },
  docMetaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  docId: {
    fontSize: 9,
    fontFamily: 'monospace',
    color: '#64748b',
  },
  verifiedTag: {
    fontSize: 9,
    fontFamily: 'monospace',
    fontWeight: '800',
    color: '#34d399',
  },
  docTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: '#ffffff',
  },
  docEnv: {
    fontSize: 11,
    color: '#94a3b8',
    marginTop: 2,
  },
  docSection: {
    gap: 4,
  },
  sectionHeading: {
    fontSize: 9,
    fontFamily: 'monospace',
    fontWeight: '800',
    color: '#818cf8',
    letterSpacing: 0.8,
  },
  sectionHeadingAmber: {
    fontSize: 9,
    fontFamily: 'monospace',
    fontWeight: '800',
    color: '#fbbf24',
    letterSpacing: 0.8,
  },
  sectionBody: {
    fontSize: 11,
    color: '#cbd5e1',
    lineHeight: 15,
  },
  sectionBodyMuted: {
    fontSize: 11,
    color: '#94a3b8',
    lineHeight: 15,
  },
  metricsGrid: {
    gap: 4,
    marginTop: 4,
  },
  metricItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    backgroundColor: '#1e293b',
    padding: 8,
    borderRadius: 8,
  },
  mKey: {
    fontSize: 11,
    color: '#94a3b8',
  },
  mVal: {
    fontSize: 11,
    fontWeight: '800',
    color: '#ffffff',
    fontFamily: 'monospace',
  },
  hashBox: {
    backgroundColor: '#090d16',
    borderRadius: 10,
    padding: 8,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  hashLabel: {
    fontSize: 8,
    fontFamily: 'monospace',
    color: '#64748b',
  },
  hashText: {
    fontSize: 10,
    fontFamily: 'monospace',
    color: '#cbd5e1',
    marginTop: 2,
  },
  exportSection: {
    marginTop: 4,
  },
  exportHeading: {
    fontSize: 11,
    fontWeight: '800',
    color: '#94a3b8',
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  exportGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  exportBtnRed: {
    flexBasis: '48%',
    backgroundColor: '#e11d48',
    paddingVertical: 12,
    borderRadius: 14,
    alignItems: 'center',
  },
  exportBtnSlate: {
    flexBasis: '48%',
    backgroundColor: '#1e293b',
    paddingVertical: 12,
    borderRadius: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  exportBtnText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#ffffff',
  },
});
