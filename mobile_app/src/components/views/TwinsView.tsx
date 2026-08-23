import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { Ionicons, Feather, MaterialCommunityIcons } from '@expo/vector-icons';
import { useApp } from '../../context/AppContext';
import { DigitalTwin } from '../../types';
import { colors, typography, layout } from '../../constants/theme';

export const TwinsView: React.FC = () => {
  const { twins, selectedTwin, setSelectedTwin, setActiveTab, toggleTwinStatus } = useApp();

  const handleSelect = (twin: DigitalTwin) => {
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
      <View style={styles.headerInfo}>
        <Text style={styles.headerTitle}>Active Digital Twins</Text>
        <Text style={styles.headerSub}>Enterprise multi-agent synthetic environments</Text>
      </View>

      <View style={styles.twinsGrid}>
        {twins.map((twin) => {
          const isSelected = selectedTwin.id === twin.id;
          const isRunning = twin.status === 'running';

          return (
            <TouchableOpacity
              key={twin.id}
              onPress={() => handleSelect(twin)}
              style={[styles.twinCard, isSelected && styles.twinCardSelected]}
              activeOpacity={0.7}
            >
              <View style={styles.cardHeader}>
                <View style={styles.iconBox}>
                  {getCategoryIcon(twin.category)}
                </View>

                <View style={styles.headerRight}>
                  <View style={[styles.statusBadge, isRunning ? styles.bgActive : styles.bgPaused]}>
                    <View style={[styles.dot, isRunning ? styles.dotGreen : styles.dotAmber]} />
                    <Text style={[styles.statusText, isRunning ? styles.textGreen : styles.textAmber]}>
                      {isRunning ? 'ACTIVE' : 'PAUSED'}
                    </Text>
                  </View>
                </View>
              </View>

              <Text style={styles.twinName}>{twin.name}</Text>
              <Text style={styles.twinDesc}>{twin.description}</Text>

              {/* Specs row */}
              <View style={styles.specsRow}>
                <View style={styles.specItem}>
                  <Text style={styles.specLabel}>AGENTS</Text>
                  <Text style={styles.specVal}>{twin.agentCount.toLocaleString()}</Text>
                </View>

                <View style={styles.specItem}>
                  <Text style={styles.specLabel}>HEALTH</Text>
                  <Text style={[styles.specVal, { color: colors.successLight }]}>{twin.healthScore}%</Text>
                </View>

                <View style={styles.specItem}>
                  <Text style={styles.specLabel}>AREA</Text>
                  <Text style={styles.specVal}>{twin.environmentSize}</Text>
                </View>
              </View>

              {/* Actions Footer */}
              <View style={styles.cardFooter}>
                <TouchableOpacity
                  onPress={() => toggleTwinStatus(twin.id)}
                  style={styles.toggleBtn}
                  activeOpacity={0.7}
                >
                  <Feather name={isRunning ? 'pause' : 'play'} size={12} color={colors.textSecondary} style={{ marginRight: 4 }} />
                  <Text style={styles.toggleText}>{isRunning ? 'Pause' : 'Resume'}</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  onPress={() => handleSelect(twin)}
                  style={styles.openBtn}
                  activeOpacity={0.7}
                >
                  <Text style={styles.openBtnText}>Launch Map ➔</Text>
                </TouchableOpacity>
              </View>
            </TouchableOpacity>
          );
        })}
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
  headerInfo: {
    marginBottom: 4,
  },
  headerTitle: {
    ...typography.h2,
  },
  headerSub: {
    ...typography.caption,
    marginTop: 2,
  },
  twinsGrid: {
    gap: 10,
  },
  twinCard: {
    backgroundColor: colors.surface,
    borderRadius: layout.radiusLg,
    padding: layout.cardPadding,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 10,
  },
  twinCardSelected: {
    borderColor: colors.primary,
    backgroundColor: colors.surfaceElevated,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  iconBox: {
    width: 36,
    height: 36,
    borderRadius: layout.radiusSm,
    backgroundColor: colors.surfaceElevated,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  headerRight: {
    alignItems: 'flex-end',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 7,
    paddingVertical: 3,
    borderRadius: 6,
    gap: 4,
    borderWidth: 1,
  },
  bgActive: {
    backgroundColor: colors.successGlow,
    borderColor: 'rgba(16, 185, 129, 0.3)',
  },
  bgPaused: {
    backgroundColor: colors.warningGlow,
    borderColor: 'rgba(245, 158, 11, 0.3)',
  },
  dot: {
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
  twinName: {
    ...typography.h2,
  },
  twinDesc: {
    ...typography.body,
  },
  specsRow: {
    flexDirection: 'row',
    backgroundColor: colors.surfaceElevated,
    borderRadius: layout.radiusSm,
    padding: 8,
    borderWidth: 1,
    borderColor: colors.border,
    justifyContent: 'space-around',
  },
  specItem: {
    alignItems: 'center',
  },
  specLabel: {
    fontSize: 8,
    fontFamily: 'monospace',
    color: colors.textMuted,
    letterSpacing: 0.5,
  },
  specVal: {
    ...typography.numberMedium,
    fontSize: 12,
    marginTop: 2,
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: 8,
    gap: 8,
  },
  toggleBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceElevated,
    paddingHorizontal: 10,
    paddingVertical: 7,
    borderRadius: layout.radiusSm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  toggleText: {
    fontSize: 10.5,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  openBtn: {
    flex: 1,
    backgroundColor: colors.primary,
    paddingVertical: 7,
    borderRadius: layout.radiusSm,
    alignItems: 'center',
  },
  openBtnText: {
    color: '#ffffff',
    fontSize: 11,
    fontWeight: '700',
  },
});
