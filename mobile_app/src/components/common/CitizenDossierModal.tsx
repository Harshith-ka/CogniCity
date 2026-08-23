import React from 'react';
import { View, Text, StyleSheet, Modal, TouchableOpacity, ScrollView } from 'react-native';
import { Feather, Ionicons } from '@expo/vector-icons';
import { useApp } from '../../context/AppContext';
import { colors, typography, layout } from '../../constants/theme';

export const CitizenDossierModal: React.FC = () => {
  const { 
    selectedCitizen, 
    setSelectedCitizen, 
    setInspectReasoningId, 
    setActiveTab, 
    showToast 
  } = useApp();

  if (!selectedCitizen) return null;

  const handleInspectReasoning = () => {
    setSelectedCitizen(null);
    setInspectReasoningId('citizen_4821');
    setActiveTab('reasoning');
    showToast('Cognitive Trace', `Inspecting reasoning steps for ${selectedCitizen.name}`, 'info');
  };

  return (
    <Modal
      visible={!!selectedCitizen}
      animationType="slide"
      transparent={true}
      onRequestClose={() => setSelectedCitizen(null)}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.sheetContainer}>
          {/* Header Profile */}
          <View style={styles.profileHeader}>
            <View style={styles.avatarRow}>
              <View style={styles.avatarBox}>
                <Feather name="user" size={24} color={colors.primaryLight} />
              </View>
              <View style={styles.titleInfo}>
                <View style={styles.nameRow}>
                  <Text style={styles.citizenName}>{selectedCitizen.name}</Text>
                  <Text style={styles.ageBadge}>{selectedCitizen.age} yrs</Text>
                </View>
                <Text style={styles.occupationText}>{selectedCitizen.occupation}</Text>
                <Text style={styles.citizenId}>ID: #{selectedCitizen.id.replace('cit_', '')}</Text>
              </View>
            </View>
            <TouchableOpacity onPress={() => setSelectedCitizen(null)} style={styles.closeBtn} activeOpacity={0.7}>
              <Feather name="x" size={16} color={colors.textSecondary} />
            </TouchableOpacity>
          </View>

          {/* Body Content */}
          <ScrollView style={styles.scrollBody} showsVerticalScrollIndicator={false}>
            {/* Live Activity Box */}
            <View style={styles.activityBox}>
              <View style={styles.activityHeader}>
                <Text style={styles.activityLabel}>CURRENT ACTIVITY</Text>
                <Text style={styles.liveTag}>LIVE STATE</Text>
              </View>
              <Text style={styles.activityAction}>{selectedCitizen.lastAction}</Text>
              <View style={styles.activityFooter}>
                <Text style={styles.locationText}>{selectedCitizen.location}</Text>
                <Text style={styles.moodText}>Intent: {selectedCitizen.currentIntent}</Text>
              </View>
            </View>

            {/* Income & Location Grid */}
            <View style={styles.statsGrid}>
              <View style={styles.statCard}>
                <Text style={styles.statLabel}>INCOME LEVEL</Text>
                <Text style={styles.incomeValue}>{selectedCitizen.income}</Text>
                <Text style={styles.statSub}>Net Worth: {selectedCitizen.netWorth}</Text>
              </View>

              <View style={styles.statCard}>
                <Text style={styles.statLabel}>EDUCATION & LOCATION</Text>
                <Text style={styles.statValue} numberOfLines={1}>{selectedCitizen.education}</Text>
                <Text style={styles.statSub} numberOfLines={1}>{selectedCitizen.location}</Text>
              </View>
            </View>

            {/* Biometrics */}
            <View style={styles.biometricsCard}>
              <View style={styles.sectionHeaderRow}>
                <Text style={styles.sectionTitle}>Biometrics & Health</Text>
                <Text style={styles.riskBadge}>Risk: {selectedCitizen.health.healthRiskScore}%</Text>
              </View>

              <View style={styles.bioGrid}>
                <View style={styles.bioBox}>
                  <Text style={styles.bioLabel}>BMI</Text>
                  <Text style={styles.bioValue}>{selectedCitizen.health.bmi}</Text>
                </View>
                <View style={styles.bioBox}>
                  <Text style={styles.bioLabel}>Blood Pressure</Text>
                  <Text style={styles.bioValue}>{selectedCitizen.health.bp}</Text>
                </View>
                <View style={styles.bioBox}>
                  <Text style={styles.bioLabel}>Resting HR</Text>
                  <Text style={[styles.bioValue, { color: colors.dangerLight }]}>{selectedCitizen.health.heartRate} bpm</Text>
                </View>
              </View>
            </View>

            {/* Lifestyle */}
            <View style={styles.lifestyleCard}>
              <Text style={styles.sectionTitle}>Lifestyle Indicators</Text>
              <View style={styles.lifestyleGrid}>
                <View style={styles.lifestyleRow}>
                  <Text style={styles.lifestyleKey}>Exercise:</Text>
                  <Text style={styles.lifestyleVal}>{selectedCitizen.health.physicalActivityMin} mins/day</Text>
                </View>
                <View style={styles.lifestyleRow}>
                  <Text style={styles.lifestyleKey}>Stress:</Text>
                  <Text style={[styles.lifestyleVal, selectedCitizen.health.stressLevel === 'High' && { color: colors.dangerLight }]}>
                    {selectedCitizen.health.stressLevel}
                  </Text>
                </View>
                <View style={styles.lifestyleRow}>
                  <Text style={styles.lifestyleKey}>Sleep:</Text>
                  <Text style={styles.lifestyleVal}>{selectedCitizen.lifestyle.sleepHours} hrs/night</Text>
                </View>
                <View style={styles.lifestyleRow}>
                  <Text style={styles.lifestyleKey}>Diet:</Text>
                  <Text style={styles.lifestyleVal} numberOfLines={1}>{selectedCitizen.lifestyle.diet}</Text>
                </View>
              </View>
            </View>
          </ScrollView>

          {/* Action Footer */}
          <View style={styles.actionFooter}>
            <TouchableOpacity onPress={handleInspectReasoning} style={styles.primaryActionBtn} activeOpacity={0.7}>
              <Feather name="git-commit" size={14} color="#ffffff" style={{ marginRight: 6 }} />
              <Text style={styles.primaryActionText}>Inspect Cognitive Trace</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(5, 8, 15, 0.85)',
    justifyContent: 'flex-end',
  },
  sheetContainer: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: layout.cardPadding,
    maxHeight: '85%',
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  profileHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    paddingBottom: 12,
  },
  avatarRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  avatarBox: {
    width: 44,
    height: 44,
    borderRadius: layout.radiusMd,
    backgroundColor: colors.primaryGlow,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(99, 102, 241, 0.25)',
  },
  titleInfo: {
    flex: 1,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  citizenName: {
    ...typography.h2,
  },
  ageBadge: {
    backgroundColor: colors.surfaceElevated,
    color: colors.textSecondary,
    fontSize: 9,
    fontWeight: '700',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    fontFamily: 'monospace',
  },
  occupationText: {
    ...typography.caption,
    marginTop: 2,
  },
  citizenId: {
    fontSize: 8.5,
    fontFamily: 'monospace',
    color: colors.textMuted,
    marginTop: 2,
  },
  closeBtn: {
    backgroundColor: colors.surfaceElevated,
    width: 28,
    height: 28,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  scrollBody: {
    paddingVertical: 10,
  },
  activityBox: {
    backgroundColor: colors.surfaceElevated,
    borderRadius: layout.radiusMd,
    padding: 10,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: 8,
  },
  activityHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  activityLabel: {
    ...typography.badge,
    color: colors.primaryLight,
  },
  liveTag: {
    fontSize: 7.5,
    fontFamily: 'monospace',
    fontWeight: '700',
    color: colors.successLight,
    backgroundColor: colors.successGlow,
    paddingHorizontal: 4,
    paddingVertical: 2,
    borderRadius: 4,
  },
  activityAction: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.textPrimary,
    marginTop: 2,
  },
  activityFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 6,
    paddingTop: 6,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  locationText: {
    fontSize: 9.5,
    color: colors.textSecondary,
  },
  moodText: {
    fontSize: 9.5,
    color: colors.textMuted,
    fontStyle: 'italic',
  },
  statsGrid: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 8,
  },
  statCard: {
    flex: 1,
    backgroundColor: colors.surfaceElevated,
    borderRadius: layout.radiusSm,
    padding: 8,
    borderWidth: 1,
    borderColor: colors.border,
  },
  statLabel: {
    ...typography.caption,
  },
  incomeValue: {
    ...typography.numberMedium,
    fontSize: 13,
    color: colors.successLight,
    marginTop: 2,
  },
  statValue: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.textPrimary,
    marginTop: 2,
  },
  statSub: {
    ...typography.caption,
    marginTop: 2,
  },
  biometricsCard: {
    backgroundColor: colors.surfaceElevated,
    borderRadius: layout.radiusMd,
    padding: 10,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: 8,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  sectionTitle: {
    ...typography.bodyBold,
  },
  riskBadge: {
    fontSize: 9,
    fontWeight: '700',
    color: colors.successLight,
    backgroundColor: colors.successGlow,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    fontFamily: 'monospace',
  },
  bioGrid: {
    flexDirection: 'row',
    gap: 6,
  },
  bioBox: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: 6,
    padding: 6,
    alignItems: 'center',
  },
  bioLabel: {
    fontSize: 8.5,
    color: colors.textMuted,
  },
  bioValue: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.textPrimary,
    fontFamily: 'monospace',
    marginTop: 2,
  },
  lifestyleCard: {
    backgroundColor: colors.surfaceElevated,
    borderRadius: layout.radiusMd,
    padding: 10,
    borderWidth: 1,
    borderColor: colors.border,
  },
  lifestyleGrid: {
    gap: 6,
    marginTop: 6,
  },
  lifestyleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  lifestyleKey: {
    ...typography.caption,
  },
  lifestyleVal: {
    fontSize: 10.5,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  actionFooter: {
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: 8,
  },
  primaryActionBtn: {
    flexDirection: 'row',
    backgroundColor: colors.primary,
    paddingVertical: 10,
    borderRadius: layout.radiusMd,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryActionText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '700',
  },
});
