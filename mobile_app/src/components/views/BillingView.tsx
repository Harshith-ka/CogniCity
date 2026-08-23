import React, { useEffect, useRef, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useApp } from '../../context/AppContext';
import { api } from '../../services/api';

export const BillingView: React.FC = () => {
  const { billing, currentOrg, buyCredits, upgradePlan } = useApp();
  const [isTopUpOpen, setIsTopUpOpen] = useState(false);
  const [isPlansOpen, setIsPlansOpen] = useState(false);
  const [plans, setPlans] = useState<any[]>([]);
  const [subscribingKey, setSubscribingKey] = useState<string | null>(null);
  const isSubscribingRef = useRef(false); // synchronous double-tap guard, see AuthModal.tsx

  useEffect(() => {
    api.listPlans().then(setPlans);
  }, []);

  const handleSubscribe = async (planKey: string) => {
    if (isSubscribingRef.current) return;
    isSubscribingRef.current = true;
    setSubscribingKey(planKey);
    try {
      await upgradePlan(planKey);
      setIsPlansOpen(false);
    } finally {
      isSubscribingRef.current = false;
      setSubscribingKey(null);
    }
  };

  const creditPacks = [
    { amount: 10000, priceInr: 499, popular: false },
    { amount: 50000, priceInr: 1999, popular: true },
    { amount: 150000, priceInr: 4999, popular: false },
  ];

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.headerBox}>
        <View style={styles.titleRow}>
          <Text style={styles.headerTitle}>Credits & Billing</Text>
          <Text style={styles.badgeText}>{billing.planName}</Text>
        </View>
        <Text style={styles.headerSubtitle}>Simulation compute budget & monthly quota</Text>
      </View>

      {/* Credit Balance Card */}
      <View style={styles.balanceCard}>
        <View style={styles.balanceTop}>
          <Text style={styles.balanceTag}>AVAILABLE COMPUTE CREDITS</Text>
          <View style={styles.activePill}>
            <Text style={styles.activePillText}>Active Quota</Text>
          </View>
        </View>

        <Text style={styles.balanceNumber}>{billing.availableCredits.toLocaleString()}</Text>
        <Text style={styles.remainingSub}>
          Estimated ~{billing.estimatedRemainingSims} full-scale simulations remaining
        </Text>

        <View style={styles.quotaBarBox}>
          <View style={styles.quotaLabelRow}>
            <Text style={styles.quotaKey}>Used this month</Text>
            <Text style={styles.quotaVal}>{billing.usedThisMonth.toLocaleString()} credits</Text>
          </View>
          <View style={styles.barBg}>
            <View
              style={[
                styles.barFill,
                { width: `${(billing.usedThisMonth / (billing.availableCredits + billing.usedThisMonth)) * 100}%` },
              ]}
            />
          </View>
        </View>

        <View style={styles.balanceActions}>
          <TouchableOpacity
            onPress={() => setIsTopUpOpen(!isTopUpOpen)}
            style={styles.buyCreditsBtn}
          >
            <Text style={styles.buyCreditsText}>+ Buy Credits</Text>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={() => setIsPlansOpen(!isPlansOpen)}
            style={styles.upgradeBtn}
          >
            <Text style={styles.upgradeText}>✨ Upgrade Plan</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Plan Picker Drawer if open */}
      {isPlansOpen && (
        <View style={styles.topUpCard}>
          <Text style={styles.topUpTitle}>Available Plans</Text>
          <View style={styles.packsList}>
            {plans.length === 0 && (
              <Text style={{ color: '#94a3b8', fontSize: 11 }}>Loading plans…</Text>
            )}
            {plans.map((plan) => {
              const isCurrent = plan.key === currentOrg?.plan_key;
              return (
                <View key={plan.key} style={styles.packItem}>
                  <View>
                    <View style={styles.packTitleRow}>
                      <Text style={styles.packAmount}>{plan.name}</Text>
                      {isCurrent && <Text style={styles.popularTag}>CURRENT</Text>}
                    </View>
                    <Text style={styles.packSub}>
                      {plan.monthly_price_inr == null ? 'Custom pricing' : `₹${plan.monthly_price_inr}/mo`} · {plan.included_credits.toLocaleString()} credits
                    </Text>
                  </View>
                  {!isCurrent && (
                    <TouchableOpacity
                      onPress={() => handleSubscribe(plan.key)}
                      disabled={subscribingKey !== null}
                      style={[styles.buyPackBtn, subscribingKey !== null && { opacity: 0.5 }]}
                    >
                      <Text style={styles.buyPackText}>{subscribingKey === plan.key ? 'Subscribing…' : 'Subscribe'}</Text>
                    </TouchableOpacity>
                  )}
                </View>
              );
            })}
          </View>
        </View>
      )}

      {/* Top Up Drawer if open */}
      {isTopUpOpen && (
        <View style={styles.topUpCard}>
          <Text style={styles.topUpTitle}>Purchase Credit Package</Text>
          <View style={styles.packsList}>
            {creditPacks.map((pack, idx) => (
              <View key={idx} style={styles.packItem}>
                <View>
                  <View style={styles.packTitleRow}>
                    <Text style={styles.packAmount}>+{pack.amount.toLocaleString()} Credits</Text>
                    {pack.popular && <Text style={styles.popularTag}>POPULAR</Text>}
                  </View>
                  <Text style={styles.packSub}>Instant cloud provisioning</Text>
                </View>
                <TouchableOpacity
                  onPress={() => {
                    buyCredits(pack.amount, pack.priceInr);
                    setIsTopUpOpen(false);
                  }}
                  style={styles.buyPackBtn}
                >
                  <Text style={styles.buyPackText}>₹{pack.priceInr}</Text>
                </TouchableOpacity>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Transactions History */}
      <View style={styles.historySection}>
        <Text style={styles.historyHeading}>USAGE HISTORY</Text>
        <View style={styles.txList}>
          {billing.transactions.map((tx) => (
            <View key={tx.id} style={styles.txCard}>
              <View style={styles.txLeft}>
                <View style={[styles.txIconBox, tx.type === 'credit' ? styles.txCreditIcon : styles.txDebitIcon]}>
                  <Text style={styles.txEmoji}>⚡</Text>
                </View>
                <View>
                  <Text style={styles.txDesc} numberOfLines={1}>{tx.description}</Text>
                  <Text style={styles.txDate}>{tx.date}</Text>
                </View>
              </View>

              <Text style={[styles.txAmount, tx.type === 'credit' ? styles.amountGreen : styles.amountMuted]}>
                {tx.amount > 0 ? `+${tx.amount.toLocaleString()}` : tx.amount.toLocaleString()}
              </Text>
            </View>
          ))}
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
    color: '#a5b4fc',
    backgroundColor: '#1e1b4b',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  headerSubtitle: {
    fontSize: 11,
    color: '#94a3b8',
    marginTop: 2,
  },
  balanceCard: {
    backgroundColor: 'rgba(15, 23, 42, 0.9)',
    borderRadius: 24,
    padding: 16,
    borderWidth: 1,
    borderColor: '#312e81',
  },
  balanceTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  balanceTag: {
    fontSize: 9,
    fontFamily: 'monospace',
    fontWeight: '800',
    color: '#818cf8',
    letterSpacing: 0.8,
  },
  activePill: {
    backgroundColor: 'rgba(6, 78, 59, 0.5)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  activePillText: {
    fontSize: 9,
    fontWeight: '700',
    color: '#34d399',
  },
  balanceNumber: {
    fontSize: 28,
    fontWeight: '900',
    color: '#ffffff',
    fontFamily: 'monospace',
    marginTop: 6,
  },
  remainingSub: {
    fontSize: 11,
    color: '#94a3b8',
    marginTop: 2,
  },
  quotaBarBox: {
    marginTop: 12,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#1e293b',
  },
  quotaLabelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  quotaKey: {
    fontSize: 11,
    color: '#94a3b8',
  },
  quotaVal: {
    fontSize: 11,
    fontWeight: '700',
    color: '#a5b4fc',
    fontFamily: 'monospace',
  },
  barBg: {
    height: 6,
    backgroundColor: '#1e293b',
    borderRadius: 3,
    overflow: 'hidden',
  },
  barFill: {
    height: 6,
    backgroundColor: '#6366f1',
    borderRadius: 3,
  },
  balanceActions: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 14,
  },
  buyCreditsBtn: {
    flex: 1,
    backgroundColor: '#4f46e5',
    paddingVertical: 12,
    borderRadius: 14,
    alignItems: 'center',
  },
  buyCreditsText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '800',
  },
  upgradeBtn: {
    backgroundColor: '#1e293b',
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#334155',
    alignItems: 'center',
  },
  upgradeText: {
    color: '#fbbf24',
    fontSize: 12,
    fontWeight: '700',
  },
  topUpCard: {
    backgroundColor: '#0f172a',
    borderRadius: 20,
    padding: 14,
    borderWidth: 1,
    borderColor: '#4f46e5',
  },
  topUpTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#ffffff',
    marginBottom: 10,
  },
  packsList: {
    gap: 8,
  },
  packItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#1e293b',
    borderRadius: 12,
    padding: 10,
  },
  packTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  packAmount: {
    fontSize: 12,
    fontWeight: '800',
    color: '#ffffff',
    fontFamily: 'monospace',
  },
  popularTag: {
    fontSize: 8,
    fontFamily: 'monospace',
    color: '#fcd34d',
    backgroundColor: '#78350f',
    paddingHorizontal: 4,
    paddingVertical: 1,
    borderRadius: 4,
  },
  packSub: {
    fontSize: 9,
    color: '#94a3b8',
    marginTop: 1,
  },
  buyPackBtn: {
    backgroundColor: '#059669',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  buyPackText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#ffffff',
  },
  historySection: {
    marginTop: 4,
  },
  historyHeading: {
    fontSize: 11,
    fontWeight: '800',
    color: '#94a3b8',
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  txList: {
    gap: 6,
  },
  txCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: 'rgba(15, 23, 42, 0.9)',
    borderRadius: 16,
    padding: 12,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  txLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
  },
  txIconBox: {
    width: 32,
    height: 32,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  txCreditIcon: {
    backgroundColor: 'rgba(6, 78, 59, 0.5)',
  },
  txDebitIcon: {
    backgroundColor: '#1e293b',
  },
  txEmoji: {
    fontSize: 14,
  },
  txDesc: {
    fontSize: 11,
    fontWeight: '700',
    color: '#ffffff',
  },
  txDate: {
    fontSize: 9,
    color: '#64748b',
    fontFamily: 'monospace',
    marginTop: 1,
  },
  txAmount: {
    fontSize: 12,
    fontWeight: '800',
    fontFamily: 'monospace',
  },
  amountGreen: {
    color: '#34d399',
  },
  amountMuted: {
    color: '#cbd5e1',
  },
});
