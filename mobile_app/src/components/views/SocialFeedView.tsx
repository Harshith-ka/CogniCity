import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput } from 'react-native';
import { Ionicons, Feather, MaterialCommunityIcons } from '@expo/vector-icons';
import { useApp } from '../../context/AppContext';
import { colors, typography, layout } from '../../constants/theme';

export const SocialFeedView: React.FC = () => {
  const { 
    socialPosts, 
    trendingTopics, 
    addSocialPost, 
    triggerTopic 
  } = useApp();

  const [postText, setPostText] = useState('');
  const [activeFilter, setActiveFilter] = useState<'all' | 'positive' | 'negative'>('all');
  const [newTopicHashtag, setNewTopicHashtag] = useState('');

  const filteredPosts = socialPosts.filter((p) => {
    if (activeFilter === 'all') return true;
    return p.sentiment === activeFilter;
  });

  const handleCreatePost = () => {
    if (!postText.trim()) return;
    addSocialPost(postText);
    setPostText('');
  };

  const handleBroadcastTopic = () => {
    if (!newTopicHashtag.trim()) return;
    const tag = newTopicHashtag.startsWith('#') ? newTopicHashtag : `#${newTopicHashtag}`;
    triggerTopic(tag, 'Citizen community pulse');
    setNewTopicHashtag('');
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {/* Trending Topics Carousel */}
      <View style={styles.section}>
        <Text style={styles.sectionHeading}>TRENDING IN CITIZEN CONVERSATIONS</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.trendingScroll}>
          {trendingTopics.map((topic, idx) => (
            <TouchableOpacity key={idx} style={styles.topicCard} activeOpacity={0.7}>
              <View style={styles.topicHeader}>
                <Text style={styles.topicHashtag}>{topic.hashtag}</Text>
                <Text style={styles.topicCategory}>{topic.category.toUpperCase()}</Text>
              </View>
              <Text style={styles.topicSummary} numberOfLines={1}>{topic.topic}</Text>
              <Text style={styles.topicMentions}>{topic.mentions.toLocaleString()} citizen mentions</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Broadcast Topic Drawer */}
      <View style={styles.broadcastBox}>
        <Feather name="hash" size={14} color={colors.textMuted} style={{ marginLeft: 6 }} />
        <TextInput
          style={styles.broadcastInput}
          placeholder="Inject new hashtag (e.g. #MetroLine4)..."
          placeholderTextColor={colors.textMuted}
          value={newTopicHashtag}
          onChangeText={setNewTopicHashtag}
        />
        <TouchableOpacity onPress={handleBroadcastTopic} style={styles.broadcastBtn} activeOpacity={0.7}>
          <Text style={styles.broadcastBtnText}>Trend</Text>
        </TouchableOpacity>
      </View>

      {/* Post Composer */}
      <View style={styles.composerCard}>
        <TextInput
          style={styles.composerInput}
          placeholder="Broadcast municipal announcement or policy statement..."
          placeholderTextColor={colors.textMuted}
          multiline
          value={postText}
          onChangeText={setPostText}
        />
        <View style={styles.composerFooter}>
          <Text style={styles.composerHint}>Real-time citizen sentiment analysis active</Text>
          <TouchableOpacity onPress={handleCreatePost} style={styles.postBtn} activeOpacity={0.7}>
            <Feather name="send" size={12} color="#ffffff" style={{ marginRight: 4 }} />
            <Text style={styles.postBtnText}>Publish</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Sentiment Filter Tabs */}
      <View style={styles.filterRow}>
        {(['all', 'positive', 'negative'] as const).map((f) => (
          <TouchableOpacity
            key={f}
            onPress={() => setActiveFilter(f)}
            style={[styles.filterPill, activeFilter === f && styles.filterPillActive]}
            activeOpacity={0.7}
          >
            <Text style={[styles.filterText, activeFilter === f && styles.filterTextActive]}>
              {f === 'all' ? 'All Pulse' : f === 'positive' ? 'Supportive' : 'Critical Concerns'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Social Posts Stream */}
      <View style={styles.postsList}>
        {filteredPosts.map((post) => {
          const isPositive = post.sentiment === 'positive';
          return (
            <View key={post.id} style={styles.postCard}>
              <View style={styles.postHeader}>
                <View style={styles.authorProfile}>
                  <View style={styles.avatarBox}>
                    <Feather name="user" size={14} color={colors.textSecondary} />
                  </View>
                  <View>
                    <Text style={styles.authorName}>{post.authorName}</Text>
                    <Text style={styles.authorHandle}>{post.authorHandle} • {post.timestamp}</Text>
                  </View>
                </View>

                <View style={[styles.sentimentTag, isPositive ? styles.sentPos : styles.sentNeg]}>
                  <Text style={[styles.sentText, isPositive ? styles.textPos : styles.textNeg]}>
                    {(post.sentimentScore * 100).toFixed(0)}% {post.sentiment}
                  </Text>
                </View>
              </View>

              <Text style={styles.postContent}>{post.content}</Text>

              {/* Hashtags */}
              <View style={styles.hashtagsRow}>
                {post.hashtags.map((tag, idx) => (
                  <Text key={idx} style={styles.hashText}>#{tag}</Text>
                ))}
              </View>

              {/* Post Engagement Row */}
              <View style={styles.engagementRow}>
                <View style={styles.engItemRow}>
                  <Ionicons name="heart-outline" size={13} color={colors.textMuted} />
                  <Text style={styles.engItem}>{post.likes}</Text>
                </View>
                <View style={styles.engItemRow}>
                  <Feather name="repeat" size={12} color={colors.textMuted} />
                  <Text style={styles.engItem}>{post.retweets}</Text>
                </View>
                <View style={styles.engItemRow}>
                  <Feather name="message-circle" size={12} color={colors.textMuted} />
                  <Text style={styles.engItem}>{post.commentsCount} replies</Text>
                </View>
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
    backgroundColor: colors.background,
  },
  contentContainer: {
    padding: layout.padding,
    paddingBottom: 30,
    gap: 12,
  },
  section: {
    gap: 8,
  },
  sectionHeading: {
    ...typography.badge,
    color: colors.textMuted,
  },
  trendingScroll: {
    flexDirection: 'row',
  },
  topicCard: {
    backgroundColor: colors.surface,
    borderRadius: layout.radiusMd,
    padding: 10,
    marginRight: 8,
    width: 190,
    borderWidth: 1,
    borderColor: colors.border,
  },
  topicHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  topicHashtag: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.primaryLight,
    fontFamily: 'monospace',
  },
  topicCategory: {
    fontSize: 7.5,
    fontFamily: 'monospace',
    color: colors.textMuted,
  },
  topicSummary: {
    fontSize: 10.5,
    color: colors.textPrimary,
    fontWeight: '600',
  },
  topicMentions: {
    fontSize: 8.5,
    fontFamily: 'monospace',
    color: colors.successLight,
    marginTop: 4,
  },
  broadcastBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: layout.radiusMd,
    padding: 4,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 6,
  },
  broadcastInput: {
    flex: 1,
    paddingHorizontal: 8,
    color: colors.textPrimary,
    fontSize: 11,
  },
  broadcastBtn: {
    backgroundColor: colors.primary,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: layout.radiusSm,
  },
  broadcastBtnText: {
    color: '#ffffff',
    fontSize: 10.5,
    fontWeight: '700',
  },
  composerCard: {
    backgroundColor: colors.surface,
    borderRadius: layout.radiusLg,
    padding: 12,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 8,
  },
  composerInput: {
    backgroundColor: colors.surfaceElevated,
    borderRadius: layout.radiusSm,
    padding: 10,
    color: colors.textPrimary,
    fontSize: 11.5,
    minHeight: 48,
    textAlignVertical: 'top',
    borderWidth: 1,
    borderColor: colors.border,
  },
  composerFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  composerHint: {
    ...typography.caption,
  },
  postBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primary,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: layout.radiusSm,
  },
  postBtnText: {
    color: '#ffffff',
    fontSize: 11,
    fontWeight: '700',
  },
  filterRow: {
    flexDirection: 'row',
    gap: 6,
  },
  filterPill: {
    backgroundColor: colors.surface,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: layout.radiusSm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  filterPillActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primaryLight,
  },
  filterText: {
    fontSize: 10,
    color: colors.textMuted,
    fontWeight: '600',
  },
  filterTextActive: {
    color: '#ffffff',
    fontWeight: '700',
  },
  postsList: {
    gap: 8,
  },
  postCard: {
    backgroundColor: colors.surface,
    borderRadius: layout.radiusMd,
    padding: 12,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 8,
  },
  postHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  authorProfile: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  avatarBox: {
    width: 28,
    height: 28,
    borderRadius: 7,
    backgroundColor: colors.surfaceElevated,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  authorName: {
    ...typography.bodyBold,
  },
  authorHandle: {
    ...typography.caption,
  },
  sentimentTag: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  sentPos: {
    backgroundColor: colors.successGlow,
  },
  sentNeg: {
    backgroundColor: colors.warningGlow,
  },
  sentText: {
    fontSize: 8.5,
    fontFamily: 'monospace',
    fontWeight: '700',
  },
  textPos: {
    color: colors.successLight,
  },
  textNeg: {
    color: colors.warningLight,
  },
  postContent: {
    ...typography.body,
  },
  hashtagsRow: {
    flexDirection: 'row',
    gap: 6,
  },
  hashText: {
    fontSize: 9.5,
    color: colors.primaryLight,
    fontFamily: 'monospace',
    fontWeight: '700',
  },
  engagementRow: {
    flexDirection: 'row',
    gap: 14,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: 6,
  },
  engItemRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  engItem: {
    ...typography.caption,
  },
});
