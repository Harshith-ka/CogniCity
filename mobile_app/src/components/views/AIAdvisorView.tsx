import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, ActivityIndicator } from 'react-native';
import { Ionicons, Feather, MaterialCommunityIcons } from '@expo/vector-icons';
import { useApp } from '../../context/AppContext';
import { colors, typography, layout } from '../../constants/theme';

export const AIAdvisorView: React.FC = () => {
  const { aiAdvisor, queryAIAdvisor } = useApp();
  const [questionInput, setQuestionInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState<Array<{ sender: 'user' | 'advisor'; text: string; time: string }>>([
    {
      sender: 'advisor',
      text: `City telemetry synchronized. Municipal stability index is at ${aiAdvisor.healthIndex}%. Ready to evaluate policy proposals, carbon offsets, or budget allocations.`,
      time: '14:30',
    },
  ]);

  const presetQueries = [
    'Analyze ICU Bed Shortage Solutions',
    'Simulate Carbon Tax on Heavy Freight',
    'Assess Impact of Metro Line 4 Completion',
    'Optimize Peak Grid Load in Tech Park',
  ];

  const handleSendQuestion = async (queryText?: string) => {
    const prompt = queryText || questionInput;
    if (!prompt.trim() || isLoading) return;

    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setChatHistory((prev) => [...prev, { sender: 'user', text: prompt, time: timeStr }]);
    if (!queryText) setQuestionInput('');
    setIsLoading(true);

    const response = await queryAIAdvisor(prompt);
    setIsLoading(false);

    setChatHistory((prev) => [
      ...prev,
      { sender: 'advisor', text: response, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) },
    ]);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {/* City Stability Diagnostic Card */}
      <View style={styles.radarCard}>
        <View style={styles.radarTop}>
          <View style={styles.radarTitleRow}>
            <View style={styles.iconBox}>
              <Feather name="cpu" size={18} color={colors.primaryLight} />
            </View>
            <View>
              <Text style={styles.radarTag}>NEURAL SIMULATION ENGINE</Text>
              <Text style={styles.radarTitle}>Municipal Diagnostic Radar</Text>
            </View>
          </View>
          <View style={styles.healthPill}>
            <Text style={styles.healthScoreText}>{aiAdvisor.healthIndex}%</Text>
          </View>
        </View>

        {/* 3 Metric Scores */}
        <View style={styles.scoresGrid}>
          <View style={styles.scoreBox}>
            <View style={styles.scoreHeader}>
              <Feather name="trending-up" size={11} color={colors.successLight} />
              <Text style={styles.scoreLabel}>Economy</Text>
            </View>
            <Text style={[styles.scoreVal, { color: colors.successLight }]}>{aiAdvisor.economicStability}%</Text>
          </View>

          <View style={styles.scoreBox}>
            <View style={styles.scoreHeader}>
              <Feather name="shield" size={11} color={colors.cyanLight} />
              <Text style={styles.scoreLabel}>Public Safety</Text>
            </View>
            <Text style={[styles.scoreVal, { color: colors.cyanLight }]}>{aiAdvisor.safetyScore}%</Text>
          </View>

          <View style={styles.scoreBox}>
            <View style={styles.scoreHeader}>
              <Feather name="zap" size={11} color={colors.purpleLight} />
              <Text style={styles.scoreLabel}>Carbon Index</Text>
            </View>
            <Text style={[styles.scoreVal, { color: colors.purpleLight }]}>
              {aiAdvisor.carbonScore === null ? 'N/A' : `${aiAdvisor.carbonScore}%`}
            </Text>
          </View>
        </View>

        <Text style={styles.summaryText}>{aiAdvisor.summary}</Text>
      </View>

      {/* Recommended Policies */}
      <View style={styles.section}>
        <Text style={styles.sectionHeading}>RECOMMENDED POLICY INTERVENTIONS</Text>
        {aiAdvisor.recommendedPolicies.length === 0 && (
          <Text style={styles.summaryText}>No issues flagged against current city metrics.</Text>
        )}
        {aiAdvisor.recommendedPolicies.map((p, idx) => (
          <View key={idx} style={styles.policyCard}>
            <View style={styles.policyHeader}>
              <View style={styles.policyTitleRow}>
                <Feather name="compass" size={14} color={colors.primaryLight} />
                <Text style={styles.policyTitle}>{p.issue}</Text>
              </View>
              <Text style={styles.policyCost}>{p.severity.toUpperCase()}</Text>
            </View>
            <Text style={styles.policyImpact}>{p.recommendation}</Text>
            <View style={styles.policyFooter}>
              <Text style={styles.roiText}>Expected impact: <Text style={styles.roiHighlight}>{p.expectedImpact}</Text></Text>
              <TouchableOpacity
                onPress={() => handleSendQuestion(`Simulate implementation of: ${p.recommendation}`)}
                style={styles.simulateBtn}
                activeOpacity={0.7}
              >
                <Text style={styles.simulateBtnText}>Simulate ➔</Text>
              </TouchableOpacity>
            </View>
          </View>
        ))}
      </View>

      {/* Quick Simulation Queries */}
      <View style={styles.section}>
        <Text style={styles.sectionHeading}>QUICK SCENARIO PROMPTS</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.presetsScroll}>
          {presetQueries.map((q, idx) => (
            <TouchableOpacity
              key={idx}
              onPress={() => handleSendQuestion(q)}
              style={styles.presetChip}
              activeOpacity={0.7}
            >
              <Text style={styles.presetChipText}>{q}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Chat Thread */}
      <View style={styles.chatSection}>
        <Text style={styles.sectionHeading}>INTERACTIVE POLICY COPILOT</Text>
        <View style={styles.chatThread}>
          {chatHistory.map((msg, idx) => {
            const isUser = msg.sender === 'user';
            return (
              <View key={idx} style={[styles.msgContainer, isUser ? styles.msgRight : styles.msgLeft]}>
                <View style={[styles.msgBubble, isUser ? styles.userBubble : styles.advisorBubble]}>
                  <Text style={[styles.msgText, isUser ? styles.userMsgText : styles.advisorMsgText]}>
                    {msg.text}
                  </Text>
                  <Text style={styles.msgTime}>{msg.time}</Text>
                </View>
              </View>
            );
          })}

          {isLoading && (
            <View style={styles.loadingBox}>
              <ActivityIndicator color={colors.primaryLight} size="small" />
              <Text style={styles.loadingText}>Simulating policy outcomes across 10,000 citizens...</Text>
            </View>
          )}
        </View>

        {/* Input Bar */}
        <View style={styles.inputRow}>
          <TextInput
            style={styles.chatInput}
            placeholder="Ask scenario question..."
            placeholderTextColor={colors.textMuted}
            value={questionInput}
            onChangeText={setQuestionInput}
          />
          <TouchableOpacity onPress={() => handleSendQuestion()} style={styles.sendBtn} activeOpacity={0.7}>
            <Feather name="arrow-up" size={16} color="#ffffff" />
          </TouchableOpacity>
        </View>
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
  radarCard: {
    backgroundColor: colors.surface,
    borderRadius: layout.radiusLg,
    padding: layout.cardPadding,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 12,
  },
  radarTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  radarTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  iconBox: {
    width: 36,
    height: 36,
    borderRadius: layout.radiusSm,
    backgroundColor: colors.primaryGlow,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(99, 102, 241, 0.25)',
  },
  radarTag: {
    ...typography.badge,
    color: colors.primaryLight,
  },
  radarTitle: {
    ...typography.h2,
    marginTop: 2,
  },
  healthPill: {
    backgroundColor: colors.successGlow,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: layout.radiusSm,
    borderWidth: 1,
    borderColor: 'rgba(16, 185, 129, 0.25)',
  },
  healthScoreText: {
    ...typography.numberMedium,
    color: colors.successLight,
  },
  scoresGrid: {
    flexDirection: 'row',
    gap: 8,
  },
  scoreBox: {
    flex: 1,
    backgroundColor: colors.surfaceElevated,
    borderRadius: layout.radiusMd,
    padding: 10,
    borderWidth: 1,
    borderColor: colors.border,
  },
  scoreHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  scoreLabel: {
    ...typography.caption,
  },
  scoreVal: {
    ...typography.numberMedium,
    marginTop: 4,
  },
  summaryText: {
    ...typography.body,
  },
  section: {
    gap: 8,
  },
  sectionHeading: {
    ...typography.badge,
    color: colors.textMuted,
  },
  policyCard: {
    backgroundColor: colors.surface,
    borderRadius: layout.radiusMd,
    padding: 12,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 6,
  },
  policyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  policyTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    flex: 1,
  },
  policyTitle: {
    ...typography.bodyBold,
  },
  policyCost: {
    ...typography.numberMedium,
    fontSize: 12,
    color: colors.warningLight,
  },
  policyImpact: {
    ...typography.body,
  },
  policyFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: 6,
  },
  roiText: {
    ...typography.caption,
  },
  roiHighlight: {
    color: colors.successLight,
    fontWeight: '700',
  },
  simulateBtn: {
    backgroundColor: colors.primary,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: layout.radiusSm,
  },
  simulateBtnText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#ffffff',
  },
  presetsScroll: {
    flexDirection: 'row',
  },
  presetChip: {
    backgroundColor: colors.surfaceElevated,
    paddingHorizontal: 10,
    paddingVertical: 7,
    borderRadius: layout.radiusSm,
    marginRight: 6,
    borderWidth: 1,
    borderColor: colors.border,
  },
  presetChipText: {
    fontSize: 10.5,
    color: colors.textSecondary,
    fontWeight: '600',
  },
  chatSection: {
    gap: 8,
    marginTop: 4,
  },
  chatThread: {
    gap: 8,
  },
  msgContainer: {
    flexDirection: 'row',
  },
  msgLeft: {
    justifyContent: 'flex-start',
  },
  msgRight: {
    justifyContent: 'flex-end',
  },
  msgBubble: {
    maxWidth: '85%',
    padding: 12,
    borderRadius: layout.radiusMd,
  },
  userBubble: {
    backgroundColor: colors.primary,
    borderBottomRightRadius: 2,
  },
  advisorBubble: {
    backgroundColor: colors.surfaceElevated,
    borderBottomLeftRadius: 2,
    borderWidth: 1,
    borderColor: colors.border,
  },
  msgText: {
    fontSize: 12,
    lineHeight: 17,
  },
  userMsgText: {
    color: '#ffffff',
  },
  advisorMsgText: {
    color: colors.textPrimary,
  },
  msgTime: {
    fontSize: 8,
    color: colors.textMuted,
    alignSelf: 'flex-end',
    marginTop: 4,
  },
  loadingBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 8,
  },
  loadingText: {
    fontSize: 10,
    color: colors.primaryLight,
    fontStyle: 'italic',
  },
  inputRow: {
    flexDirection: 'row',
    backgroundColor: colors.surface,
    borderRadius: layout.radiusMd,
    padding: 4,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 6,
  },
  chatInput: {
    flex: 1,
    paddingHorizontal: 10,
    paddingVertical: 8,
    color: colors.textPrimary,
    fontSize: 12,
  },
  sendBtn: {
    backgroundColor: colors.primary,
    width: 34,
    height: 34,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
