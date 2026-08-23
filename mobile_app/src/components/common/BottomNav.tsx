import React, { useMemo, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Modal, ScrollView } from 'react-native';
import { Ionicons, Feather, MaterialCommunityIcons } from '@expo/vector-icons';
import { useApp } from '../../context/AppContext';
import { ActiveTab } from '../../types';
import { colors, typography, layout } from '../../constants/theme';

interface NavItem {
  id: ActiveTab;
  label: string;
  iconName: string;
  iconFamily: 'Ionicons' | 'Feather' | 'MaterialCommunityIcons';
}

// Tabs mapped onto the backend feature-module keys that gate them (see
// backend/app/core/feature_modules.py). A tab absent from this map has no
// plan-tier gate and stays visible to everyone. A tab shows if the org's
// allowed_modules is empty (unrestricted) or includes ANY of its listed keys.
const TAB_MODULE_KEYS: Partial<Record<ActiveTab, string[]>> = {
  twins: ['twin_platform'],
  agents: ['agent_eval'],
  disasters_pandemics: ['disasters', 'pandemic'],
  social_feed: ['social_media'],
  ai_advisor: ['ai_advisor'],
  infrastructure: ['infrastructure'],
  elections: ['elections'],
  gov_mode: ['government'],
};

export const BottomNav: React.FC = () => {
  const { activeTab, setActiveTab, unreadAlertsCount, currentOrg } = useApp();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const isTabAllowed = useMemo(() => {
    const allowedModules: string[] | undefined = currentOrg?.allowed_modules;
    return (tabId: ActiveTab): boolean => {
      const requiredKeys = TAB_MODULE_KEYS[tabId];
      if (!requiredKeys) return true;
      if (!allowedModules || allowedModules.length === 0) return true;
      return requiredKeys.some((k) => allowedModules.includes(k));
    };
  }, [currentOrg]);

  // 5 Main Quick Bar Tabs with sleek vector icons
  const primaryTabs: NavItem[] = [
    { id: 'home', label: 'Command', iconName: 'view-dashboard-outline', iconFamily: 'MaterialCommunityIcons' },
    { id: 'twins', label: 'Twins', iconName: 'globe-outline', iconFamily: 'Ionicons' },
    { id: 'live_map', label: 'Map', iconName: 'map-outline', iconFamily: 'Ionicons' },
    { id: 'ai_advisor', label: 'Advisor', iconName: 'cpu', iconFamily: 'Feather' },
    { id: 'alerts', label: 'Alerts', iconName: 'notifications-outline', iconFamily: 'Ionicons' },
  ];

  // All Features in Drawer Sheet grouped by Domain
  const allModules: Array<{ section: string; items: NavItem[] }> = [
    {
      section: 'SIMULATION & DIGITAL TWINS',
      items: [
        { id: 'home', label: 'Command Center', iconName: 'view-dashboard-outline', iconFamily: 'MaterialCommunityIcons' },
        { id: 'twins', label: 'Digital Twin Catalog', iconName: 'globe-outline', iconFamily: 'Ionicons' },
        { id: 'live_map', label: 'Live 2.5D City Canvas', iconName: 'map-outline', iconFamily: 'Ionicons' },
        { id: 'experiment_watch', label: 'Cloud Run Watch', iconName: 'activity', iconFamily: 'Feather' },
        { id: 'comparison', label: 'Model A/B Benchmarks', iconName: 'git-compare-outline', iconFamily: 'Ionicons' },
      ],
    },
    {
      section: 'MUNICIPAL & EMERGENCY OPS',
      items: [
        { id: 'disasters_pandemics', label: 'Disasters & Outbreaks', iconName: 'alert-triangle', iconFamily: 'Feather' },
        { id: 'social_feed', label: 'Citizen Pulse Stream', iconName: 'message-square', iconFamily: 'Feather' },
        { id: 'ai_advisor', label: 'Mayor AI Copilot', iconName: 'cpu', iconFamily: 'Feather' },
        { id: 'infrastructure', label: 'Infrastructure Grid', iconName: 'layers', iconFamily: 'Feather' },
        { id: 'elections', label: 'Civic Elections & Polling', iconName: 'check-square', iconFamily: 'Feather' },
      ],
    },
    {
      section: 'AI AGENTS & POPULATION',
      items: [
        { id: 'agents', label: 'Agent Sandbox Test', iconName: 'shield-outline', iconFamily: 'Ionicons' },
        { id: 'population', label: 'Synthetic Population', iconName: 'people-outline', iconFamily: 'Ionicons' },
        { id: 'reasoning', label: 'Cognitive Trace (XAI)', iconName: 'git-commit', iconFamily: 'Feather' },
        { id: 'analytics', label: 'Telemetry & Analytics', iconName: 'bar-chart-2', iconFamily: 'Feather' },
      ],
    },
    {
      section: 'ENTERPRISE & WORKSPACE',
      items: [
        { id: 'account_auth', label: 'Security & Auth', iconName: 'lock', iconFamily: 'Feather' },
        { id: 'gov_mode', label: 'Municipal Departments', iconName: 'briefcase', iconFamily: 'Feather' },
        { id: 'marketplace', label: 'Twin & Model Store', iconName: 'shopping-bag', iconFamily: 'Feather' },
        { id: 'billing', label: 'Compute Credits Ledger', iconName: 'credit-card', iconFamily: 'Feather' },
        { id: 'collaboration', label: 'Team Workspace', iconName: 'users', iconFamily: 'Feather' },
        { id: 'reports', label: 'Research Export', iconName: 'file-text', iconFamily: 'Feather' },
      ],
    },
  ];

  const handleSelectTab = (tabId: ActiveTab) => {
    setActiveTab(tabId);
    setIsDrawerOpen(false);
  };

  const visiblePrimaryTabs = primaryTabs.filter((t) => isTabAllowed(t.id));
  const visibleModules = allModules
    .map((group) => ({ ...group, items: group.items.filter((t) => isTabAllowed(t.id)) }))
    .filter((group) => group.items.length > 0);

  const renderIcon = (item: NavItem, isSelected: boolean, size: number = 20) => {
    const iconColor = isSelected ? colors.primaryLight : colors.textMuted;
    if (item.iconFamily === 'Ionicons') {
      return <Ionicons name={item.iconName as any} size={size} color={iconColor} />;
    }
    if (item.iconFamily === 'Feather') {
      return <Feather name={item.iconName as any} size={size} color={iconColor} />;
    }
    return <MaterialCommunityIcons name={item.iconName as any} size={size} color={iconColor} />;
  };

  return (
    <>
      <View style={styles.navBarContainer}>
        {visiblePrimaryTabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <TouchableOpacity
              key={tab.id}
              onPress={() => setActiveTab(tab.id)}
              style={styles.tabButton}
              activeOpacity={0.7}
            >
              <View style={styles.iconWrapper}>
                {renderIcon(tab, isActive, 20)}
                {tab.id === 'alerts' && unreadAlertsCount > 0 && (
                  <View style={styles.badgeDot} />
                )}
              </View>
              <Text style={[styles.tabLabel, isActive && styles.activeTabLabel]}>
                {tab.label}
              </Text>
              {isActive && <View style={styles.activePill} />}
            </TouchableOpacity>
          );
        })}

        {/* All Modules Drawer Toggle */}
        <TouchableOpacity
          onPress={() => setIsDrawerOpen(true)}
          style={styles.tabButton}
          activeOpacity={0.7}
        >
          <View style={styles.iconWrapper}>
            <Feather name="grid" size={19} color={colors.textMuted} />
          </View>
          <Text style={styles.tabLabel}>More</Text>
        </TouchableOpacity>
      </View>

      {/* Slide-Up Navigation Drawer Modal */}
      <Modal
        visible={isDrawerOpen}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setIsDrawerOpen(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.drawerContainer}>
            {/* Drawer Header */}
            <View style={styles.drawerHeader}>
              <View style={styles.drawerTitleRow}>
                <View style={styles.pulseDot} />
                <Text style={styles.drawerTitle}>Platform Navigation</Text>
              </View>
              <TouchableOpacity
                onPress={() => setIsDrawerOpen(false)}
                style={styles.closeBtn}
                activeOpacity={0.7}
              >
                <Feather name="x" size={16} color={colors.textSecondary} />
              </TouchableOpacity>
            </View>

            {/* Scrollable list of all modules */}
            <ScrollView style={styles.modulesScroll} showsVerticalScrollIndicator={false}>
              {visibleModules.map((group, gIdx) => (
                <View key={gIdx} style={styles.groupSection}>
                  <Text style={styles.groupHeading}>{group.section}</Text>
                  <View style={styles.gridContainer}>
                    {group.items.map((item) => {
                      const isSelected = activeTab === item.id;
                      return (
                        <TouchableOpacity
                          key={item.id}
                          onPress={() => handleSelectTab(item.id)}
                          style={[
                            styles.gridItem,
                            isSelected && styles.gridItemSelected,
                          ]}
                          activeOpacity={0.7}
                        >
                          <View style={[styles.gridIconBox, isSelected && styles.gridIconBoxSelected]}>
                            {renderIcon(item, isSelected, 16)}
                          </View>
                          <Text
                            style={[
                              styles.gridLabel,
                              isSelected && styles.gridLabelSelected,
                            ]}
                            numberOfLines={1}
                          >
                            {item.label}
                          </Text>
                        </TouchableOpacity>
                      );
                    })}
                  </View>
                </View>
              ))}
            </ScrollView>
          </View>
        </View>
      </Modal>
    </>
  );
};

const styles = StyleSheet.create({
  navBarContainer: {
    flexDirection: 'row',
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingVertical: 8,
    paddingHorizontal: 6,
    justifyContent: 'space-around',
    alignItems: 'center',
  },
  tabButton: {
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
    paddingVertical: 2,
    position: 'relative',
  },
  iconWrapper: {
    position: 'relative',
    height: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  badgeDot: {
    position: 'absolute',
    top: -2,
    right: -4,
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.danger,
  },
  tabLabel: {
    fontSize: 9.5,
    color: colors.textMuted,
    marginTop: 3,
    fontWeight: '500',
  },
  activeTabLabel: {
    color: colors.primaryLight,
    fontWeight: '700',
  },
  activePill: {
    width: 12,
    height: 2,
    backgroundColor: colors.primary,
    borderRadius: 1,
    marginTop: 2,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(5, 8, 15, 0.85)',
    justifyContent: 'flex-end',
  },
  drawerContainer: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: layout.cardPadding,
    maxHeight: '85%',
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  drawerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    paddingBottom: 12,
    marginBottom: 8,
  },
  drawerTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  pulseDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.primary,
  },
  drawerTitle: {
    ...typography.h2,
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
  modulesScroll: {
    paddingVertical: 4,
  },
  groupSection: {
    marginBottom: 16,
  },
  groupHeading: {
    ...typography.badge,
    color: colors.textMuted,
    marginBottom: 8,
  },
  gridContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  gridItem: {
    flexBasis: '48.5%',
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceElevated,
    paddingHorizontal: 10,
    paddingVertical: 10,
    borderRadius: layout.radiusMd,
    gap: 8,
    borderWidth: 1,
    borderColor: colors.border,
  },
  gridItemSelected: {
    backgroundColor: colors.primaryGlow,
    borderColor: colors.borderActive,
  },
  gridIconBox: {
    width: 28,
    height: 28,
    borderRadius: 6,
    backgroundColor: colors.surfaceSubtle,
    alignItems: 'center',
    justifyContent: 'center',
  },
  gridIconBoxSelected: {
    backgroundColor: 'rgba(99, 102, 241, 0.25)',
  },
  gridLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.textSecondary,
    flex: 1,
  },
  gridLabelSelected: {
    color: colors.textPrimary,
    fontWeight: '700',
  },
});
