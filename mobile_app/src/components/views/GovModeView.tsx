import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useApp } from '../../context/AppContext';

export const GovModeView: React.FC = () => {
  const {
    departments,
    selectedDept,
    setSelectedDept,
    currentUser,
  } = useApp();

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {/* Gov Header Card */}
      <View style={styles.govHeaderCard}>
        <View style={styles.govTopRow}>
          <View style={styles.govTagRow}>
            <Text style={styles.govTagText}>MUNICIPAL GOV CONSOLE</Text>
            <View style={styles.govPulseDot} />
          </View>
          <View style={styles.secureBadge}>
            <Text style={styles.secureText}>SECURE ACCESS</Text>
          </View>
        </View>

        <Text style={styles.orgTitle}>ABC Metropolitan Smart City</Text>
        <Text style={styles.orgSubtitle}>Autonomous Infrastructure & Multi-Agency Simulation Node</Text>

        <View style={styles.roleSection}>
          <Text style={styles.roleSectionLabel}>YOUR AUTHENTICATED ACCESS TIER</Text>
          <View style={styles.roleButtonsRow}>
            <View style={[styles.roleBtn, styles.roleBtnActive]}>
              <Text style={[styles.roleBtnText, styles.roleBtnTextActive]}>
                {currentUser ? currentUser.role.replace('_', ' ') : 'Not signed in'}
              </Text>
            </View>
          </View>
        </View>
      </View>

      {/* Departments List */}
      <View style={styles.deptsSection}>
        <Text style={styles.deptsHeading}>MUNICIPAL DEPARTMENTS ({departments.length})</Text>

        <View style={styles.deptsList}>
          {departments.map((dept) => {
            const isSelected = selectedDept?.id === dept.id;
            return (
              <TouchableOpacity
                key={dept.id}
                onPress={() => setSelectedDept(dept)}
                style={[styles.deptCard, isSelected && styles.deptCardSelected]}
              >
                <View style={styles.deptTop}>
                  <View style={styles.deptProfile}>
                    <View style={styles.deptIconBox}>
                      <Text style={styles.deptEmoji}>{dept.icon}</Text>
                    </View>
                    <View>
                      <Text style={styles.deptName}>{dept.name}</Text>
                      <Text style={styles.deptLead}>Lead: {dept.lead}</Text>
                    </View>
                  </View>

                  <View style={styles.healthBox}>
                    <Text style={styles.healthLabel}>Health Index</Text>
                    <Text style={styles.healthVal}>{dept.kpiHealth}%</Text>
                  </View>
                </View>

                <View style={styles.deptStatsRow}>
                  <View style={styles.deptStatBox}>
                    <Text style={styles.deptStatLabel}>Active Sims</Text>
                    <Text style={styles.deptStatVal}>{dept.activeSimulations}</Text>
                  </View>
                  <View style={styles.deptStatBox}>
                    <Text style={styles.deptStatLabel}>Budget</Text>
                    <Text style={[styles.deptStatVal, { color: '#818cf8' }]}>{dept.budgetAllocated}</Text>
                  </View>
                  <View style={styles.deptStatBox}>
                    <Text style={styles.deptStatLabel}>Alerts</Text>
                    <Text style={[styles.deptStatVal, { color: dept.alertsCount > 0 ? '#fbbf24' : '#64748b' }]}>
                      {dept.alertsCount}
                    </Text>
                  </View>
                </View>
              </TouchableOpacity>
            );
          })}
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
  govHeaderCard: {
    backgroundColor: 'rgba(76, 5, 25, 0.6)',
    borderRadius: 24,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e11d48',
  },
  govTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  govTagRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  govTagText: {
    fontSize: 9,
    fontFamily: 'monospace',
    fontWeight: '800',
    color: '#fda4af',
    letterSpacing: 0.8,
  },
  govPulseDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#f43f5e',
  },
  secureBadge: {
    backgroundColor: '#1e293b',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  secureText: {
    fontSize: 9,
    fontFamily: 'monospace',
    color: '#cbd5e1',
  },
  orgTitle: {
    fontSize: 16,
    fontWeight: '900',
    color: '#ffffff',
  },
  orgSubtitle: {
    fontSize: 11,
    color: '#cbd5e1',
    marginTop: 2,
  },
  roleSection: {
    marginTop: 12,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: 'rgba(225, 29, 72, 0.3)',
  },
  roleSectionLabel: {
    fontSize: 8,
    fontFamily: 'monospace',
    fontWeight: '800',
    color: '#cbd5e1',
    marginBottom: 6,
  },
  roleButtonsRow: {
    flexDirection: 'row',
    gap: 6,
  },
  roleBtn: {
    flex: 1,
    backgroundColor: '#1e293b',
    paddingVertical: 6,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  roleBtnActive: {
    backgroundColor: '#e11d48',
    borderColor: '#f43f5e',
  },
  roleBtnText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#94a3b8',
  },
  roleBtnTextActive: {
    color: '#ffffff',
  },
  deptsSection: {
    gap: 8,
  },
  deptsHeading: {
    fontSize: 11,
    fontWeight: '800',
    color: '#94a3b8',
    letterSpacing: 0.8,
  },
  deptsList: {
    gap: 8,
  },
  deptCard: {
    backgroundColor: 'rgba(15, 23, 42, 0.9)',
    borderRadius: 20,
    padding: 14,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  deptCardSelected: {
    borderColor: '#e11d48',
  },
  deptTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  deptProfile: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
  },
  deptIconBox: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: '#1e293b',
    alignItems: 'center',
    justifyContent: 'center',
  },
  deptEmoji: {
    fontSize: 20,
  },
  deptName: {
    fontSize: 13,
    fontWeight: '800',
    color: '#ffffff',
  },
  deptLead: {
    fontSize: 10,
    color: '#94a3b8',
    marginTop: 1,
  },
  healthBox: {
    alignItems: 'flex-end',
  },
  healthLabel: {
    fontSize: 9,
    color: '#64748b',
  },
  healthVal: {
    fontSize: 12,
    fontWeight: '800',
    color: '#34d399',
    fontFamily: 'monospace',
  },
  deptStatsRow: {
    flexDirection: 'row',
    gap: 6,
    marginTop: 10,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#1e293b',
  },
  deptStatBox: {
    flex: 1,
    backgroundColor: '#090d16',
    borderRadius: 8,
    padding: 6,
    alignItems: 'center',
  },
  deptStatLabel: {
    fontSize: 8,
    color: '#64748b',
  },
  deptStatVal: {
    fontSize: 11,
    fontWeight: '800',
    color: '#ffffff',
    fontFamily: 'monospace',
    marginTop: 1,
  },
});
