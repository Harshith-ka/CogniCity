import React, { useRef, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, ActivityIndicator } from 'react-native';
import { Feather, Ionicons } from '@expo/vector-icons';
import { useApp } from '../../context/AppContext';
import { colors, typography, layout } from '../../constants/theme';

export const AccountAuthView: React.FC = () => {
  const {
    currentUser,
    isAuthenticated,
    login,
    logout,
    isBackendConnected,
  } = useApp();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const isSubmittingRef = useRef(false); // synchronous double-tap guard, see AuthModal.tsx

  const handleLogin = async () => {
    if (isSubmittingRef.current || !email.trim() || !password.trim()) return;
    isSubmittingRef.current = true;
    setIsLoading(true);
    try {
      await login(email, password);
    } finally {
      isSubmittingRef.current = false;
      setIsLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {isAuthenticated && currentUser ? (
        /* Authenticated User Profile Card */
        <View style={styles.profileCard}>
          <View style={styles.profileTop}>
            <View style={styles.avatarBox}>
              <Feather name="user" size={24} color={colors.primaryLight} />
            </View>
            <View style={styles.userInfo}>
              <View style={styles.nameBadgeRow}>
                <Text style={styles.userName}>{currentUser.name}</Text>
                <View style={styles.roleBadge}>
                  <Text style={styles.roleBadgeText}>{currentUser.role.toUpperCase()}</Text>
                </View>
              </View>
              <Text style={styles.userEmail}>{currentUser.email}</Text>
              <Text style={styles.userOrg}>{currentUser.organization_name || 'Platform-level account'}</Text>
            </View>
          </View>

          {/* Session & Security Specs */}
          <View style={styles.sessionBox}>
            <View style={styles.sessionRow}>
              <Text style={styles.sessionLabel}>Session Mode:</Text>
              <Text style={styles.sessionVal}>{isBackendConnected ? 'FastAPI JWT Bearer' : 'Local Standalone Session'}</Text>
            </View>
            <View style={styles.sessionRow}>
              <Text style={styles.sessionLabel}>Role:</Text>
              <Text style={[styles.sessionVal, { color: colors.successLight }]}>{currentUser.role.replace('_', ' ')}</Text>
            </View>
            <View style={styles.sessionRow}>
              <Text style={styles.sessionLabel}>Organization:</Text>
              <Text style={styles.sessionVal}>{currentUser.organization_name || '— platform-level account'}</Text>
            </View>
          </View>

          <TouchableOpacity onPress={() => logout()} style={styles.logoutBtn} activeOpacity={0.7}>
            <Feather name="log-out" size={13} color="#ffffff" style={{ marginRight: 6 }} />
            <Text style={styles.logoutBtnText}>Sign Out of Platform</Text>
          </TouchableOpacity>
        </View>
      ) : (
        /* Login Form */
        <View style={styles.authCard}>
          <View style={styles.authHeader}>
            <View style={styles.authLogoBox}>
              <Feather name="lock" size={20} color={colors.primaryLight} />
            </View>
            <Text style={styles.authTitle}>Platform Authentication</Text>
            <Text style={styles.authSubtitle}>Sign in to access AI Twin City enterprise workspaces</Text>
          </View>

          <View style={styles.formGroup}>
            <Text style={styles.fieldLabel}>ORGANIZATION EMAIL</Text>
            <TextInput
              style={styles.textInput}
              placeholder="admin@digitaltwin.city"
              placeholderTextColor={colors.textMuted}
              autoCapitalize="none"
              keyboardType="email-address"
              value={email}
              onChangeText={setEmail}
            />
          </View>

          <View style={styles.formGroup}>
            <Text style={styles.fieldLabel}>PASSWORD</Text>
            <TextInput
              style={styles.textInput}
              placeholder="••••••••"
              placeholderTextColor={colors.textMuted}
              secureTextEntry
              value={password}
              onChangeText={setPassword}
            />
          </View>

          <TouchableOpacity
            onPress={() => handleLogin()}
            disabled={isLoading}
            style={styles.submitBtn}
            activeOpacity={0.7}
          >
            {isLoading ? (
              <ActivityIndicator color="#ffffff" size="small" />
            ) : (
              <Text style={styles.submitBtnText}>Sign In ➔</Text>
            )}
          </TouchableOpacity>

          <Text style={[styles.demoHeading, { marginTop: 4 }]}>New here? Create an account from the sign-in prompt on Home.</Text>
        </View>
      )}
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
  profileCard: {
    backgroundColor: colors.surface,
    borderRadius: layout.radiusLg,
    padding: layout.cardPadding,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 12,
  },
  profileTop: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    paddingBottom: 12,
  },
  avatarBox: {
    width: 48,
    height: 48,
    borderRadius: layout.radiusMd,
    backgroundColor: colors.primaryGlow,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(99, 102, 241, 0.25)',
  },
  userInfo: {
    flex: 1,
  },
  nameBadgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  userName: {
    ...typography.h2,
  },
  roleBadge: {
    backgroundColor: colors.primaryGlow,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  roleBadgeText: {
    fontSize: 8,
    fontFamily: 'monospace',
    fontWeight: '800',
    color: colors.primaryLight,
  },
  userEmail: {
    ...typography.caption,
    marginTop: 2,
    fontFamily: 'monospace',
  },
  userOrg: {
    fontSize: 10.5,
    color: colors.textSecondary,
    marginTop: 2,
  },
  sessionBox: {
    backgroundColor: colors.surfaceElevated,
    borderRadius: layout.radiusMd,
    padding: 10,
    gap: 6,
    borderWidth: 1,
    borderColor: colors.border,
  },
  sessionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  sessionLabel: {
    ...typography.caption,
  },
  sessionVal: {
    fontSize: 9.5,
    fontFamily: 'monospace',
    fontWeight: '700',
    color: colors.textSecondary,
  },
  roleSwitchSection: {
    gap: 6,
  },
  sectionHeading: {
    ...typography.badge,
    color: colors.textMuted,
  },
  rolesGrid: {
    flexDirection: 'row',
    gap: 6,
  },
  roleSelectBtn: {
    flex: 1,
    backgroundColor: colors.surfaceElevated,
    paddingVertical: 8,
    borderRadius: layout.radiusSm,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  roleSelectActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primaryLight,
  },
  roleSelectText: {
    fontSize: 10,
    fontWeight: '600',
    color: colors.textMuted,
  },
  roleSelectTextActive: {
    color: '#ffffff',
    fontWeight: '700',
  },
  logoutBtn: {
    flexDirection: 'row',
    backgroundColor: 'rgba(244, 63, 94, 0.15)',
    paddingVertical: 10,
    borderRadius: layout.radiusMd,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(244, 63, 94, 0.3)',
    marginTop: 4,
  },
  logoutBtnText: {
    color: colors.dangerLight,
    fontSize: 11.5,
    fontWeight: '700',
  },
  authCard: {
    backgroundColor: colors.surface,
    borderRadius: layout.radiusLg,
    padding: layout.cardPadding,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 12,
  },
  authHeader: {
    alignItems: 'center',
    marginBottom: 4,
  },
  authLogoBox: {
    width: 44,
    height: 44,
    borderRadius: layout.radiusMd,
    backgroundColor: colors.primaryGlow,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
    borderWidth: 1,
    borderColor: 'rgba(99, 102, 241, 0.25)',
  },
  authTitle: {
    ...typography.h2,
  },
  authSubtitle: {
    ...typography.caption,
    marginTop: 2,
    textAlign: 'center',
  },
  formGroup: {
    gap: 4,
  },
  fieldLabel: {
    ...typography.badge,
    color: colors.textMuted,
  },
  textInput: {
    backgroundColor: colors.surfaceElevated,
    borderRadius: layout.radiusSm,
    paddingHorizontal: 12,
    paddingVertical: 9,
    color: colors.textPrimary,
    fontSize: 12,
    borderWidth: 1,
    borderColor: colors.border,
  },
  submitBtn: {
    backgroundColor: colors.primary,
    paddingVertical: 11,
    borderRadius: layout.radiusMd,
    alignItems: 'center',
    marginTop: 4,
  },
  submitBtnText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '700',
  },
  demoSection: {
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: 10,
    gap: 6,
  },
  demoHeading: {
    ...typography.badge,
    color: colors.textMuted,
    textAlign: 'center',
  },
  demoButtonsList: {
    gap: 6,
    marginTop: 4,
  },
  demoBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceElevated,
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: layout.radiusSm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  demoBtnText: {
    fontSize: 10,
    color: colors.textSecondary,
    fontFamily: 'monospace',
  },
});
