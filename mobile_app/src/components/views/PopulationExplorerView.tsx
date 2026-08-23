import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput } from 'react-native';
import { useApp } from '../../context/AppContext';
import { SyntheticCitizen } from '../../types';

export const PopulationExplorerView: React.FC = () => {
  const { citizens, setSelectedCitizen, populationStats } = useApp();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterOcc, setFilterOcc] = useState('all');

  const occupations = ['all', 'Teacher', 'Software Architect', 'Cardiologist', 'UI Designer', 'Technician'];

  const filteredCitizens = citizens.filter((c) => {
    const matchesSearch = c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.occupation.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.location.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesOcc = filterOcc === 'all' || c.occupation.includes(filterOcc);
    return matchesSearch && matchesOcc;
  });

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {/* Banner */}
      <View style={styles.bannerCard}>
        <View style={styles.bannerTop}>
          <View>
            <Text style={styles.bannerTag}>DEMOGRAPHIC SAMPLER</Text>
            <Text style={styles.bannerHeading}>10,000 Synthetic Citizens</Text>
          </View>
          <View style={styles.bannerIconBox}>
            <Text style={styles.bannerIcon}>👥</Text>
          </View>
        </View>

        <View style={styles.statsRow}>
          <View style={styles.statBox}>
            <Text style={styles.statLabel}>Avg. Age</Text>
            <Text style={styles.statVal}>{populationStats ? `${populationStats.avg_age} yrs` : '—'}</Text>
          </View>
          <View style={styles.statBox}>
            {/* Citizen.salary is monthly (backend businesses pay 2,000-6,000/mo — see
                city_generator.py's BUSINESS_TEMPLATES) — not annual, so no lakhs
                conversion here; that would just misrepresent the real number. */}
            <Text style={styles.statLabel}>Median Income</Text>
            <Text style={[styles.statVal, { color: '#34d399' }]}>
              {populationStats ? `₹${Math.round(populationStats.median_income).toLocaleString('en-IN')}/mo` : '—'}
            </Text>
          </View>
          <View style={styles.statBox}>
            {/* No BMI concept in the simulation — avg citizen health is the real field
                every other health metric in this app is built on. */}
            <Text style={styles.statLabel}>Avg. Health</Text>
            <Text style={[styles.statVal, { color: '#38bdf8' }]}>
              {populationStats ? `${populationStats.avg_health_pct}%` : '—'}
            </Text>
          </View>
        </View>
      </View>

      {/* Search Box */}
      <View style={styles.searchBox}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search citizen by name, job, or district..."
          placeholderTextColor="#64748b"
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
      </View>

      {/* Occupation Pills */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.pillsScroll}>
        {occupations.map((occ) => (
          <TouchableOpacity
            key={occ}
            onPress={() => setFilterOcc(occ)}
            style={[styles.occPill, filterOcc === occ && styles.occPillActive]}
          >
            <Text style={[styles.occText, filterOcc === occ && styles.occTextActive]}>
              {occ === 'all' ? 'All Roles' : occ}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Citizens List */}
      <View style={styles.citizensList}>
        <View style={styles.listHeader}>
          <Text style={styles.listSub}>Sampled citizen dossiers</Text>
          <Text style={styles.listCount}>{filteredCitizens.length} Citizens</Text>
        </View>

        {filteredCitizens.map((citizen) => (
          <TouchableOpacity
            key={citizen.id}
            onPress={() => setSelectedCitizen(citizen)}
            style={styles.citizenCard}
          >
            <View style={styles.citizenProfile}>
              <View style={styles.avatarBox}>
                <Text style={styles.avatarText}>{citizen.avatar}</Text>
              </View>
              <View>
                <View style={styles.nameRow}>
                  <Text style={styles.citizenName}>{citizen.name}</Text>
                  <Text style={styles.citizenId}>#{citizen.id.replace('cit_', '')}</Text>
                </View>
                <Text style={styles.occupationText}>
                  {citizen.occupation} • <Text style={styles.incomeHighlight}>{citizen.income}</Text>
                </Text>
              </View>
            </View>

            <View style={styles.rightSide}>
              <Text style={styles.healthMeta}>{citizen.health.bp}</Text>
              <Text style={styles.arrowIcon}>➔</Text>
            </View>
          </TouchableOpacity>
        ))}
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
  bannerCard: {
    backgroundColor: 'rgba(8, 51, 68, 0.6)',
    borderRadius: 24,
    padding: 16,
    borderWidth: 1,
    borderColor: '#0e7490',
  },
  bannerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  bannerTag: {
    fontSize: 9,
    fontFamily: 'monospace',
    fontWeight: '800',
    color: '#38bdf8',
    letterSpacing: 0.8,
  },
  bannerHeading: {
    fontSize: 16,
    fontWeight: '900',
    color: '#ffffff',
    marginTop: 2,
  },
  bannerIconBox: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: '#083344',
    alignItems: 'center',
    justifyContent: 'center',
  },
  bannerIcon: {
    fontSize: 20,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 6,
    marginTop: 12,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: 'rgba(14, 116, 144, 0.4)',
  },
  statBox: {
    flex: 1,
    backgroundColor: '#090d16',
    borderRadius: 10,
    padding: 8,
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 9,
    color: '#94a3b8',
  },
  statVal: {
    fontSize: 12,
    fontWeight: '800',
    color: '#ffffff',
    fontFamily: 'monospace',
    marginTop: 2,
  },
  searchBox: {
    backgroundColor: '#0f172a',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#1e293b',
    paddingHorizontal: 12,
  },
  searchInput: {
    height: 44,
    color: '#ffffff',
    fontSize: 13,
  },
  pillsScroll: {
    flexDirection: 'row',
  },
  occPill: {
    backgroundColor: '#1e293b',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
    marginRight: 6,
    borderWidth: 1,
    borderColor: '#334155',
  },
  occPillActive: {
    backgroundColor: '#0891b2',
    borderColor: '#22d3ee',
  },
  occText: {
    fontSize: 11,
    color: '#94a3b8',
    fontWeight: '600',
  },
  occTextActive: {
    color: '#ffffff',
    fontWeight: '700',
  },
  citizensList: {
    gap: 8,
  },
  listHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  listSub: {
    fontSize: 11,
    color: '#94a3b8',
  },
  listCount: {
    fontSize: 11,
    fontWeight: '700',
    color: '#38bdf8',
    fontFamily: 'monospace',
  },
  citizenCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: 'rgba(15, 23, 42, 0.9)',
    borderRadius: 20,
    padding: 12,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  citizenProfile: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  avatarBox: {
    width: 42,
    height: 42,
    borderRadius: 12,
    backgroundColor: '#1e293b',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 20,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  citizenName: {
    fontSize: 13,
    fontWeight: '800',
    color: '#ffffff',
  },
  citizenId: {
    fontSize: 9,
    color: '#64748b',
    fontFamily: 'monospace',
  },
  occupationText: {
    fontSize: 11,
    color: '#94a3b8',
    marginTop: 2,
  },
  incomeHighlight: {
    color: '#34d399',
    fontWeight: '700',
    fontFamily: 'monospace',
  },
  rightSide: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  healthMeta: {
    fontSize: 11,
    color: '#94a3b8',
    fontFamily: 'monospace',
  },
  arrowIcon: {
    fontSize: 12,
    color: '#0891b2',
  },
});
