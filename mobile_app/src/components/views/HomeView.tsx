import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { Ionicons, Feather, MaterialCommunityIcons } from '@expo/vector-icons';
import { useApp } from '../../context/AppContext';
import { DigitalTwin } from '../../types';
import { colors, typography, layout } from '../../constants/theme';

export const HomeView: React.FC = () => {
  const {
    twins,
    setSelectedTwin,
    setActiveTab,
    toggleTwinStatus,
    simTime,
    toggleSimulationPlay,
    setSpeedMultiplier,
    setIsCreateExpOpen,
  } = useApp();

  const totalAgents = twins.reduce((acc, curr) => acc + curr.agentCount, 0);
  const activeSimsCount = twins.filter((t) => t.status === 'running').length;
  const runningExperiments = 2;
  const avgHealth = Math.round(twins.reduce((acc, curr) => acc + curr.healthScore, 0) / twins.length);

  const handleOpenSimulation = (twin: DigitalTwin) => {
    setSelectedTwin(twin);
    setActiveTab('live_map');
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'smart_city': return <MaterialCommunityIcons name="city-variant-outline" size={18} color={colors.primaryLight} />;
      case 'healthcare': return <Ionicons name="medical-outline" size={18} color={colors.dangerLight} />;
      case 'aviation': return <Ionicons name="airplane-outline" size={18} color={colors.cyanLight} />;
      case 'industrial': return <MaterialCommunityIcons name="factory" size={18} color={colors.warningLight} />;
      case 'education': return <Ionicons name="school-outline" size={18} color={colors.purpleLight} />;
      case 'energy': return <Feather name="zap" size={18} color={colors.warningLight} />;
      default: return <Feather name="globe" size={18} color={colors.primaryLight} />;
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {/* Hero Telemetry Card */}
      <View style={styles.heroCard}>
        <View style={styles.heroTopRow}>
          <View>
            <Text style={styles.heroTag}>SYSTEM OVERVIEW</Text>
            <Text style={styles.heroTitle}>Autonomous Twins</Text>
          </View>
          <View style={styles.healthBadge}>
            <Text style={styles.healthBadgeVal}>{avgHealth}%</Text>
            <Text style={styles.healthBadgeLabel}>HEALTH</Text>
          </View>
        </View>

        {/* 4 Stats Grid */}
        <View style={styles.statsGrid}>
          <View style={styles.statBox}>
            <View style={styles.statIconRow}>
              <Feather name="users" size={13} color={colors.primaryLight} />
              <Text style={styles.statLabel}>Agents</Text>
            </View>
            <Text style={styles.statNumber}>{totalAgents.toLocaleString()}</Text>
          </View>

          <View style={styles.statBox}>
            <View style={styles.statIconRow}>
              <Feather name="globe" size={13} color={colors.cyanLight} />
              <Text style={styles.statLabel}>Environments</Text>
            </View>
            <Text style={styles.statNumber}>{twins.length}</Text>
          </View>

          <View style={styles.statBox}>
            <View style={styles.statIconRow}>
              <Feather name="activity" size={13} color={colors.warningLight} />
              <Text style={styles.statLabel}>Simulations</Text>
            </View>
            <Text style={styles.statNumber}>{activeSimsCount}</Text>
          </View>

          <View style={styles.statBox}>
            <View style={styles.statIconRow}>
              <Feather name="zap" size={13} color={colors.successLight} />
              <Text style={styles.statLabel}>Experiments</Text>
            </View>
            <Text style={styles.statNumber}>{runningExperiments}</Text>
          </View>
        </View>
      </View>

      {/* Global Playback Quick Controls */}
      <View style={styles.controlsBar}>
        <View style={styles.timeInfo}>
          <Text style={styles.timeLabel}>VIRTUAL TIME</Text>
          <Text style={styles.timeClock}>
            Day {simTime.day} • {String(simTime.hour).padStart(2, '0')}:{String(simTime.minute).padStart(2, '0')}
          </Text>
        </View>

        <View style={styles.btnRow}>
          <TouchableOpacity
            onPress={toggleSimulationPlay}
            style={[styles.playBtn, simTime.isRunning ? styles.playBtnPause : styles.playBtnRun]}
            activeOpacity={0.7}
          >
            <Ionicons
              name={simTime.isRunning ? 'pause' : 'play'}
              size={13}
              color={simTime.isRunning ? colors.warningLight : colors.successLight}
            />
            <Text style={[styles.playBtnText, simTime.isRunning ? styles.textAmber : styles.textGreen]}>
              {simTime.isRunning ? 'PAUSE' : 'RUN'}
            </Text>
          </TouchableOpacity>

          <View style={styles.speedRow}>
            {[1, 10, 100].map((s) => (
              <TouchableOpacity
                key={s}
                onPress={() => setSpeedMultiplier(s)}
                style={[styles.speedBtn, simTime.speedMultiplier === s && styles.speedBtnActive]}
                activeOpacity={0.7}
              >
                <Text style={[styles.speedText, simTime.speedMultiplier === s && styles.speedTextActive]}>
                  {s}x
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </View>

      {/* Live Environments Section */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>ACTIVE DIGITAL TWINS</Text>
          <TouchableOpacity onPress={() => setActiveTab('twins')} activeOpacity={0.7}>
            <Text style={styles.seeAllText}>View All ➔</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.twinsList}>
          {twins.map((twin) => {
            const isRunning = twin.status === 'running';
            return (
              <TouchableOpacity
                key={twin.id}
                onPress={() => handleOpenSimulation(twin)}
                style={styles.twinCard}
                activeOpacity={0.7}
              >
                <View style={styles.twinTop}>
                  <View style={styles.twinTitleRow}>
                    <View style={styles.twinIconBox}>
                      {getCategoryIcon(twin.category)}
                    </View>
                    <View>
                      <Text style={styles.twinName}>{twin.name}</Text>
                      <Text style={styles.twinAgents}>{twin.agentCount.toLocaleString()} synthetic agents</Text>
                    </View>
                  </View>

                  <View style={styles.statusWrap}>
                    <View style={[styles.statusPill, isRunning ? styles.pillActive : styles.pillPaused]}>
                      <View style={[styles.statusDot, isRunning ? styles.dotGreen : styles.dotAmber]} />
                      <Text style={[styles.statusText, isRunning ? styles.textGreen : styles.textAmber]}>
                        {isRunning ? 'RUNNING' : 'PAUSED'}
                      </Text>
                    </View>
                  </View>
                </View>

                {/* Micro Metric Preview */}
                <View style={styles.metricRow}>
                  <View style={styles.metricItem}>
                    <Text style={styles.metricLabel}>Health Index</Text>
                    <Text style={styles.metricVal}>{twin.healthScore}%</Text>
                  </View>
                  <View style={styles.metricItem}>
                    <Text style={styles.metricLabel}>Scenario</Text>
                    <Text style={styles.metricVal} numberOfLines={1}>{twin.activeScenario || 'Baseline Standard'}</Text>
                  </View>

                  <TouchableOpacity
                    onPress={() => toggleTwinStatus(twin.id)}
                    style={styles.twinToggleBtn}
                    activeOpacity={0.7}
                  >
                    <Feather name={isRunning ? 'pause' : 'play'} size={12} color={colors.textSecondary} />
                  </TouchableOpacity>
                </View>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {/* Quick Experiment Launcher Action */}
      <View style={styles.bannerAction}>
        <View style={styles.bannerLeft}>
          <Text style={styles.bannerTitle}>Simulate Cloud Scenarios</Text>
          <Text style={styles.bannerSub}>Stress test policies with up to 50k citizens</Text>
        </View>
        <TouchableOpacity
          onPress={() => setIsCreateExpOpen(true)}
          style={styles.bannerBtn}
          activeOpacity={0.7}
        >
          <Feather name="plus" size={13} color="#ffffff" style={{ marginRight: 4 }} />
          <Text style={styles.bannerBtnText}>Launch</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  contentContainer: {
    padding: layout.padding,
    paddingBottom: 30,
    gap: 12,
  },
  heroCard: {
    backgroundColor: colors.surface,
    borderRadius: layout.radiusLg,
    padding: layout.cardPadding,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 12,
  },
  heroTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  heroTag: {
    ...typography.badge,
    color: colors.primaryLight,
  },
  heroTitle: {
    ...typography.h1,
    marginTop: 2,
  },
  healthBadge: {
    backgroundColor: colors.successGlow,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: layout.radiusSm,
    borderWidth: 1,
    borderColor: 'rgba(16, 185, 129, 0.25)',
    alignItems: 'center',
  },
  healthBadgeVal: {
    ...typography.numberMedium,
    color: colors.successLight,
  },
  healthBadgeLabel: {
    fontSize: 7.5,
    fontFamily: 'monospace',
    fontWeight: '700',
    color: colors.successLight,
    letterSpacing: 0.5,
  },
  statsGrid: {
    flexDirection: 'row',
    gap: 8,
  },
  statBox: {
    flex: 1,
    backgroundColor: colors.surfaceElevated,
    borderRadius: layout.radiusMd,
    padding: 10,
    borderWidth: 1,
    borderColor: colors.border,
  },
  statIconRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statLabel: {
    ...typography.caption,
  },
  statNumber: {
    ...typography.numberMedium,
    marginTop: 4,
  },
  controlsBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: colors.surface,
    padding: 12,
    borderRadius: layout.radiusMd,
    borderWidth: 1,
    borderColor: colors.border,
  },
  timeInfo: {
    gap: 2,
  },
  timeLabel: {
    ...typography.badge,
    color: colors.textMuted,
  },
  timeClock: {
    fontSize: 12,
    fontWeight: '700',
    fontFamily: 'monospace',
    color: colors.textPrimary,
  },
  btnRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  playBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: layout.radiusSm,
    gap: 4,
    borderWidth: 1,
  },
  playBtnRun: {
    backgroundColor: colors.successGlow,
    borderColor: 'rgba(16, 185, 129, 0.3)',
  },
  playBtnPause: {
    backgroundColor: colors.warningGlow,
    borderColor: 'rgba(245, 158, 11, 0.3)',
  },
  playBtnText: {
    fontSize: 10,
    fontWeight: '800',
    fontFamily: 'monospace',
  },
  speedRow: {
    flexDirection: 'row',
    backgroundColor: colors.surfaceElevated,
    borderRadius: layout.radiusSm,
    padding: 2,
    gap: 2,
    borderWidth: 1,
    borderColor: colors.border,
  },
  speedBtn: {
    paddingHorizontal: 7,
    paddingVertical: 4,
    borderRadius: 6,
  },
  speedBtnActive: {
    backgroundColor: colors.primary,
  },
  speedText: {
    fontSize: 10,
    fontWeight: '700',
    fontFamily: 'monospace',
    color: colors.textMuted,
  },
  speedTextActive: {
    color: '#ffffff',
  },
  section: {
    gap: 8,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionTitle: {
    ...typography.badge,
    color: colors.textMuted,
  },
  seeAllText: {
    fontSize: 11,
    color: colors.primaryLight,
    fontWeight: '600',
  },
  twinsList: {
    gap: 8,
  },
  twinCard: {
    backgroundColor: colors.surface,
    borderRadius: layout.radiusMd,
    padding: 12,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 8,
  },
  twinTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  twinTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
  },
  twinIconBox: {
    width: 36,
    height: 36,
    borderRadius: layout.radiusSm,
    backgroundColor: colors.surfaceElevated,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  twinName: {
    ...typography.bodyBold,
  },
  twinAgents: {
    ...typography.caption,
    marginTop: 1,
  },
  statusWrap: {
    alignItems: 'flex-end',
  },
  statusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 6,
    paddingVertical: 3,
    borderRadius: 6,
    gap: 4,
    borderWidth: 1,
  },
  pillActive: {
    backgroundColor: colors.successGlow,
    borderColor: 'rgba(16, 185, 129, 0.3)',
  },
  pillPaused: {
    backgroundColor: colors.warningGlow,
    borderColor: 'rgba(245, 158, 11, 0.3)',
  },
  statusDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
  },
  dotGreen: {
    backgroundColor: colors.success,
  },
  dotAmber: {
    backgroundColor: colors.warning,
  },
  statusText: {
    fontSize: 8.5,
    fontFamily: 'monospace',
    fontWeight: '700',
  },
  textGreen: {
    color: colors.successLight,
  },
  textAmber: {
    color: colors.warningLight,
  },
  metricRow: {
    flexDirection: 'row',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: 8,
    gap: 12,
  },
  metricItem: {
    flex: 1,
  },
  metricLabel: {
    fontSize: 8.5,
    color: colors.textMuted,
    textTransform: 'uppercase',
  },
  metricVal: {
    fontSize: 11,
    color: colors.textSecondary,
    fontWeight: '600',
    marginTop: 1,
  },
  twinToggleBtn: {
    backgroundColor: colors.surfaceElevated,
    padding: 6,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: colors.border,
  },
  bannerAction: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: colors.primaryGlow,
    borderRadius: layout.radiusMd,
    padding: 14,
    borderWidth: 1,
    borderColor: 'rgba(99, 102, 241, 0.3)',
  },
  bannerLeft: {
    flex: 1,
  },
  bannerTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  bannerSub: {
    fontSize: 10,
    color: colors.textSecondary,
    marginTop: 2,
  },
  bannerBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primary,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: layout.radiusSm,
  },
  bannerBtnText: {
    color: '#ffffff',
    fontSize: 11,
    fontWeight: '700',
  },
});
