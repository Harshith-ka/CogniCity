import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput } from 'react-native';
import { useApp } from '../../context/AppContext';
import { TeamMember } from '../../types';

export const CollaborationView: React.FC = () => {
  const { team, inviteTeamMember, showToast } = useApp();
  const [inviteEmail, setInviteEmail] = useState('');
  const [commentInput, setCommentInput] = useState('');
  const [comments, setComments] = useState([
    {
      id: 'c1',
      author: 'Dr. Priya Sharma',
      avatar: '👩🔬',
      text: 'ICU triage agent v2.1 reached 93.1% accuracy. Reviewing bed diversion thresholds.',
      time: '10 mins ago',
    },
    {
      id: 'c2',
      author: 'Arjun Sen',
      avatar: '👨💻',
      text: 'Pushed RL checkpoint with adjusted reward weighting for rush hour pedestrian safety.',
      time: '25 mins ago',
    },
  ]);

  const handleInvite = () => {
    if (!inviteEmail.trim()) return;
    inviteTeamMember(inviteEmail, 'Researcher');
    setInviteEmail('');
  };

  const handlePostComment = () => {
    if (!commentInput.trim()) return;
    setComments([
      {
        id: 'c_' + Date.now(),
        author: 'You (Researcher)',
        avatar: '👨🔬',
        text: commentInput,
        time: 'Just now',
      },
      ...comments,
    ]);
    setCommentInput('');
    showToast('Note Added', 'Your note was posted to the workspace feed.', 'success');
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {/* Workspace Banner */}
      <View style={styles.bannerCard}>
        <Text style={styles.bannerTag}>COLLABORATIVE WORKSPACE</Text>
        <Text style={styles.bannerTitle}>Metropolitan Hospital AI</Text>
        <Text style={styles.bannerDesc}>
          Shared research repository for autonomous triage modeling and casualty surge stress testing.
        </Text>
      </View>

      {/* Team Roster */}
      <View style={styles.sectionBox}>
        <Text style={styles.sectionHeading}>RESEARCH TEAM ({team.length})</Text>
        <View style={styles.teamList}>
          {team.map((member) => (
            <View key={member.id} style={styles.memberCard}>
              <View style={styles.memberLeft}>
                <View style={styles.avatarBox}>
                  <Text style={styles.avatarText}>{member.avatar}</Text>
                </View>
                <View>
                  <View style={styles.nameRoleRow}>
                    <Text style={styles.memberName}>{member.name}</Text>
                    <Text style={styles.roleTag}>{member.role}</Text>
                  </View>
                  <Text style={styles.lastAction} numberOfLines={1}>{member.lastAction}</Text>
                </View>
              </View>
              <View style={[styles.statusDot, member.status === 'active' ? styles.dotActive : styles.dotOffline]} />
            </View>
          ))}
        </View>
      </View>

      {/* Invite Member Box */}
      <View style={styles.inviteCard}>
        <Text style={styles.inviteHeading}>Invite New Collaborator</Text>
        <View style={styles.inviteRow}>
          <TextInput
            style={styles.inviteInput}
            placeholder="colleague@institute.edu"
            placeholderTextColor="#64748b"
            value={inviteEmail}
            onChangeText={setInviteEmail}
          />
          <TouchableOpacity onPress={handleInvite} style={styles.inviteBtn}>
            <Text style={styles.inviteBtnText}>Invite</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Research Activity Notes */}
      <View style={styles.sectionBox}>
        <Text style={styles.sectionHeading}>RESEARCH NOTES & FEED</Text>

        <View style={styles.postBox}>
          <TextInput
            style={styles.postInput}
            placeholder="Leave a research note or finding..."
            placeholderTextColor="#64748b"
            value={commentInput}
            onChangeText={setCommentInput}
          />
          <TouchableOpacity onPress={handlePostComment} style={styles.postBtn}>
            <Text style={styles.postBtnText}>Post Note</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.commentsList}>
          {comments.map((c) => (
            <View key={c.id} style={styles.commentCard}>
              <View style={styles.commentHeader}>
                <View style={styles.authorRow}>
                  <Text style={styles.commentAvatar}>{c.avatar}</Text>
                  <Text style={styles.commentAuthor}>{c.author}</Text>
                </View>
                <Text style={styles.commentTime}>{c.time}</Text>
              </View>
              <Text style={styles.commentText}>{c.text}</Text>
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
  bannerCard: {
    backgroundColor: 'rgba(15, 23, 42, 0.9)',
    borderRadius: 24,
    padding: 16,
    borderWidth: 1,
    borderColor: '#312e81',
  },
  bannerTag: {
    fontSize: 9,
    fontFamily: 'monospace',
    fontWeight: '800',
    color: '#818cf8',
    letterSpacing: 0.8,
  },
  bannerTitle: {
    fontSize: 16,
    fontWeight: '900',
    color: '#ffffff',
    marginTop: 2,
  },
  bannerDesc: {
    fontSize: 11,
    color: '#cbd5e1',
    marginTop: 4,
    lineHeight: 15,
  },
  sectionBox: {
    gap: 8,
  },
  sectionHeading: {
    fontSize: 11,
    fontWeight: '800',
    color: '#94a3b8',
    letterSpacing: 0.8,
  },
  teamList: {
    gap: 8,
  },
  memberCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: 'rgba(15, 23, 42, 0.9)',
    borderRadius: 18,
    padding: 12,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  memberLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
  },
  avatarBox: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: '#1e293b',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 18,
  },
  nameRoleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  memberName: {
    fontSize: 13,
    fontWeight: '800',
    color: '#ffffff',
  },
  roleTag: {
    fontSize: 9,
    fontFamily: 'monospace',
    color: '#a5b4fc',
    backgroundColor: '#1e1b4b',
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: 4,
  },
  lastAction: {
    fontSize: 10,
    color: '#94a3b8',
    marginTop: 2,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  dotActive: {
    backgroundColor: '#10b981',
  },
  dotOffline: {
    backgroundColor: '#64748b',
  },
  inviteCard: {
    backgroundColor: '#0f172a',
    borderRadius: 20,
    padding: 14,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  inviteHeading: {
    fontSize: 12,
    fontWeight: '800',
    color: '#ffffff',
    marginBottom: 8,
  },
  inviteRow: {
    flexDirection: 'row',
    gap: 8,
  },
  inviteInput: {
    flex: 1,
    backgroundColor: '#1e293b',
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 8,
    color: '#ffffff',
    fontSize: 12,
  },
  inviteBtn: {
    backgroundColor: '#4f46e5',
    paddingHorizontal: 14,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  inviteBtnText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '800',
  },
  postBox: {
    flexDirection: 'row',
    gap: 8,
  },
  postInput: {
    flex: 1,
    backgroundColor: '#0f172a',
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: '#ffffff',
    fontSize: 12,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  postBtn: {
    backgroundColor: '#4f46e5',
    paddingHorizontal: 14,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  postBtnText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '800',
  },
  commentsList: {
    gap: 8,
    marginTop: 4,
  },
  commentCard: {
    backgroundColor: 'rgba(15, 23, 42, 0.9)',
    borderRadius: 16,
    padding: 12,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  commentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  authorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  commentAvatar: {
    fontSize: 14,
  },
  commentAuthor: {
    fontSize: 12,
    fontWeight: '800',
    color: '#ffffff',
  },
  commentTime: {
    fontSize: 9,
    fontFamily: 'monospace',
    color: '#64748b',
  },
  commentText: {
    fontSize: 11,
    color: '#cbd5e1',
    lineHeight: 15,
    paddingLeft: 20,
  },
});
