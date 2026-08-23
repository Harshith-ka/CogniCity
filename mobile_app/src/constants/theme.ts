/**
 * Classy & Enterprise Dark Design System for CogniCity Mobile
 */

export const colors = {
  // Backgrounds
  background: '#07090E',
  surface: '#0E131F',
  surfaceElevated: '#141B2D',
  surfaceSubtle: 'rgba(20, 27, 45, 0.65)',
  surfaceHighlight: 'rgba(255, 255, 255, 0.04)',

  // Borders & Dividers
  border: 'rgba(255, 255, 255, 0.08)',
  borderLight: 'rgba(255, 255, 255, 0.14)',
  borderActive: 'rgba(99, 102, 241, 0.5)',

  // Typography Colors
  textPrimary: '#F8FAFC',
  textSecondary: '#94A3B8',
  textMuted: '#64748B',
  textDisabled: '#475569',

  // Brand & Accents
  primary: '#6366F1',
  primaryDark: '#4F46E5',
  primaryLight: '#818CF8',
  primaryGlow: 'rgba(99, 102, 241, 0.15)',

  // Status & Telemetry
  success: '#10B981',
  successLight: '#34D399',
  successGlow: 'rgba(16, 185, 129, 0.15)',

  warning: '#F59E0B',
  warningLight: '#FBBF24',
  warningGlow: 'rgba(245, 158, 11, 0.15)',

  danger: '#F43F5E',
  dangerLight: '#FDA4AF',
  dangerGlow: 'rgba(244, 63, 94, 0.15)',

  cyan: '#06B6D4',
  cyanLight: '#38BDF8',
  cyanGlow: 'rgba(6, 182, 212, 0.15)',

  purple: '#8B5CF6',
  purpleLight: '#C084FC',
  purpleGlow: 'rgba(139, 92, 246, 0.15)',
};

export const typography = {
  h1: {
    fontSize: 22,
    fontWeight: '800' as const,
    color: colors.textPrimary,
    letterSpacing: -0.4,
  },
  h2: {
    fontSize: 16,
    fontWeight: '700' as const,
    color: colors.textPrimary,
    letterSpacing: -0.2,
  },
  h3: {
    fontSize: 14,
    fontWeight: '700' as const,
    color: colors.textPrimary,
  },
  body: {
    fontSize: 12,
    fontWeight: '400' as const,
    color: colors.textSecondary,
    lineHeight: 17,
  },
  bodyBold: {
    fontSize: 12,
    fontWeight: '600' as const,
    color: colors.textPrimary,
  },
  caption: {
    fontSize: 10,
    fontWeight: '500' as const,
    color: colors.textMuted,
  },
  badge: {
    fontSize: 9,
    fontFamily: 'monospace',
    fontWeight: '700' as const,
    letterSpacing: 0.6,
  },
  numberLarge: {
    fontSize: 26,
    fontWeight: '800' as const,
    fontFamily: 'monospace',
    color: colors.textPrimary,
  },
  numberMedium: {
    fontSize: 16,
    fontWeight: '700' as const,
    fontFamily: 'monospace',
    color: colors.textPrimary,
  },
};

export const layout = {
  radiusSm: 8,
  radiusMd: 12,
  radiusLg: 18,
  radiusXl: 24,
  padding: 14,
  cardPadding: 16,
};
