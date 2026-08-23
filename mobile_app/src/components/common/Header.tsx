import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons, Feather } from '@expo/vector-icons';
import { useApp } from '../../context/AppContext';
import { BackendSettingsModal } from './BackendSettingsModal';
import { colors, typography, layout } from '../../constants/theme';

export const Header: React.FC = () => {
  const {
    activeTab,
    setActiveTab,
    unreadAlertsCount,
    selectedTwin,
    activeExperiment,
    isBackendConnected,
    currentUser,
    isAuthenticated,
    logout,
  } = useApp();

  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const getTitle = () => {
    switch (activeTab) {
      case 'home': return 'Command Center';
      case 'twins': return 'Digital Twins';
      case 'live_map': return selectedTwin.name;
      case 'experiments': return 'Cloud Experiments';
      case 'agents': return 'Agent Evaluation';
      case 'population': return 'Synthetic Population';
      case 'reasoning': return 'Cognitive Trace';
      case 'alerts': return 'Real-Time Alerts';
      case 'analytics': return 'Telemetry & Metrics';
      case 'comparison': return 'Model Comparison';
      case 'marketplace': return 'Twin & Model Hub';
      case 'billing': return 'Compute & Billing';
      case 'collaboration': return 'Team Workspace';
      case 'reports': return 'Research Reports';
      case 'gov_mode': return 'Municipal Authority';
      case 'experiment_watch': return 'Experiment Watch';
      case 'disasters_pandemics': return 'Emergency Operations';
      case 'social_feed': return 'Citizen Pulse';
      case 'ai_advisor': return 'City AI Copilot';
      case 'infrastructure': return 'Infrastructure Grid';
      case 'elections': return 'Civic Elections';
      case 'account_auth': return 'Account & Security';
      default: return 'CogniCity';
    }
  };

  return (
    <>
      <View style={styles.headerContainer}>
        {/* Top Status & Brand Row */}
        <View style={styles.topMicroRow}>
          <View style={styles.brandRow}>
            <View style={styles.pulseDot} />
            <Text style={styles.brandText}>COGNICITY</Text>

            {isAuthenticated && currentUser && (
              <View style={styles.roleBadge}>
                <Text style={styles.roleText}>{currentUser.role.replace('_', ' ')}</Text>
              </View>
            )}

            {isAuthenticated && (
              <TouchableOpacity onPress={() => setActiveTab('account_auth')} style={styles.userBadge} activeOpacity={0.7}>
                <Feather name="user" size={11} color={colors.textSecondary} />
                <Text style={styles.userRoleText}>{currentUser?.role === 'super_admin' ? 'Super Admin' : currentUser?.name?.split(' ')[0] || 'User'}</Text>
              </TouchableOpacity>
            )}

            {isAuthenticated && (
              <TouchableOpacity
                onPress={() => logout()}
                style={styles.logoutIconBtn}
                activeOpacity={0.7}
                accessibilityLabel="Sign out"
              >
                <Feather name="log-out" size={13} color={colors.textSecondary} />
              </TouchableOpacity>
            )}
          </View>

          <View style={styles.statusRow}>
            {activeExperiment && (
              <TouchableOpacity 
                onPress={() => setActiveTab('experiment_watch')}
                style={styles.expBadge}
                activeOpacity={0.7}
              >
                <Feather name="activity" size={10} color={colors.primaryLight} style={{ marginRight: 3 }} />
                <Text style={styles.expText}>{activeExperiment.progressPercent}%</Text>
              </TouchableOpacity>
            )}

            {/* Backend Connection Indicator */}
            <TouchableOpacity 
              onPress={() => setIsSettingsOpen(true)}
              style={[styles.healthBadge, isBackendConnected ? styles.bgConnected : styles.bgOffline]}
              activeOpacity={0.7}
            >
              <View style={[styles.statusDot, isBackendConnected ? styles.dotGreen : styles.dotAmber]} />
              <Text style={[styles.healthText, isBackendConnected ? styles.textConnected : styles.textOffline]}>
                {isBackendConnected ? 'API LIVE' : 'STANDALONE'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Main Title Row */}
        <View style={styles.mainTitleRow}>
          <Text style={styles.titleText} numberOfLines={1}>{getTitle()}</Text>

          <View style={styles.actionButtons}>
            {activeTab === 'live_map' && (
              <TouchableOpacity
                onPress={() => setActiveTab('twins')}
                style={styles.pillBtn}
                activeOpacity={0.7}
              >
                <Feather name="grid" size={12} color={colors.textSecondary} style={{ marginRight: 4 }} />
                <Text style={styles.pillBtnText}>Twins</Text>
              </TouchableOpacity>
            )}

            <TouchableOpacity
              onPress={() => setActiveTab('alerts')}
              style={styles.alertBtn}
              activeOpacity={0.7}
            >
              <Ionicons name="notifications-outline" size={16} color={colors.textPrimary} />
              {unreadAlertsCount > 0 && (
                <View style={styles.badgeCount}>
                  <Text style={styles.badgeText}>{unreadAlertsCount}</Text>
                </View>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </View>

      <BackendSettingsModal
        visible={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
    </>
  );
};

const styles = StyleSheet.create({
  headerContainer: {
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    paddingHorizontal: layout.cardPadding,
    paddingTop: 12,
    paddingBottom: 12,
  },
  topMicroRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  pulseDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.success,
  },
  brandText: {
    fontSize: 10,
    fontWeight: '800',
    color: colors.primaryLight,
    letterSpacing: 1.2,
  },
  roleBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primaryGlow,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: 'rgba(99, 102, 241, 0.25)',
  },
  roleText: {
    fontSize: 9,
    color: colors.primaryLight,
    fontWeight: '700',
  },
  userBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceElevated,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
    gap: 3,
    borderWidth: 1,
    borderColor: colors.border,
  },
  logoutIconBtn: {
    width: 22,
    height: 22,
    borderRadius: 6,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surfaceElevated,
    borderWidth: 1,
    borderColor: colors.border,
  },
  userRoleText: {
    fontSize: 9,
    color: colors.textSecondary,
    fontWeight: '600',
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  expBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primaryGlow,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: 'rgba(99, 102, 241, 0.3)',
  },
  expText: {
    fontSize: 9,
    color: colors.primaryLight,
    fontWeight: '700',
    fontFamily: 'monospace',
  },
  healthBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
    gap: 4,
    borderWidth: 1,
  },
  bgConnected: {
    backgroundColor: colors.successGlow,
    borderColor: 'rgba(16, 185, 129, 0.3)',
  },
  bgOffline: {
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
  healthText: {
    fontSize: 8.5,
    fontWeight: '700',
    fontFamily: 'monospace',
    letterSpacing: 0.4,
  },
  textConnected: {
    color: colors.successLight,
  },
  textOffline: {
    color: colors.warningLight,
  },
  mainTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  titleText: {
    ...typography.h2,
    flex: 1,
  },
  actionButtons: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  pillBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceElevated,
    paddingHorizontal: 8,
    paddingVertical: 5,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
  },
  pillBtnText: {
    fontSize: 11,
    color: colors.textSecondary,
    fontWeight: '600',
  },
  alertBtn: {
    backgroundColor: colors.surfaceElevated,
    width: 32,
    height: 32,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
    borderWidth: 1,
    borderColor: colors.border,
  },
  badgeCount: {
    position: 'absolute',
    top: -3,
    right: -3,
    backgroundColor: colors.danger,
    minWidth: 14,
    height: 14,
    borderRadius: 7,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 2,
  },
  badgeText: {
    color: '#ffffff',
    fontSize: 8,
    fontWeight: '800',
  },
});
