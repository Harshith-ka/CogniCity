import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { Ionicons, Feather, MaterialCommunityIcons } from '@expo/vector-icons';
import { useApp } from '../../context/AppContext';
import { DisasterIncident } from '../../types';
import { colors, typography, layout } from '../../constants/theme';

export const DisasterPandemicView: React.FC = () => {
  const { 
    disasters, 
    triggerDisaster, 
    resolveDisaster, 
    pandemic, 
    togglePandemicPolicy 
  } = useApp();

  const [activeSubTab, setActiveSubTab] = useState<'disasters' | 'pandemic'>('disasters');
  const [selectedDisasterType, setSelectedDisasterType] = useState<DisasterIncident['type']>('fire');
  const [selectedDistrict, setSelectedDistrict] = useState('Westside District');

  const disasterOptions: Array<{ type: DisasterIncident['type']; iconName: string; name: string }> = [
    { type: 'fire', iconName: 'flame-outline', name: 'Structural Fire' },
    { type: 'flood', iconName: 'water-outline', name: 'Flash Flood' },
    { type: 'earthquake', iconName: 'pulse-outline', name: 'Earthquake' },
    { type: 'blackout', iconName: 'flash-off-outline', name: 'Grid Blackout' },
    { type: 'chemical', iconName: 'warning-outline', name: 'Chemical Leak' },
  ];

  const districts = ['Westside District', 'Cyber Towers', 'Riverside Lowlands', 'Industrial East', 'Greenwood'];

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {/* Top Switcher */}
      <View style={styles.subTabRow}>
        <TouchableOpacity
          onPress={() => setActiveSubTab('disasters')}
          style={[styles.subTabBtn, activeSubTab === 'disasters' && styles.subTabBtnActiveRed]}
          activeOpacity={0.7}
        >
          <Feather name="alert-triangle" size={13} color={activeSubTab === 'disasters' ? colors.dangerLight : colors.textMuted} style={{ marginRight: 6 }} />
          <Text style={[styles.subTabText, activeSubTab === 'disasters' && styles.subTabTextActive]}>
            Disasters ({disasters.filter((d) => d.isActive).length} Active)
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => setActiveSubTab('pandemic')}
          style={[styles.subTabBtn, activeSubTab === 'pandemic' && styles.subTabBtnActiveAmber]}
          activeOpacity={0.7}
        >
          <Ionicons name="medical-outline" size={13} color={activeSubTab === 'pandemic' ? colors.warningLight : colors.textMuted} style={{ marginRight: 6 }} />
          <Text style={[styles.subTabText, activeSubTab === 'pandemic' && styles.subTabTextActive]}>
            Pandemic Engine
          </Text>
        </TouchableOpacity>
      </View>

      {activeSubTab === 'disasters' ? (
        <>
          {/* Incident Injector */}
          <View style={styles.triggerCard}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardTag}>INCIDENT INJECTOR</Text>
              <Text style={styles.cardTitle}>Trigger Urban Crisis Scenario</Text>
            </View>

            {/* Disaster Type Pills */}
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.pillsScroll}>
              {disasterOptions.map((opt) => (
                <TouchableOpacity
                  key={opt.type}
                  onPress={() => setSelectedDisasterType(opt.type)}
                  style={[styles.disasterPill, selectedDisasterType === opt.type && styles.disasterPillActive]}
                  activeOpacity={0.7}
                >
                  <Ionicons name={opt.iconName as any} size={14} color={selectedDisasterType === opt.type ? '#ffffff' : colors.textSecondary} />
                  <Text style={[styles.pillText, selectedDisasterType === opt.type && styles.pillTextActive]}>
                    {opt.name}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>

            {/* District Selector */}
            <View style={styles.districtSelector}>
              <Text style={styles.districtLabel}>TARGET DISTRICT</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.districtScroll}>
                {districts.map((d) => (
                  <TouchableOpacity
                    key={d}
                    onPress={() => setSelectedDistrict(d)}
                    style={[styles.districtBtn, selectedDistrict === d && styles.districtBtnActive]}
                    activeOpacity={0.7}
                  >
                    <Text style={[styles.districtBtnText, selectedDistrict === d && styles.districtBtnTextActive]}>
                      {d}
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>

            <TouchableOpacity
              onPress={() => triggerDisaster(selectedDisasterType, selectedDistrict)}
              style={styles.triggerActionBtn}
              activeOpacity={0.7}
            >
              <Feather name="zap" size={14} color="#ffffff" style={{ marginRight: 6 }} />
              <Text style={styles.triggerActionText}>Dispatch Incident Simulation</Text>
            </TouchableOpacity>
          </View>

          {/* Active Disasters List */}
          <View style={styles.incidentsSection}>
            <Text style={styles.sectionHeading}>ACTIVE INCIDENTS & DISASTER LIFECYCLE</Text>
            {disasters.map((disaster) => (
              <View key={disaster.id} style={[styles.incidentCard, !disaster.isActive && styles.incidentCardResolved]}>
                <View style={styles.incidentTop}>
                  <View style={styles.incidentTitleRow}>
                    <View style={styles.iconBox}>
                      <Ionicons
                        name={disaster.type === 'fire' ? 'flame-outline' : disaster.type === 'flood' ? 'water-outline' : 'alert-circle-outline'}
                        size={18}
                        color={disaster.isActive ? colors.dangerLight : colors.textMuted}
                      />
                    </View>
                    <View>
                      <Text style={styles.incidentName}>{disaster.title}</Text>
                      <Text style={styles.districtSub}>{disaster.district} • {disaster.startedAt}</Text>
                    </View>
                  </View>

                  <View style={[styles.phaseBadge, disaster.isActive ? styles.phaseActive : styles.phaseResolved]}>
                    <Text style={styles.phaseText}>{disaster.phase.toUpperCase()}</Text>
                  </View>
                </View>

                <Text style={styles.narrativeText}>{disaster.responseNarrative}</Text>

                <View style={styles.incidentMetaRow}>
                  <Text style={styles.metaItem}>Affected: <Text style={styles.highlightVal}>{disaster.affectedCitizens.toLocaleString()}</Text></Text>
                  <Text style={styles.metaItem}>Zone: <Text style={styles.highlightVal}>{disaster.evacuationZoneRadius}m</Text></Text>
                  <Text style={styles.metaItem}>Intensity: <Text style={styles.highlightVal}>{(disaster.intensity * 100).toFixed(0)}%</Text></Text>
                </View>

                {disaster.isActive && (
                  <TouchableOpacity
                    onPress={() => resolveDisaster(disaster.id)}
                    style={styles.resolveBtn}
                    activeOpacity={0.7}
                  >
                    <Feather name="check" size={13} color={colors.successLight} style={{ marginRight: 4 }} />
                    <Text style={styles.resolveBtnText}>Stand Down Incident</Text>
                  </TouchableOpacity>
                )}
              </View>
            ))}
          </View>
        </>
      ) : (
        /* Pandemic Outbreak View */
        <View style={styles.pandemicCard}>
          <View style={styles.pandemicTop}>
            <View>
              <Text style={styles.cardTag}>EPIDEMIOLOGICAL MODEL</Text>
              <Text style={styles.pandemicTitle}>{pandemic.pathogenName}</Text>
              <Text style={styles.variantText}>Variant: {pandemic.variant} • Spread: {pandemic.spreadVelocity}</Text>
            </View>
            <View style={styles.r0Box}>
              <Text style={styles.r0Label}>Reproduction</Text>
              <Text style={styles.r0Value}>R₀ {pandemic.r0.toFixed(1)}</Text>
            </View>
          </View>

          {/* Stats Grid */}
          <View style={styles.pandemicStatsGrid}>
            <View style={styles.statBox}>
              <Text style={styles.statBoxLabel}>Total Infected</Text>
              <Text style={[styles.statBoxVal, { color: colors.dangerLight }]}>{pandemic.totalInfected.toLocaleString()}</Text>
            </View>
            <View style={styles.statBox}>
              <Text style={styles.statBoxLabel}>Hospitalized</Text>
              <Text style={[styles.statBoxVal, { color: colors.warningLight }]}>{pandemic.activeHospitalizations}</Text>
            </View>
            <View style={styles.statBox}>
              <Text style={styles.statBoxLabel}>Recovered</Text>
              <Text style={[styles.statBoxVal, { color: colors.successLight }]}>{pandemic.totalRecovered.toLocaleString()}</Text>
            </View>
          </View>

          {/* Policy Mandate Toggles */}
          <View style={styles.policySection}>
            <Text style={styles.policyHeading}>GOVERNMENT EPIDEMIC POLICIES</Text>

            <View style={styles.policyRow}>
              <View>
                <Text style={styles.policyTitle}>Quarantine Red Zones</Text>
                <Text style={styles.policySub}>Restricts inter-district mobility</Text>
              </View>
              <TouchableOpacity
                onPress={() => togglePandemicPolicy('quarantine')}
                style={[styles.toggleBtn, pandemic.quarantineActive ? styles.toggleOn : styles.toggleOff]}
                activeOpacity={0.7}
              >
                <Text style={styles.toggleText}>{pandemic.quarantineActive ? 'ENACTED' : 'DISABLED'}</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.policyRow}>
              <View>
                <Text style={styles.policyTitle}>Universal Mask Mandate</Text>
                <Text style={styles.policySub}>Reduces transmission rate R₀ by 0.4</Text>
              </View>
              <TouchableOpacity
                onPress={() => togglePandemicPolicy('mask_mandate')}
                style={[styles.toggleBtn, pandemic.maskMandateActive ? styles.toggleOn : styles.toggleOff]}
                activeOpacity={0.7}
              >
                <Text style={styles.toggleText}>{pandemic.maskMandateActive ? 'ENACTED' : 'DISABLED'}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      )}
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
  subTabRow: {
    flexDirection: 'row',
    backgroundColor: colors.surface,
    borderRadius: layout.radiusMd,
    padding: 3,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 4,
  },
  subTabBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 9,
    borderRadius: layout.radiusSm,
  },
  subTabBtnActiveRed: {
    backgroundColor: colors.dangerGlow,
  },
  subTabBtnActiveAmber: {
    backgroundColor: colors.warningGlow,
  },
  subTabText: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.textMuted,
  },
  subTabTextActive: {
    color: colors.textPrimary,
    fontWeight: '700',
  },
  triggerCard: {
    backgroundColor: colors.surface,
    borderRadius: layout.radiusLg,
    padding: layout.cardPadding,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 10,
  },
  cardHeader: {
    marginBottom: 2,
  },
  cardTag: {
    ...typography.badge,
    color: colors.dangerLight,
  },
  cardTitle: {
    ...typography.h2,
    marginTop: 2,
  },
  pillsScroll: {
    flexDirection: 'row',
  },
  disasterPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceElevated,
    paddingHorizontal: 10,
    paddingVertical: 7,
    borderRadius: layout.radiusSm,
    marginRight: 6,
    gap: 5,
    borderWidth: 1,
    borderColor: colors.border,
  },
  disasterPillActive: {
    backgroundColor: colors.danger,
    borderColor: colors.dangerLight,
  },
  pillText: {
    fontSize: 10.5,
    color: colors.textSecondary,
    fontWeight: '600',
  },
  pillTextActive: {
    color: '#ffffff',
    fontWeight: '700',
  },
  districtSelector: {
    gap: 6,
    marginTop: 4,
  },
  districtLabel: {
    ...typography.badge,
    color: colors.textMuted,
  },
  districtScroll: {
    flexDirection: 'row',
  },
  districtBtn: {
    backgroundColor: colors.surfaceElevated,
    paddingHorizontal: 9,
    paddingVertical: 6,
    borderRadius: layout.radiusSm,
    marginRight: 6,
    borderWidth: 1,
    borderColor: colors.border,
  },
  districtBtnActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primaryLight,
  },
  districtBtnText: {
    fontSize: 10,
    color: colors.textMuted,
    fontWeight: '600',
  },
  districtBtnTextActive: {
    color: '#ffffff',
    fontWeight: '700',
  },
  triggerActionBtn: {
    flexDirection: 'row',
    backgroundColor: colors.danger,
    paddingVertical: 11,
    borderRadius: layout.radiusMd,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 4,
  },
  triggerActionText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '700',
  },
  incidentsSection: {
    gap: 8,
    marginTop: 4,
  },
  sectionHeading: {
    ...typography.badge,
    color: colors.textMuted,
  },
  incidentCard: {
    backgroundColor: colors.surface,
    borderRadius: layout.radiusMd,
    padding: 12,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 8,
  },
  incidentCardResolved: {
    opacity: 0.6,
  },
  incidentTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  incidentTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
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
  incidentName: {
    ...typography.bodyBold,
  },
  districtSub: {
    ...typography.caption,
    marginTop: 1,
  },
  phaseBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  phaseActive: {
    backgroundColor: colors.dangerGlow,
    borderWidth: 1,
    borderColor: 'rgba(244, 63, 94, 0.3)',
  },
  phaseResolved: {
    backgroundColor: colors.surfaceElevated,
  },
  phaseText: {
    fontSize: 8.5,
    fontWeight: '700',
    color: colors.dangerLight,
    fontFamily: 'monospace',
  },
  narrativeText: {
    fontSize: 11,
    color: colors.dangerLight,
    lineHeight: 15,
  },
  incidentMetaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: 6,
  },
  metaItem: {
    ...typography.caption,
  },
  highlightVal: {
    color: colors.textPrimary,
    fontWeight: '700',
    fontFamily: 'monospace',
  },
  resolveBtn: {
    flexDirection: 'row',
    backgroundColor: colors.surfaceElevated,
    paddingVertical: 7,
    borderRadius: layout.radiusSm,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  resolveBtnText: {
    fontSize: 10.5,
    fontWeight: '700',
    color: colors.successLight,
  },
  pandemicCard: {
    backgroundColor: colors.surface,
    borderRadius: layout.radiusLg,
    padding: layout.cardPadding,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 12,
  },
  pandemicTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  pandemicTitle: {
    ...typography.h2,
    marginTop: 2,
  },
  variantText: {
    ...typography.caption,
    marginTop: 1,
  },
  r0Box: {
    backgroundColor: colors.warningGlow,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: layout.radiusSm,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(245, 158, 11, 0.3)',
  },
  r0Label: {
    fontSize: 7.5,
    color: colors.warningLight,
    fontFamily: 'monospace',
  },
  r0Value: {
    ...typography.numberMedium,
    fontSize: 13,
    color: colors.warningLight,
  },
  pandemicStatsGrid: {
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
  statBoxLabel: {
    ...typography.caption,
  },
  statBoxVal: {
    ...typography.numberMedium,
    fontSize: 13,
    marginTop: 2,
  },
  policySection: {
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: 10,
    gap: 8,
  },
  policyHeading: {
    ...typography.badge,
    color: colors.warningLight,
  },
  policyRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: colors.surfaceElevated,
    padding: 10,
    borderRadius: layout.radiusMd,
    borderWidth: 1,
    borderColor: colors.border,
  },
  policyTitle: {
    fontSize: 11.5,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  policySub: {
    ...typography.caption,
    marginTop: 1,
  },
  toggleBtn: {
    paddingHorizontal: 9,
    paddingVertical: 5,
    borderRadius: 6,
  },
  toggleOn: {
    backgroundColor: colors.success,
  },
  toggleOff: {
    backgroundColor: colors.textDisabled,
  },
  toggleText: {
    fontSize: 9,
    fontWeight: '800',
    color: '#ffffff',
    fontFamily: 'monospace',
  },
});
