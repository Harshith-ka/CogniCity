import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useApp } from '../../context/AppContext';
import { colors, typography, layout } from '../../constants/theme';

export const ElectionsView: React.FC = () => {
  const { elections, castVote } = useApp();

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {/* Election Header Card */}
      <View style={styles.electionCard}>
        <View style={styles.topRow}>
          <View style={styles.tagRow}>
            <Text style={styles.tagText}>DEMOCRATIC SIMULATION ENGINE</Text>
            <View style={styles.pulseDot} />
          </View>
          <View style={styles.daysBox}>
            <Text style={styles.daysText}>{elections.daysUntilElection} Days to Polls</Text>
          </View>
        </View>

        <Text style={styles.raceTitle}>{elections.title}</Text>
        <Text style={styles.raceSub}>
          Projected Civic Turnout: <Text style={styles.highlightText}>{elections.projectedTurnoutPercent}% of 10,000 citizens</Text>
        </Text>
      </View>

      {/* Candidates Polling Section */}
      <View style={styles.candidatesSection}>
        <Text style={styles.sectionHeading}>MAYORAL CANDIDATES & PROJECTED POLLING</Text>
        {elections.candidates.map((cand) => (
          <View key={cand.id} style={styles.candCard}>
            <View style={styles.candTop}>
              <View style={styles.candProfile}>
                <View style={styles.avatarBox}>
                  <Feather name="user" size={16} color={colors.textSecondary} />
                </View>
                <View>
                  <Text style={styles.candName}>{cand.name}</Text>
                  <Text style={styles.candParty}>{cand.party}</Text>
                </View>
              </View>

              <View style={styles.pollingBox}>
                <Text style={styles.pollingVal}>{cand.pollingPercent}%</Text>
                <Text style={styles.pollingLabel}>Polling</Text>
              </View>
            </View>

            {/* Polling bar */}
            <View style={styles.barBg}>
              <View style={[styles.barFill, { width: `${cand.pollingPercent}%` }]} />
            </View>

            <Text style={styles.platformText}>{cand.platformSummary}</Text>

            <View style={styles.candFooter}>
              <Text style={styles.stanceText}>Key Stance: <Text style={styles.stanceHighlight}>{cand.keyStance}</Text></Text>
              <TouchableOpacity onPress={() => castVote(cand.id)} style={styles.voteBtn} activeOpacity={0.7}>
                <Feather name="check" size={12} color="#ffffff" style={{ marginRight: 4 }} />
                <Text style={styles.voteBtnText}>Cast Ballot</Text>
              </TouchableOpacity>
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
  electionCard: {
    backgroundColor: colors.surface,
    borderRadius: layout.radiusLg,
    padding: layout.cardPadding,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 6,
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  tagRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  tagText: {
    ...typography.badge,
    color: colors.primaryLight,
  },
  pulseDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.success,
  },
  daysBox: {
    backgroundColor: colors.primaryGlow,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: layout.radiusSm,
    borderWidth: 1,
    borderColor: 'rgba(99, 102, 241, 0.25)',
  },
  daysText: {
    fontSize: 9,
    fontFamily: 'monospace',
    fontWeight: '700',
    color: colors.primaryLight,
  },
  raceTitle: {
    ...typography.h2,
    marginTop: 2,
  },
  raceSub: {
    ...typography.body,
  },
  highlightText: {
    color: colors.successLight,
    fontWeight: '700',
  },
  candidatesSection: {
    gap: 8,
  },
  sectionHeading: {
    ...typography.badge,
    color: colors.textMuted,
  },
  candCard: {
    backgroundColor: colors.surface,
    borderRadius: layout.radiusMd,
    padding: 12,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 8,
  },
  candTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  candProfile: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
  },
  avatarBox: {
    width: 32,
    height: 32,
    borderRadius: layout.radiusSm,
    backgroundColor: colors.surfaceElevated,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  candName: {
    ...typography.bodyBold,
  },
  candParty: {
    ...typography.caption,
    marginTop: 1,
  },
  pollingBox: {
    alignItems: 'flex-end',
  },
  pollingVal: {
    ...typography.numberMedium,
    color: colors.primaryLight,
  },
  pollingLabel: {
    ...typography.caption,
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
  platformText: {
    ...typography.body,
  },
  candFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: 6,
  },
  stanceText: {
    ...typography.caption,
    flex: 1,
  },
  stanceHighlight: {
    color: colors.textPrimary,
    fontWeight: '600',
  },
  voteBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primary,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: layout.radiusSm,
  },
  voteBtnText: {
    color: '#ffffff',
    fontSize: 10.5,
    fontWeight: '700',
  },
});
