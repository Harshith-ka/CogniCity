import React, { useRef, useState } from 'react';
import { View, Text, StyleSheet, Modal, TouchableOpacity, TextInput, ActivityIndicator } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useApp } from '../../context/AppContext';
import { colors, typography, layout } from '../../constants/theme';

interface Props {
  visible: boolean;
  onClose?: () => void;
}

export const AuthModal: React.FC<Props> = ({ visible, onClose }) => {
  const { login, signup, isBackendConnected } = useApp();
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [orgName, setOrgName] = useState('');
  const [name, setName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  // A ref, not state — state-based `disabled` still lets a second tap through
  // before React re-renders, since setState is async. This flag is checked and set
  // synchronously, so a rapid double-tap's second call bails out immediately instead
  // of firing a second signup/login request (which was creating duplicate orgs).
  const isSubmittingRef = useRef(false);

  const handleLogin = async () => {
    if (isSubmittingRef.current || !email.trim() || !password.trim()) return;
    isSubmittingRef.current = true;
    setIsLoading(true);
    try {
      const success = await login(email, password);
      if (success && onClose) onClose();
    } finally {
      isSubmittingRef.current = false;
      setIsLoading(false);
    }
  };

  const handleSignup = async () => {
    if (isSubmittingRef.current || !email.trim() || !password.trim() || !name.trim() || !orgName.trim()) return;
    isSubmittingRef.current = true;
    setIsLoading(true);
    try {
      const success = await signup(email, password, name, orgName);
      if (success && onClose) onClose();
    } finally {
      isSubmittingRef.current = false;
      setIsLoading(false);
    }
  };

  return (
    <Modal
      visible={visible}
      animationType="fade"
      transparent={true}
      onRequestClose={onClose}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.authContainer}>
          {/* Header */}
          <View style={styles.authHeader}>
            <View style={styles.logoBox}>
              <Feather name="shield" size={22} color={colors.primaryLight} />
            </View>
            <Text style={styles.titleText}>COGNICITY</Text>
            <Text style={styles.subText}>Autonomous Digital Twin Platform & Policy Sandbox</Text>

            <View style={[styles.statusPill, isBackendConnected ? styles.pillLive : styles.pillOffline]}>
              <View style={[styles.dot, isBackendConnected ? styles.dotGreen : styles.dotAmber]} />
              <Text style={[styles.statusText, isBackendConnected ? styles.textGreen : styles.textAmber]}>
                {isBackendConnected ? 'FastAPI Auth Service Live' : 'Offline Simulation Mode'}
              </Text>
            </View>
          </View>

          {/* Form */}
          <View style={styles.formSection}>
            {mode === 'signup' && (
              <>
                <View style={styles.fieldGroup}>
                  <Text style={styles.fieldLabel}>ORGANIZATION NAME</Text>
                  <TextInput
                    style={styles.textInput}
                    placeholder="Acme Research Lab"
                    placeholderTextColor={colors.textMuted}
                    value={orgName}
                    onChangeText={setOrgName}
                  />
                </View>
                <View style={styles.fieldGroup}>
                  <Text style={styles.fieldLabel}>YOUR NAME</Text>
                  <TextInput
                    style={styles.textInput}
                    placeholder="Jane Doe"
                    placeholderTextColor={colors.textMuted}
                    value={name}
                    onChangeText={setName}
                  />
                </View>
              </>
            )}

            <View style={styles.fieldGroup}>
              <Text style={styles.fieldLabel}>EMAIL</Text>
              <TextInput
                style={styles.textInput}
                placeholder="you@organization.com"
                placeholderTextColor={colors.textMuted}
                autoCapitalize="none"
                keyboardType="email-address"
                value={email}
                onChangeText={setEmail}
              />
            </View>

            <View style={styles.fieldGroup}>
              <Text style={styles.fieldLabel}>PASSWORD</Text>
              <TextInput
                style={styles.textInput}
                placeholder={mode === 'signup' ? 'min. 8 characters' : '••••••••'}
                placeholderTextColor={colors.textMuted}
                secureTextEntry
                value={password}
                onChangeText={setPassword}
              />
            </View>

            <TouchableOpacity
              onPress={mode === 'signin' ? handleLogin : handleSignup}
              disabled={isLoading}
              style={styles.signInBtn}
              activeOpacity={0.7}
            >
              {isLoading ? (
                <ActivityIndicator color="#ffffff" size="small" />
              ) : (
                <Text style={styles.signInBtnText}>{mode === 'signin' ? 'Sign In ➔' : 'Create Account ➔'}</Text>
              )}
            </TouchableOpacity>
            {mode === 'signup' && (
              <Text style={styles.demoCardSub}>Starts on the Free Trial plan — 3 simulation runs, upgrade anytime from Billing.</Text>
            )}
          </View>

          <TouchableOpacity
            onPress={() => setMode(mode === 'signin' ? 'signup' : 'signin')}
            style={styles.guestBtn}
            activeOpacity={0.7}
          >
            <Text style={styles.guestBtnText}>
              {mode === 'signin' ? "New here? Create an account ➔" : 'Already have an account? Sign in ➔'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(5, 8, 15, 0.94)',
    justifyContent: 'center',
    padding: 16,
  },
  authContainer: {
    backgroundColor: colors.surface,
    borderRadius: layout.radiusXl,
    padding: layout.cardPadding,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 12,
  },
  authHeader: {
    alignItems: 'center',
  },
  logoBox: {
    width: 46,
    height: 46,
    borderRadius: layout.radiusMd,
    backgroundColor: colors.primaryGlow,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 6,
    borderWidth: 1,
    borderColor: 'rgba(99, 102, 241, 0.25)',
  },
  titleText: {
    fontSize: 16,
    fontWeight: '900',
    color: colors.textPrimary,
    letterSpacing: 1.5,
  },
  subText: {
    ...typography.caption,
    marginTop: 2,
    textAlign: 'center',
  },
  statusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: layout.radiusSm,
    gap: 5,
    marginTop: 6,
    borderWidth: 1,
  },
  pillLive: {
    backgroundColor: colors.successGlow,
    borderColor: 'rgba(16, 185, 129, 0.3)',
  },
  pillOffline: {
    backgroundColor: colors.warningGlow,
    borderColor: 'rgba(245, 158, 11, 0.3)',
  },
  dot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
  },
  dotGreen: {
    backgroundColor: colors.success,
  },
  dotAmber: {
    backgroundColor: colors.warning,
  },
  statusText: {
    fontSize: 8.5,
    fontFamily: 'monospace',
    fontWeight: '700',
  },
  textGreen: {
    color: colors.successLight,
  },
  textAmber: {
    color: colors.warningLight,
  },
  formSection: {
    gap: 6,
    marginTop: 2,
  },
  fieldGroup: {
    gap: 3,
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
  signInBtn: {
    backgroundColor: colors.primary,
    paddingVertical: 11,
    borderRadius: layout.radiusMd,
    alignItems: 'center',
    marginTop: 4,
  },
  signInBtnText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '700',
  },
  demoSection: {
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: 8,
    gap: 6,
  },
  demoHeading: {
    ...typography.badge,
    color: colors.textMuted,
    textAlign: 'center',
  },
  demoGrid: {
    gap: 5,
  },
  demoCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: colors.surfaceElevated,
    paddingHorizontal: 10,
    paddingVertical: 7,
    borderRadius: layout.radiusSm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  demoCardLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  demoCardTitle: {
    fontSize: 11,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  demoCardSub: {
    fontSize: 8.5,
    color: colors.textMuted,
    fontFamily: 'monospace',
  },
  guestBtn: {
    backgroundColor: 'transparent',
    paddingVertical: 6,
    alignItems: 'center',
  },
  guestBtnText: {
    color: colors.primaryLight,
    fontSize: 11,
    fontWeight: '600',
  },
});
