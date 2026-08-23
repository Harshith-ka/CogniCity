import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { Feather, MaterialCommunityIcons } from '@expo/vector-icons';
import { useApp } from '../../context/AppContext';
import { colors, typography, layout } from '../../constants/theme';

export const InfrastructureView: React.FC = () => {
  const { projects } = useApp();

  const totalBudget = '₹193 Cr';
  const activeProjectsCount = projects.length;

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'transit': return <MaterialCommunityIcons name="train" size={16} color={colors.primaryLight} />;
      case 'energy': return <Feather name="zap" size={16} color={colors.warningLight} />;
      case 'water': return <Feather name="droplet" size={16} color={colors.cyanLight} />;
      default: return <Feather name="layers" size={16} color={colors.textSecondary} />;
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {/* Infrastructure Telemetry Hero */}
      <View style={styles.telemetryCard}>
        <View style={styles.telemetryTop}>
          <View>
            <Text style={styles.telemetryTag}>CAPITAL WORKS & MUNICIPAL ASSETS</Text>
            <Text style={styles.telemetryTitle}>Infrastructure Grid</Text>
          </View>
          <View style={styles.countBadge}>
            <Text style={styles.countText}>{activeProjectsCount} Major Projects</Text>
          </View>
        </View>

        <View style={styles.statsGrid}>
          <View style={styles.statBox}>
            <Text style={styles.statLabel}>Capital Budget</Text>
            <Text style={[styles.statVal, { color: colors.primaryLight }]}>{totalBudget}</Text>
          </View>
          <View style={styles.statBox}>
            <Text style={styles.statLabel}>Power Grid Load</Text>
            <Text style={[styles.statVal, { color: colors.successLight }]}>68.2%</Text>
          </View>
          <View style={styles.statBox}>
            <Text style={styles.statLabel}>Clean Water Index</Text>
            <Text style={[styles.statVal, { color: colors.cyanLight }]}>98.5%</Text>
          </View>
        </View>
      </View>

      {/* Projects List */}
      <View style={styles.projectsSection}>
        <Text style={styles.sectionHeading}>ACTIVE CAPITAL INFRASTRUCTURE WORKS</Text>
        {projects.map((proj) => (
          <View key={proj.id} style={styles.projectCard}>
            <View style={styles.projectHeader}>
              <View style={styles.projectTitleRow}>
                <View style={styles.iconBox}>
                  {getCategoryIcon(proj.category)}
                </View>
                <View>
                  <Text style={styles.projectTitle}>{proj.title}</Text>
                  <Text style={styles.projectDistrict}>{proj.district} • ETA: {proj.etaMonths} months</Text>
                </View>
              </View>
              <Text style={styles.progressPercent}>{proj.progressPercent}%</Text>
            </View>

            {/* Progress Bar */}
            <View style={styles.barBg}>
              <View style={[styles.barFill, { width: `${proj.progressPercent}%` }]} />
            </View>

            <Text style={styles.benefitDesc}>{proj.benefitDescription}</Text>

            <View style={styles.projectFooter}>
              <Text style={styles.budgetText}>Budget: <Text style={styles.budgetHighlight}>{proj.spentSoFar}</Text> / {proj.budgetTotal}</Text>
              <View style={styles.statusPill}>
                <Text style={styles.statusPillText}>{proj.status.toUpperCase()}</Text>
              </View>
            </View>
          </View>
        ))}
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
  telemetryCard: {
    backgroundColor: colors.surface,
    borderRadius: layout.radiusLg,
    padding: layout.cardPadding,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 12,
  },
  telemetryTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  telemetryTag: {
    ...typography.badge,
    color: colors.primaryLight,
  },
  telemetryTitle: {
    ...typography.h2,
    marginTop: 2,
  },
  countBadge: {
    backgroundColor: colors.primaryGlow,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: layout.radiusSm,
    borderWidth: 1,
    borderColor: 'rgba(99, 102, 241, 0.25)',
  },
  countText: {
    fontSize: 9,
    fontFamily: 'monospace',
    color: colors.primaryLight,
    fontWeight: '700',
  },
  statsGrid: {
    flexDirection: 'row',
    gap: 8,
  },
  statBox: {
    flex: 1,
    backgroundColor: colors.surfaceElevated,
    borderRadius: layout.radiusSm,
    padding: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  statLabel: {
    ...typography.caption,
  },
  statVal: {
    ...typography.numberMedium,
    fontSize: 13,
    marginTop: 2,
  },
  projectsSection: {
    gap: 8,
  },
  sectionHeading: {
    ...typography.badge,
    color: colors.textMuted,
  },
  projectCard: {
    backgroundColor: colors.surface,
    borderRadius: layout.radiusMd,
    padding: 12,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 8,
  },
  projectHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  projectTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
  },
  iconBox: {
    width: 32,
    height: 32,
    borderRadius: layout.radiusSm,
    backgroundColor: colors.surfaceElevated,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  projectTitle: {
    ...typography.bodyBold,
  },
  projectDistrict: {
    ...typography.caption,
    marginTop: 1,
  },
  progressPercent: {
    ...typography.numberMedium,
    fontSize: 13,
    color: colors.primaryLight,
  },
  barBg: {
    height: 4,
    backgroundColor: colors.surfaceElevated,
    borderRadius: 2,
    overflow: 'hidden',
  },
  barFill: {
    height: 4,
    backgroundColor: colors.primary,
    borderRadius: 2,
  },
  benefitDesc: {
    ...typography.body,
  },
  projectFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: 6,
  },
  budgetText: {
    ...typography.caption,
  },
  budgetHighlight: {
    color: colors.textPrimary,
    fontWeight: '700',
    fontFamily: 'monospace',
  },
  statusPill: {
    backgroundColor: colors.successGlow,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  statusPillText: {
    fontSize: 8,
    fontFamily: 'monospace',
    fontWeight: '700',
    color: colors.successLight,
  },
});
