import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useApp } from '../../context/AppContext';

export const AnalyticsView: React.FC = () => {
  const { selectedTwin } = useApp();
  const [metricTimeframe, setMetricTimeframe] = useState<'24h' | '7d' | '30d'>('7d');

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.headerRow}>
        <View>
          <Text style={styles.headerTitle}>Live Telemetry & KPIs</Text>
          <Text style={styles.headerSubtitle}>Multi-sensor real-time telemetry metrics</Text>
        </View>

        <View style={styles.timeframeBox}>
          {(['24h', '7d', '30d'] as const).map((tf) => (
            <TouchableOpacity
              key={tf}
              onPress={() => setMetricTimeframe(tf)}
              style={[styles.tfPill, metricTimeframe === tf && styles.tfPillActive]}
            >
              <Text style={[styles.tfText, metricTimeframe === tf && styles.tfTextActive]}>
                {tf}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* KPI Cards Grid */}
      <View style={styles.cardsList}>
        {/* 1. Traffic */}
        <View style={styles.kpiCard}>
          <View style={styles.cardTop}>
            <View style={styles.iconTitleRow}>
              <View style={[styles.iconBox, { backgroundColor: '#1e1b4b' }]}>
                <Text style={styles.iconEmoji}>🚗</Text>
              </View>
              <View>
                <Text style={styles.cardTitle}>Traffic Flow & Congestion Index</Text>
                <Text style={styles.cardSub}>Corridor Velocity: 44.2 km/h</Text>
              </View>
            </View>
            <Text style={styles.trendGreen}>+8.4% Flow</Text>
          </View>

          <View style={styles.cardBottom}>
            <View>
              <Text style={styles.bottomLabel}>Avg. Signal Wait</Text>
              <Text style={styles.bottomVal}>14.2 sec</Text>
            </View>
            {/* Native Mini Bar Graph representation */}
            <View style={styles.miniBarChart}>
              {[40, 55, 65, 75, 82, 90, 95].map((h, i) => (
                <View key={i} style={[styles.barColumn, { height: (h / 100) * 32, backgroundColor: '#6366f1' }]} />
              ))}
            </View>
          </View>
        </View>

        {/* 2. Healthcare */}
        <View style={styles.kpiCard}>
          <View style={styles.cardTop}>
            <View style={styles.iconTitleRow}>
              <View style={[styles.iconBox, { backgroundColor: '#4c0519' }]}>
                <Text style={styles.iconEmoji}>🏥</Text>
              </View>
              <View>
                <Text style={styles.cardTitle}>Hospital & ICU Load Factor</Text>
                <Text style={styles.cardSub}>618 / 650 Acute Beds Occupied</Text>
              </View>
            </View>
            <Text style={styles.trendAmber}>95.0% Load</Text>
          </View>

          <View style={styles.cardBottom}>
            <View>
              <Text style={styles.bottomLabel}>Triage Intake Speed</Text>
              <Text style={styles.bottomVal}>4.8 min</Text>
            </View>
            <View style={styles.miniBarChart}>
              {[50, 60, 68, 76, 85, 91, 95].map((h, i) => (
                <View key={i} style={[styles.barColumn, { height: (h / 100) * 32, backgroundColor: '#f43f5e' }]} />
              ))}
            </View>
          </View>
        </View>

        {/* 3. Economic Productivity */}
        <View style={styles.kpiCard}>
          <View style={styles.cardTop}>
            <View style={styles.iconTitleRow}>
              <View style={[styles.iconBox, { backgroundColor: '#064e3b' }]}>
                <Text style={styles.iconEmoji}>💰</Text>
              </View>
              <View>
                <Text style={styles.cardTitle}>Simulated Municipal GDP</Text>
                <Text style={styles.cardSub}>Productivity + Commercial Dispatch</Text>
              </View>
            </View>
            <Text style={styles.trendGreen}>₹4.82 Cr/day</Text>
          </View>

          <View style={styles.cardBottom}>
            <View>
              <Text style={styles.bottomLabel}>Efficiency Gain</Text>
              <Text style={styles.bottomVal}>+12.6%</Text>
            </View>
            <View style={styles.miniBarChart}>
              {[45, 50, 58, 66, 75, 84, 94].map((h, i) => (
                <View key={i} style={[styles.barColumn, { height: (h / 100) * 32, backgroundColor: '#10b981' }]} />
              ))}
            </View>
          </View>
        </View>

        {/* 4. Air Quality */}
        <View style={styles.kpiCard}>
          <View style={styles.cardTop}>
            <View style={styles.iconTitleRow}>
              <View style={[styles.iconBox, { backgroundColor: '#083344' }]}>
                <Text style={styles.iconEmoji}>🌿</Text>
              </View>
              <View>
                <Text style={styles.cardTitle}>Air Quality Index (AQI)</Text>
                <Text style={styles.cardSub}>PM2.5 & Micro-particulates</Text>
              </View>
            </View>
            <Text style={styles.trendCyan}>44 (Good)</Text>
          </View>

          <View style={styles.cardBottom}>
            <View>
              <Text style={styles.bottomLabel}>CO₂ Reduced</Text>
              <Text style={styles.bottomVal}>-18.4%</Text>
            </View>
            <View style={styles.miniBarChart}>
              {[80, 72, 65, 58, 52, 48, 44].map((h, i) => (
                <View key={i} style={[styles.barColumn, { height: (h / 100) * 32, backgroundColor: '#06b6d4' }]} />
              ))}
            </View>
          </View>
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
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#ffffff',
  },
  headerSubtitle: {
    fontSize: 11,
    color: '#94a3b8',
    marginTop: 2,
  },
  timeframeBox: {
    flexDirection: 'row',
    backgroundColor: '#0f172a',
    borderRadius: 12,
    padding: 2,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  tfPill: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  tfPillActive: {
    backgroundColor: '#4f46e5',
  },
  tfText: {
    fontSize: 10,
    fontFamily: 'monospace',
    color: '#94a3b8',
    fontWeight: '600',
  },
  tfTextActive: {
    color: '#ffffff',
    fontWeight: '800',
  },
  cardsList: {
    gap: 10,
  },
  kpiCard: {
    backgroundColor: 'rgba(15, 23, 42, 0.9)',
    borderRadius: 24,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  cardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
    paddingBottom: 10,
  },
  iconTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
  },
  iconBox: {
    width: 36,
    height: 36,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconEmoji: {
    fontSize: 18,
  },
  cardTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#ffffff',
  },
  cardSub: {
    fontSize: 10,
    color: '#94a3b8',
    marginTop: 1,
  },
  trendGreen: {
    fontSize: 12,
    fontWeight: '800',
    color: '#34d399',
    fontFamily: 'monospace',
  },
  trendAmber: {
    fontSize: 12,
    fontWeight: '800',
    color: '#fbbf24',
    fontFamily: 'monospace',
  },
  trendCyan: {
    fontSize: 12,
    fontWeight: '800',
    color: '#38bdf8',
    fontFamily: 'monospace',
  },
  cardBottom: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    marginTop: 10,
  },
  bottomLabel: {
    fontSize: 9,
    color: '#64748b',
  },
  bottomVal: {
    fontSize: 14,
    fontWeight: '900',
    color: '#ffffff',
    fontFamily: 'monospace',
    marginTop: 2,
  },
  miniBarChart: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 4,
    height: 34,
  },
  barColumn: {
    width: 8,
    borderRadius: 3,
  },
});
