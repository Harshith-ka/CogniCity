import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useApp } from '../../context/AppContext';
import { RealTimeAlert } from '../../types';

export const AlertsView: React.FC = () => {
  const { 
    alerts, 
    markAlertRead, 
    markAllAlertsRead, 
    setActiveTab, 
    setSelectedTwin,
    twins 
  } = useApp();

  const [filterSeverity, setFilterSeverity] = useState('all');

  const filteredAlerts = alerts.filter((a) => {
    if (filterSeverity === 'unread') return !a.read;
    if (filterSeverity === 'all') return true;
    return a.severity === filterSeverity;
  });

  const handleActionClick = (alert: RealTimeAlert) => {
    markAlertRead(alert.id);
    if (alert.title.includes('Anomaly') || alert.title.includes('Capacity')) {
      const twin = twins.find((t) => t.id === alert.twinId) || twins[0];
      setSelectedTwin(twin);
      setActiveTab('live_map');
    } else if (alert.title.includes('Experiment') || alert.title.includes('Report')) {
      setActiveTab('comparison');
    } else if (alert.title.includes('Heart') || alert.title.includes('Traffic')) {
      setActiveTab('agents');
    }
  };

  const getAlertIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return '🚨';
      case 'warning': return '⚠️';
      case 'success': return '✅';
      default: return 'ℹ️';
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {/* Header Row */}
      <View style={styles.headerRow}>
        <View>
          <View style={styles.titleRow}>
            <Text style={styles.headerTitle}>Live Alerts Center</Text>
            <Text style={styles.unreadBadge}>{alerts.filter((a) => !a.read).length} Unread</Text>
          </View>
          <Text style={styles.headerSubtitle}>Real-time simulation anomaly & model drift alerts</Text>
        </View>

        <TouchableOpacity onPress={markAllAlertsRead} style={styles.markReadBtn}>
          <Text style={styles.markReadText}>Mark Read</Text>
        </TouchableOpacity>
      </View>

      {/* Filter Tabs */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.pillsScroll}>
        {[
          { id: 'all', label: 'All Alerts' },
          { id: 'unread', label: 'Unread' },
          { id: 'critical', label: '🚨 Critical' },
          { id: 'warning', label: '⚠️ Warning' },
          { id: 'info', label: 'ℹ️ Info' },
        ].map((f) => (
          <TouchableOpacity
            key={f.id}
            onPress={() => setFilterSeverity(f.id)}
            style={[styles.filterPill, filterSeverity === f.id && styles.filterPillActive]}
          >
            <Text style={[styles.filterText, filterSeverity === f.id && styles.filterTextActive]}>
              {f.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Alerts Stream */}
      <View style={styles.alertsList}>
        {filteredAlerts.length === 0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyText}>No alerts found for this filter.</Text>
          </View>
        ) : (
          filteredAlerts.map((alert) => (
            <TouchableOpacity
              key={alert.id}
              onPress={() => markAlertRead(alert.id)}
              style={[styles.alertCard, !alert.read && styles.alertCardUnread]}
            >
              <View style={styles.alertContent}>
                <View style={styles.iconBox}>
                  <Text style={styles.iconEmoji}>{getAlertIcon(alert.severity)}</Text>
                </View>

                <View style={styles.textBox}>
                  <View style={styles.alertTop}>
                    <Text style={styles.alertTitle}>{alert.title}</Text>
                    {!alert.read && <View style={styles.unreadDot} />}
                  </View>

                  <Text style={styles.alertMessage}>{alert.message}</Text>

                  <View style={styles.alertFooter}>
                    <Text style={styles.sourceText}>
                      {alert.source} • {alert.timestamp}
                    </Text>

                    {alert.actionLabel && (
                      <TouchableOpacity onPress={() => handleActionClick(alert)}>
                        <Text style={styles.actionLink}>{alert.actionLabel} ➔</Text>
                      </TouchableOpacity>
                    )}
                  </View>
                </View>
              </View>
            </TouchableOpacity>
          ))
        )}
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
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#ffffff',
  },
  unreadBadge: {
    fontSize: 10,
    fontFamily: 'monospace',
    fontWeight: '800',
    color: '#fda4af',
    backgroundColor: '#881337',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  headerSubtitle: {
    fontSize: 11,
    color: '#94a3b8',
    marginTop: 2,
  },
  markReadBtn: {
    backgroundColor: '#1e293b',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#334155',
  },
  markReadText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#818cf8',
  },
  pillsScroll: {
    flexDirection: 'row',
  },
  filterPill: {
    backgroundColor: '#1e293b',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
    marginRight: 6,
    borderWidth: 1,
    borderColor: '#334155',
  },
  filterPillActive: {
    backgroundColor: '#4f46e5',
    borderColor: '#818cf8',
  },
  filterText: {
    fontSize: 11,
    color: '#94a3b8',
    fontWeight: '600',
  },
  filterTextActive: {
    color: '#ffffff',
    fontWeight: '700',
  },
  alertsList: {
    gap: 10,
  },
  emptyCard: {
    backgroundColor: '#0f172a',
    borderRadius: 20,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  emptyText: {
    fontSize: 12,
    color: '#64748b',
  },
  alertCard: {
    backgroundColor: 'rgba(15, 23, 42, 0.8)',
    borderRadius: 20,
    padding: 14,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  alertCardUnread: {
    borderColor: '#4f46e5',
    backgroundColor: 'rgba(15, 23, 42, 0.95)',
  },
  alertContent: {
    flexDirection: 'row',
    gap: 12,
  },
  iconBox: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: '#1e293b',
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconEmoji: {
    fontSize: 18,
  },
  textBox: {
    flex: 1,
  },
  alertTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  alertTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#ffffff',
    flex: 1,
  },
  unreadDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#ef4444',
  },
  alertMessage: {
    fontSize: 11,
    color: '#cbd5e1',
    marginTop: 4,
    lineHeight: 15,
  },
  alertFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 10,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#1e293b',
  },
  sourceText: {
    fontSize: 10,
    fontFamily: 'monospace',
    color: '#64748b',
  },
  actionLink: {
    fontSize: 11,
    fontWeight: '800',
    color: '#818cf8',
  },
});
