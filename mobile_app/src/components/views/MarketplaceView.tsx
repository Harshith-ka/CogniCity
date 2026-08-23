import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput } from 'react-native';
import { useApp } from '../../context/AppContext';

export const MarketplaceView: React.FC = () => {
  const { marketplace, installMarketItem } = useApp();
  const [activeMarketTab, setActiveMarketTab] = useState<'all' | 'simulations' | 'agents'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredItems = marketplace.filter((item) => {
    const matchesTab = activeMarketTab === 'all' ||
      (activeMarketTab === 'simulations' && item.type === 'simulation') ||
      (activeMarketTab === 'agents' && item.type === 'agent');
    const matchesSearch = item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesTab && matchesSearch;
  });

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.headerBox}>
        <View style={styles.titleRow}>
          <Text style={styles.headerTitle}>Twin & Agent Store</Text>
          <Text style={styles.badgeText}>VERIFIED MODELS</Text>
        </View>
        <Text style={styles.headerSubtitle}>Install pre-calibrated environments & verified AI models</Text>
      </View>

      {/* Tabs */}
      <View style={styles.tabsRow}>
        {[
          { id: 'all', label: 'All Items' },
          { id: 'simulations', label: '🌍 Twins' },
          { id: 'agents', label: '🤖 Agents' },
        ].map((tab) => (
          <TouchableOpacity
            key={tab.id}
            onPress={() => setActiveMarketTab(tab.id as any)}
            style={[styles.tabBtn, activeMarketTab === tab.id && styles.tabBtnActive]}
          >
            <Text style={[styles.tabBtnText, activeMarketTab === tab.id && styles.tabBtnTextActive]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Search Input */}
      <View style={styles.searchBox}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search environments, models, tags..."
          placeholderTextColor="#64748b"
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
      </View>

      {/* Items List */}
      <View style={styles.itemsList}>
        {filteredItems.map((item) => {
          const isSim = item.type === 'simulation';
          return (
            <View key={item.id} style={styles.itemCard}>
              <View style={styles.cardHeader}>
                <View style={styles.itemProfile}>
                  <View style={[styles.iconBox, isSim ? styles.simIconBg : styles.agentIconBg]}>
                    <Text style={styles.iconEmoji}>{isSim ? '🌍' : '🤖'}</Text>
                  </View>
                  <View style={styles.itemMeta}>
                    <View style={styles.titleBadgeRow}>
                      <Text style={styles.itemTitle}>{item.title}</Text>
                      {item.badge && <Text style={styles.itemBadge}>{item.badge.toUpperCase()}</Text>}
                    </View>
                    <Text style={styles.authorText}>by {item.author}</Text>
                  </View>
                </View>

                <View style={styles.ratingBox}>
                  <Text style={styles.ratingText}>⭐ {item.rating}</Text>
                  <Text style={styles.reviewsText}>{item.reviewsCount} reviews</Text>
                </View>
              </View>

              <Text style={styles.description} numberOfLines={2}>{item.description}</Text>

              <View style={styles.tagsRow}>
                {item.tags.map((tag, idx) => (
                  <View key={idx} style={styles.tagPill}>
                    <Text style={styles.tagText}>#{tag}</Text>
                  </View>
                ))}
              </View>

              <View style={styles.cardFooter}>
                <View>
                  <Text style={styles.priceLabel}>Pricing</Text>
                  <Text style={styles.priceValue}>{item.price}</Text>
                </View>

                <TouchableOpacity
                  onPress={() => installMarketItem(item.id)}
                  style={[styles.installBtn, item.installed && styles.installedBtn]}
                >
                  <Text style={[styles.installBtnText, item.installed && styles.installedBtnText]}>
                    {item.installed ? '✓ Installed' : 'Install'}
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          );
        })}
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
  headerBox: {
    marginBottom: 2,
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
  badgeText: {
    fontSize: 9,
    fontFamily: 'monospace',
    fontWeight: '800',
    color: '#f472b6',
    backgroundColor: '#500724',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  headerSubtitle: {
    fontSize: 11,
    color: '#94a3b8',
    marginTop: 2,
  },
  tabsRow: {
    flexDirection: 'row',
    backgroundColor: '#0f172a',
    borderRadius: 14,
    padding: 4,
    borderWidth: 1,
    borderColor: '#1e293b',
    gap: 6,
  },
  tabBtn: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 10,
    alignItems: 'center',
  },
  tabBtnActive: {
    backgroundColor: '#4f46e5',
  },
  tabBtnText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#94a3b8',
  },
  tabBtnTextActive: {
    color: '#ffffff',
  },
  searchBox: {
    backgroundColor: '#0f172a',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#1e293b',
    paddingHorizontal: 12,
  },
  searchInput: {
    height: 42,
    color: '#ffffff',
    fontSize: 13,
  },
  itemsList: {
    gap: 10,
  },
  itemCard: {
    backgroundColor: 'rgba(15, 23, 42, 0.9)',
    borderRadius: 24,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  itemProfile: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  iconBox: {
    width: 44,
    height: 44,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  simIconBg: {
    backgroundColor: '#1e1b4b',
    borderWidth: 1,
    borderColor: '#4338ca',
  },
  agentIconBg: {
    backgroundColor: '#3b0764',
    borderWidth: 1,
    borderColor: '#7e22ce',
  },
  iconEmoji: {
    fontSize: 22,
  },
  itemMeta: {
    flex: 1,
  },
  titleBadgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  itemTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#ffffff',
    flex: 1,
  },
  itemBadge: {
    fontSize: 8,
    fontFamily: 'monospace',
    fontWeight: '800',
    color: '#f472b6',
    backgroundColor: '#500724',
    paddingHorizontal: 4,
    paddingVertical: 2,
    borderRadius: 4,
  },
  authorText: {
    fontSize: 10,
    color: '#94a3b8',
    marginTop: 1,
  },
  ratingBox: {
    alignItems: 'flex-end',
  },
  ratingText: {
    fontSize: 12,
    fontWeight: '800',
    color: '#fbbf24',
  },
  reviewsText: {
    fontSize: 9,
    color: '#64748b',
    fontFamily: 'monospace',
  },
  description: {
    fontSize: 11,
    color: '#cbd5e1',
    marginTop: 8,
    lineHeight: 15,
  },
  tagsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 4,
    marginTop: 8,
  },
  tagPill: {
    backgroundColor: '#090d16',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  tagText: {
    fontSize: 9,
    fontFamily: 'monospace',
    color: '#94a3b8',
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#1e293b',
    marginTop: 10,
    paddingTop: 8,
  },
  priceLabel: {
    fontSize: 9,
    color: '#64748b',
  },
  priceValue: {
    fontSize: 13,
    fontWeight: '800',
    color: '#34d399',
    fontFamily: 'monospace',
  },
  installBtn: {
    backgroundColor: '#4f46e5',
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 10,
  },
  installedBtn: {
    backgroundColor: 'rgba(6, 78, 59, 0.6)',
    borderWidth: 1,
    borderColor: '#065f46',
  },
  installBtnText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#ffffff',
  },
  installedBtnText: {
    color: '#34d399',
  },
});
