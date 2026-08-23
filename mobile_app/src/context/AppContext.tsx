import React, { createContext, useContext, useState, useEffect, useCallback, useMemo, ReactNode } from 'react';
import {
  ActiveTab,
  DigitalTwin,
  AIAgent,
  SyntheticCitizen,
  RealTimeAlert,
  Experiment,
  MarketplaceItem,
  BillingState,
  TeamMember,
  DepartmentGov,
  SimulationTime,
  ReasoningChain,
  DisasterIncident,
  PandemicOutbreak,
  SocialMediaPost,
  TrendingTopic,
  AIAdvisorAnalysis,
  InfrastructureProject,
  ElectionRace,
  AuthUser,
} from '../types';
import {
  initialTwins,
  initialAgents,
  initialCitizens,
  initialAlerts,
  initialExperiments,
  marketplaceItems,
  initialBilling,
  initialTeamMembers,
  initialGovDepartments,
  sampleReasoningChains,
  initialDisasters,
  initialPandemic,
  initialSocialPosts,
  initialTrendingTopics,
  initialAIAdvisor,
  initialProjects,
  initialElections,
} from '../data/mockData';
import { api } from '../services/api';

interface Toast {
  id: string;
  title: string;
  message: string;
  severity: 'critical' | 'warning' | 'info' | 'success';
}

interface AppContextType {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  twins: DigitalTwin[];
  selectedTwin: DigitalTwin;
  setSelectedTwin: (twin: DigitalTwin) => void;
  toggleTwinStatus: (twinId: string) => void;
  restartTwinSimulation: (twinId: string) => void;
  agents: AIAgent[];
  selectedAgent: AIAgent | null;
  setSelectedAgent: (agent: AIAgent | null) => void;
  citizens: SyntheticCitizen[];
  selectedCitizen: SyntheticCitizen | null;
  setSelectedCitizen: (citizen: SyntheticCitizen | null) => void;
  alerts: RealTimeAlert[];
  unreadAlertsCount: number;
  markAlertRead: (alertId: string) => void;
  markAllAlertsRead: () => void;
  dismissAlert: (alertId: string) => void;
  experiments: Experiment[];
  activeExperiment: Experiment | null;
  addExperiment: (exp: Omit<Experiment, 'id' | 'status' | 'progressPercent' | 'startedAt' | 'estimatedRemaining' | 'agentHoursProcessed'>) => void;
  simTime: SimulationTime;
  toggleSimulationPlay: () => void;
  setSpeedMultiplier: (speed: number) => void;
  stepForward: () => void;
  restartSimulation: () => void;
  marketplace: MarketplaceItem[];
  installMarketItem: (itemId: string) => void;
  billing: BillingState;
  buyCredits: (amount: number, costInr: number) => void;
  upgradePlan: (planKey: string) => Promise<void>;
  team: TeamMember[];
  inviteTeamMember: (email: string, role: TeamMember['role']) => void;
  departments: DepartmentGov[];
  selectedDept: DepartmentGov | null;
  setSelectedDept: (dept: DepartmentGov | null) => void;
  userRole: 'Admin' | 'Researcher' | 'Analyst' | 'Viewer';
  setUserRole: (role: 'Admin' | 'Researcher' | 'Analyst' | 'Viewer') => void;
  reasoningChains: Record<string, ReasoningChain>;
  toasts: Toast[];
  dismissToast: (id: string) => void;
  showToast: (title: string, message: string, severity?: Toast['severity']) => void;
  isCreateExpOpen: boolean;
  setIsCreateExpOpen: (open: boolean) => void;
  inspectReasoningId: string | null;
  setInspectReasoningId: (id: string | null) => void;
  compareExpIds: [string, string];
  setCompareExpIds: (ids: [string, string]) => void;

  // New Backend Features
  disasters: DisasterIncident[];
  triggerDisaster: (type: DisasterIncident['type'], district: string) => Promise<void>;
  resolveDisaster: (disasterId: string) => Promise<void>;
  refreshDisasters: () => Promise<void>;
  pandemic: PandemicOutbreak;
  togglePandemicPolicy: (policy: 'quarantine' | 'mask_mandate') => void;
  socialPosts: SocialMediaPost[];
  trendingTopics: TrendingTopic[];
  addSocialPost: (content: string) => void;
  triggerTopic: (hashtag: string, topic: string) => void;
  aiAdvisor: AIAdvisorAnalysis;
  queryAIAdvisor: (question: string) => Promise<string>;
  refreshAdvisorScorecard: () => Promise<void>;
  populationStats: any | null;
  refreshPopulationStats: () => Promise<void>;
  projects: InfrastructureProject[];
  elections: ElectionRace;
  castVote: (candidateId: string) => void;

  // Authentication & Multi-Tenancy
  currentUser: AuthUser | null;
  isAuthenticated: boolean;
  isRestoringSession: boolean;
  currentOrg: any | null;
  login: (email: string, password: string) => Promise<boolean>;
  signup: (email: string, password: string, name: string, organizationName: string) => Promise<boolean>;
  logout: () => Promise<void>;

  // Backend Connection
  isBackendConnected: boolean;
  backendUrl: string;
  setBackendUrl: (url: string) => void;
  checkBackendHealth: () => Promise<boolean>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

// Maps this app's mock twin ids onto the real Twin Platform environment keys the
// backend actually knows about (see backend/app/core/feature_modules.py and the
// EnvironmentRegistry catalog). twin_energy_grid has no real backend counterpart yet,
// so it's intentionally absent — it stays visible to everyone rather than being
// filtered against an entitlement that doesn't apply to it.
const TWIN_ENV_KEY_MAP: Record<string, string> = {
  twin_smart_city: 'city',
  twin_hospital: 'hospital_ward',
  twin_airport: 'airport_terminal',
  twin_factory: 'factory_line',
  twin_university: 'university_campus',
};

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('home');
  const [allTwins, setAllTwins] = useState<DigitalTwin[]>(initialTwins);
  const [selectedTwin, setSelectedTwin] = useState<DigitalTwin>(initialTwins[0]);
  const [agents, setAgents] = useState<AIAgent[]>(initialAgents);
  const [selectedAgent, setSelectedAgent] = useState<AIAgent | null>(initialAgents[0]);
  const [citizens, setCitizens] = useState<SyntheticCitizen[]>(initialCitizens);
  const [selectedCitizen, setSelectedCitizen] = useState<SyntheticCitizen | null>(null);
  const [alerts, setAlerts] = useState<RealTimeAlert[]>(initialAlerts);
  const [experiments, setExperiments] = useState<Experiment[]>(initialExperiments);
  const [marketplace, setMarketplace] = useState<MarketplaceItem[]>(marketplaceItems);
  const [billing, setBilling] = useState<BillingState>(initialBilling);
  const [team, setTeam] = useState<TeamMember[]>(initialTeamMembers);
  const [departments, setDepartments] = useState<DepartmentGov[]>(initialGovDepartments);
  const [selectedDept, setSelectedDept] = useState<DepartmentGov | null>(initialGovDepartments[0]);
  const [userRole, setUserRole] = useState<'Admin' | 'Researcher' | 'Analyst' | 'Viewer'>('Researcher');
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [isCreateExpOpen, setIsCreateExpOpen] = useState<boolean>(false);
  const [inspectReasoningId, setInspectReasoningId] = useState<string | null>(null);
  const [compareExpIds, setCompareExpIds] = useState<[string, string]>(['exp_881', 'exp_882']);

  // New Backend States
  const [disasters, setDisasters] = useState<DisasterIncident[]>(initialDisasters);
  const [pandemic, setPandemic] = useState<PandemicOutbreak>(initialPandemic);
  const [socialPosts, setSocialPosts] = useState<SocialMediaPost[]>(initialSocialPosts);
  const [trendingTopics, setTrendingTopics] = useState<TrendingTopic[]>(initialTrendingTopics);
  const [aiAdvisor, setAiAdvisor] = useState<AIAdvisorAnalysis>(initialAIAdvisor);
  const [populationStats, setPopulationStats] = useState<any | null>(null);
  const [projects, setProjects] = useState<InfrastructureProject[]>(initialProjects);
  const [elections, setElections] = useState<ElectionRace>(initialElections);

  // Authentication State — starts logged out. A real session (if one exists) is
  // restored from a persisted token at boot, in the effect below; it is never
  // assumed. See M1/M2 of the mobile integration plan.
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isRestoringSession, setIsRestoringSession] = useState<boolean>(true);
  const [currentOrg, setCurrentOrg] = useState<any | null>(null);

  // Twins filtered against the logged-in org's allowed_environments — empty/no org
  // means unrestricted, matching the backend's own convention. twin_energy_grid has
  // no real environment key yet (see TWIN_ENV_KEY_MAP) so it's never filtered.
  const twins = useMemo(() => {
    const allowedEnvs: string[] | undefined = currentOrg?.allowed_environments;
    if (!allowedEnvs || allowedEnvs.length === 0) return allTwins;
    return allTwins.filter((t) => {
      const envKey = TWIN_ENV_KEY_MAP[t.id];
      return !envKey || allowedEnvs.includes(envKey);
    });
  }, [allTwins, currentOrg]);

  // Backend connection state
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);
  const [backendUrl, setBackendUrlState] = useState<string>(api.getBaseUrl());

  // Simulation Clock
  const [simTime, setSimTime] = useState<SimulationTime>({
    day: 142,
    hour: 14,
    minute: 32,
    second: 15,
    speedMultiplier: 1,
    isRunning: true,
    totalSteps: 48291,
  });

  const showToast = useCallback((title: string, message: string, severity: Toast['severity'] = 'info') => {
    const id = 'toast_' + Date.now() + Math.random().toString(36).substring(2, 5);
    setToasts((prev) => [...prev, { id, title, message, severity }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  }, []);

  const dismissToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const setBackendUrl = (url: string) => {
    setBackendUrlState(url);
    api.setBaseUrl(url);
    checkBackendHealth();
  };

  const checkBackendHealth = async (): Promise<boolean> => {
    const connected = await api.checkHealth();
    setIsBackendConnected(connected);
    if (connected) {
      showToast('Backend Connected', `Synced with FastAPI backend at ${api.getBaseUrl()}`, 'success');
      syncWithBackend();
    }
    return connected;
  };

  const syncWithBackend = async () => {
    try {
      const status = await api.getSimulationStatus();
      if (status) {
        setSimTime((prev) => ({
          ...prev,
          isRunning: status.status === 'running',
          totalSteps: status.current_tick || prev.totalSteps,
        }));
      }

      const remoteTwins = await api.getTwinEnvironments();
      if (remoteTwins && remoteTwins.length > 0) {
        showToast('Environments Synced', `Loaded ${remoteTwins.length} digital twin environments`, 'info');
      }
      // Session restore (getMe) deliberately lives only in the boot effect and in
      // login() below — not here. This can be re-run just from changing the backend
      // URL in Settings, and silently re-authenticating off a leftover token against
      // a different host would be surprising, not helpful.
    } catch {
      // ignore
    }
  };

  const fetchOrgForUser = async (user: AuthUser) => {
    if (!user.organization_id) {
      setCurrentOrg(null);
      return;
    }
    const org = await api.getOrganization(user.organization_id);
    setCurrentOrg(org);
  };

  const login = async (email: string, password: string): Promise<boolean> => {
    const user = await api.login(email, password);
    if (user) {
      setCurrentUser(user);
      setIsAuthenticated(true);
      setUserRole(user.role === 'super_admin' || user.role === 'org_admin' ? 'Admin' : user.role === 'researcher' ? 'Researcher' : 'Viewer');
      showToast('Welcome Back', `Signed in as ${user.name} (${user.role})`, 'success');
      await fetchOrgForUser(user);
      return true;
    }
    showToast(
      'Login Failed',
      isBackendConnected ? 'Incorrect email or password.' : `Can't reach the backend at ${api.getBaseUrl()}. Check the connection in Settings.`,
      'critical'
    );
    return false;
  };

  const signup = async (email: string, password: string, name: string, organizationName: string): Promise<boolean> => {
    const user = await api.signup(email, password, name, organizationName);
    if (user) {
      setCurrentUser(user);
      setIsAuthenticated(true);
      setUserRole('Admin'); // every self-signup becomes org_admin of their own new org
      showToast('Account Created', `Welcome, ${user.name} — ${organizationName} is on the Free Trial plan.`, 'success');
      await fetchOrgForUser(user);
      return true;
    }
    showToast(
      'Signup Failed',
      isBackendConnected ? 'Could not create the account — email or organization name may already be taken.' : `Can't reach the backend at ${api.getBaseUrl()}.`,
      'critical'
    );
    return false;
  };

  const logout = async (): Promise<void> => {
    await api.logout();
    setCurrentUser(null);
    setIsAuthenticated(false);
    setCurrentOrg(null);
    showToast('Signed Out', 'You have been logged out of the platform.', 'info');
  };

  useEffect(() => {
    (async () => {
      await api.restoreToken();
      const connected = await checkBackendHealth();
      if (connected) {
        const me = await api.getMe();
        if (me) {
          setCurrentUser(me);
          setIsAuthenticated(true);
          setUserRole(me.role === 'super_admin' || me.role === 'org_admin' ? 'Admin' : me.role === 'researcher' ? 'Researcher' : 'Viewer');
          await fetchOrgForUser(me);
        }
        // Replace the mock Disasters/AI Advisor/Population data with real,
        // backend-derived state now that we know the API is reachable.
        refreshDisasters();
        refreshAdvisorScorecard();
        refreshPopulationStats();
      }
      setIsRestoringSession(false);
    })();

    api.connectWebSocket((data) => {
      if (data.type === 'tick' || data.type === 'simulation_state') {
        setSimTime((prev) => ({
          ...prev,
          totalSteps: data.current_tick || prev.totalSteps + 1,
        }));
      } else if (data.type === 'alert' || data.type === 'disaster') {
        showToast(data.title || 'Live Incident', data.message || 'Disaster detected in simulation.', 'critical');
      }
    });
  }, []);

  // Clock tick timer effect
  useEffect(() => {
    if (!simTime.isRunning) return;

    const intervalMs = Math.max(30, Math.floor(1000 / simTime.speedMultiplier));
    const timer = setInterval(() => {
      setSimTime((prev) => {
        let sec = prev.second + 1;
        let min = prev.minute;
        let hr = prev.hour;
        let day = prev.day;

        if (sec >= 60) {
          sec = 0;
          min += 1;
          if (min >= 60) {
            min = 0;
            hr += 1;
            if (hr >= 24) {
              hr = 0;
              day += 1;
            }
          }
        }

        return {
          ...prev,
          second: sec,
          minute: min,
          hour: hr,
          day: day,
          totalSteps: prev.totalSteps + 1,
        };
      });
    }, intervalMs);

    return () => clearInterval(timer);
  }, [simTime.isRunning, simTime.speedMultiplier]);

  // Background experiment progress ticker
  useEffect(() => {
    const expTimer = setInterval(() => {
      setExperiments((prev) =>
        prev.map((exp) => {
          if (exp.status === 'running' && exp.progressPercent < 100) {
            const nextPercent = Math.min(100, exp.progressPercent + 1);
            if (nextPercent === 100) {
              showToast(
                '✅ Experiment Completed',
                `${exp.title} has completed 10M agent-hours! Agent B outperformed Agent A by 13.7%.`,
                'success'
              );
              return {
                ...exp,
                progressPercent: 100,
                status: 'completed',
                estimatedRemaining: 'Completed',
              };
            }
            return {
              ...exp,
              progressPercent: nextPercent,
              estimatedRemaining: `${Math.max(1, Math.round((100 - nextPercent) * 0.5))} mins remaining`,
            };
          }
          return exp;
        })
      );
    }, 4000);

    return () => clearInterval(expTimer);
  }, [showToast]);

  const toggleSimulationPlay = () => {
    const nextState = !simTime.isRunning;
    setSimTime((prev) => ({ ...prev, isRunning: nextState }));
    api.sendSimulationControl(nextState ? 'resume' : 'pause');
  };

  const setSpeedMultiplier = (speed: number) => {
    setSimTime((prev) => ({ ...prev, speedMultiplier: speed }));
  };

  const stepForward = () => {
    setSimTime((prev) => {
      let min = prev.minute + 1;
      let hr = prev.hour;
      let day = prev.day;
      if (min >= 60) {
        min = 0;
        hr += 1;
        if (hr >= 24) {
          hr = 0;
          day += 1;
        }
      }
      return {
        ...prev,
        minute: min,
        hour: hr,
        day,
        totalSteps: prev.totalSteps + 1,
      };
    });
    api.sendSimulationControl('step', 1);
    showToast('Simulation Stepped', 'Advanced simulation by 1 step', 'info');
  };

  const restartSimulation = () => {
    setSimTime((prev) => ({
      ...prev,
      day: 1,
      hour: 0,
      minute: 0,
      second: 0,
      totalSteps: 0,
    }));
    api.sendSimulationControl('start');
    showToast('Simulation Restarted', 'Timeline reset to Day 1', 'warning');
  };

  const toggleTwinStatus = (twinId: string) => {
    setAllTwins((prev) =>
      prev.map((t) => {
        if (t.id === twinId) {
          const newStatus = t.status === 'running' ? 'paused' : 'running';
          api.sendSimulationControl(newStatus === 'running' ? 'resume' : 'pause');
          showToast(
            `${t.name} ${newStatus === 'running' ? 'Resumed' : 'Paused'}`,
            `Twin environment is now ${newStatus}.`,
            'info'
          );
          return { ...t, status: newStatus };
        }
        return t;
      })
    );
  };

  const restartTwinSimulation = (twinId: string) => {
    api.sendSimulationControl('start');
    showToast('Twin Reset', 'Digital Twin recalibrated.', 'info');
  };

  const markAlertRead = (alertId: string) => {
    setAlerts((prev) =>
      prev.map((a) => (a.id === alertId ? { ...a, read: true } : a))
    );
  };

  const markAllAlertsRead = () => {
    setAlerts((prev) => prev.map((a) => ({ ...a, read: true })));
    showToast('Alerts Cleared', 'All notifications marked as read.', 'info');
  };

  const dismissAlert = (alertId: string) => {
    setAlerts((prev) => prev.filter((a) => a.id !== alertId));
  };

  const addExperiment = (
    newExp: Omit<Experiment, 'id' | 'status' | 'progressPercent' | 'startedAt' | 'estimatedRemaining' | 'agentHoursProcessed'>
  ) => {
    const id = 'exp_' + Math.floor(Math.random() * 900 + 100);
    const expObj: Experiment = {
      ...newExp,
      id,
      status: 'running',
      progressPercent: 0,
      startedAt: 'Just now',
      estimatedRemaining: '30 mins remaining',
      agentHoursProcessed: '0 / ' + (newExp.population * newExp.durationDays / 1000).toFixed(1) + 'k agent-hours',
      metrics: {
        accuracy: 92.4,
        costInr: Math.round(newExp.population * 0.015),
        robustness: 84.5,
        fairness: 88.0,
        latencyMs: 140,
        carbonKg: 2.1,
      },
    };

    setExperiments((prev) => [expObj, ...prev]);
    setBilling((prev) => ({
      ...prev,
      availableCredits: Math.max(0, prev.availableCredits - 500),
      usedThisMonth: prev.usedThisMonth + 500,
      transactions: [
        {
          id: 'tx_' + Date.now(),
          description: `Launched ${newExp.title}`,
          amount: -500,
          date: 'Just now',
          type: 'debit',
        },
        ...prev.transactions,
      ],
    }));

    showToast(
      '🚀 Experiment Dispatched to Cloud',
      `${newExp.title} is now executing with ${newExp.population.toLocaleString()} agents.`,
      'success'
    );
  };

  const installMarketItem = (itemId: string) => {
    setMarketplace((prev) =>
      prev.map((item) => {
        if (item.id === itemId) {
          const isInstalled = !item.installed;
          showToast(
            isInstalled ? 'Installed Successfully' : 'Uninstalled',
            `${item.title} has been ${isInstalled ? 'added to your workspace' : 'removed'}.`,
            isInstalled ? 'success' : 'info'
          );
          return { ...item, installed: isInstalled };
        }
        return item;
      })
    );
  };

  const buyCredits = (amount: number, costInr: number) => {
    setBilling((prev) => ({
      ...prev,
      availableCredits: prev.availableCredits + amount,
      transactions: [
        {
          id: 'tx_' + Date.now(),
          description: `Purchased +${amount.toLocaleString()} Cloud Compute Credits`,
          amount: amount,
          date: 'Just now',
          type: 'credit',
        },
        ...prev.transactions,
      ],
    }));
    showToast('Payment Successful', `Added +${amount.toLocaleString()} credits for ₹${costInr}.`, 'success');
  };

  const upgradePlan = async (planKey: string) => {
    // Real subscribe (see backend/services/billing.py) — no payment gateway, but a
    // genuine plan switch: quota, credits, and allowed_environments/allowed_modules
    // all update server-side immediately, which is why currentOrg gets refreshed
    // here too — that's what BottomNav's tab filtering and TwinsView's environment
    // filtering actually read from.
    if (!currentOrg?.id) {
      showToast('Upgrade Failed', 'No organization to upgrade — sign in first.', 'critical');
      return;
    }
    const updatedOrg = await api.subscribeToPlan(currentOrg.id, planKey);
    if (!updatedOrg) {
      showToast('Upgrade Failed', 'Could not change your plan. Only an org_admin can do this.', 'critical');
      return;
    }
    setCurrentOrg(updatedOrg);
    setBilling((prev) => ({ ...prev, planName: updatedOrg.plan_key, availableCredits: updatedOrg.credits_balance }));
    showToast('Plan Upgraded', `Your organization is now subscribed to ${updatedOrg.plan_key}.`, 'success');
  };

  const inviteTeamMember = async (email: string, role: TeamMember['role']) => {
    const newMember: TeamMember = {
      id: 'mbr_' + Date.now(),
      name: email.split('@')[0],
      email,
      role,
      avatar: role === 'Researcher' ? '👩🔬' : role === 'Developer' ? '👨💻' : '👨💼',
      status: 'active',
      lastAction: 'Joined workspace',
    };

    // Real invite, when this user is actually an admin of a real organization:
    // creates a genuine PlatformUser via the same endpoint the admin portal uses.
    // There's no email-invite flow on the backend yet, so a temporary password is
    // generated here and surfaced once — the admin is expected to hand it to the
    // invitee directly and have them change it after first login.
    if (currentOrg?.id && (currentUser?.role === 'org_admin' || currentUser?.role === 'super_admin')) {
      const tempPassword = 'Temp' + Math.random().toString(36).slice(2, 8) + '!';
      const backendRole = role === 'Owner' || role === 'Developer' ? 'org_admin' : 'org_member';
      const created = await api.inviteOrganizationUser(currentOrg.id, email, tempPassword, newMember.name, backendRole);
      if (created) {
        setTeam((prev) => [...prev, { ...newMember, id: created.id, name: created.name }]);
        showToast(
          'User Created',
          `${email} was added to ${currentOrg.name}. Temporary password: ${tempPassword}`,
          'success'
        );
        return;
      }
      showToast('Invite Failed', `Could not add ${email} to the organization. They may already exist.`, 'critical');
      return;
    }

    // No real organization context (e.g. viewing standalone/offline) — local-only,
    // clearly not a real backend action.
    setTeam((prev) => [...prev, newMember]);
    showToast('Added Locally', `${email} added to this workspace view only — no organization is active to invite them into.`, 'info');
  };

  const triggerDisaster = async (type: DisasterIncident['type'], district: string) => {
    const icon = type === 'fire' ? '🔥' : type === 'flood' ? '🌊' : type === 'earthquake' ? '🌋' : type === 'blackout' ? '⚡' : '☣️';
    const result = await api.triggerDisaster(type, 0.8);
    if (!result) {
      showToast('Trigger Failed', `Couldn't reach the backend at ${api.getBaseUrl()} — disaster was not created.`, 'critical');
      return;
    }
    // The backend is the source of truth for id/phase/intensity — this local record
    // only fills in the display fields (district, icon, narrative) it doesn't return.
    const newDisaster: DisasterIncident = {
      id: result.id || 'dis_' + Date.now(),
      type,
      title: result.name || `${type.toUpperCase()} Outbreak Triggered`,
      icon,
      district,
      intensity: result.intensity ?? 0.8,
      phase: result.phase || 'onset',
      affectedCitizens: Math.floor(Math.random() * 2000) + 500, // no per-disaster casualty estimate at trigger time
      evacuationZoneRadius: 600,
      responseNarrative: 'Mayor & Emergency department dispatching response units immediately.',
      startedAt: 'Just now',
      isActive: true,
    };
    setDisasters((prev) => [newDisaster, ...prev]);
    showToast(`🚨 ${newDisaster.title}`, `Emergency declared in ${district}. Response crews deployed.`, 'critical');
  };

  const resolveDisaster = async (disasterId: string) => {
    const ok = await api.resolveDisaster(disasterId);
    if (!ok) {
      showToast('Resolve Failed', `Couldn't reach the backend at ${api.getBaseUrl()} — disaster is still active.`, 'critical');
      return;
    }
    setDisasters((prev) =>
      prev.map((d) => (d.id === disasterId ? { ...d, phase: 'resolved', isActive: false } : d))
    );
    showToast('Disaster Resolved', 'Emergency crews stood down. Area restored to normal status.', 'success');
  };

  const refreshDisasters = async () => {
    const active = await api.getActiveDisasters();
    if (!active || active.length === 0) return; // keep current state — an empty/failed fetch isn't proof there are none
    setDisasters(active.map((d: any) => ({
      id: d.id,
      type: (d.type || d.disaster_type || 'fire') as DisasterIncident['type'],
      title: d.name || `${(d.type || d.disaster_type || '').toUpperCase()} Incident`,
      icon: d.type === 'fire' ? '🔥' : d.type === 'flood' ? '🌊' : d.type === 'earthquake' ? '🌋' : d.type === 'blackout' ? '⚡' : '☣️',
      district: d.district || 'Unknown District',
      intensity: d.intensity ?? 0.5,
      phase: d.phase || 'onset',
      affectedCitizens: d.affected_citizens ?? 0,
      evacuationZoneRadius: d.evacuation_zone_radius ?? 600,
      responseNarrative: d.status_narrative || 'Response units engaged.',
      startedAt: d.started_at || 'Active',
      isActive: d.is_active ?? true,
    })));
  };

  const refreshAdvisorScorecard = async () => {
    const scorecard = await api.getAdvisorScorecard();
    if (!scorecard) return;
    setAiAdvisor({
      healthIndex: scorecard.healthIndex ?? 0,
      economicStability: scorecard.economicStability ?? 0,
      safetyScore: scorecard.safetyScore ?? 0,
      carbonScore: scorecard.carbonScore ?? null,
      summary: scorecard.summary || 'No analysis available yet.',
      riskLevel: scorecard.riskLevel || 'moderate',
      criticalRisks: scorecard.criticalRisks || [],
      recommendedPolicies: scorecard.recommendedPolicies || [],
    });
  };

  const refreshPopulationStats = async () => {
    const stats = await api.getPopulationLiveStats();
    setPopulationStats(stats);
  };

  const togglePandemicPolicy = (policy: 'quarantine' | 'mask_mandate') => {
    setPandemic((prev) => {
      const isQuar = policy === 'quarantine' ? !prev.quarantineActive : prev.quarantineActive;
      const isMask = policy === 'mask_mandate' ? !prev.maskMandateActive : prev.maskMandateActive;
      showToast('Pandemic Policy Enacted', `${policy === 'quarantine' ? 'Quarantine Zones' : 'Universal Mask Mandate'} updated.`, 'warning');
      return {
        ...prev,
        quarantineActive: isQuar,
        maskMandateActive: isMask,
        r0: isQuar || isMask ? Math.max(0.8, prev.r0 - 0.4) : prev.r0 + 0.5,
      };
    });
  };

  const addSocialPost = (content: string) => {
    const newPost: SocialMediaPost = {
      id: 'post_' + Date.now(),
      authorName: currentUser?.name || 'City Citizen Voice',
      authorHandle: `@${currentUser?.email.split('@')[0] || 'citizen_voice'}`,
      authorAvatar: currentUser?.avatar || '🗣️',
      content,
      timestamp: 'Just now',
      sentiment: 'positive',
      sentimentScore: 0.75,
      likes: 12,
      retweets: 2,
      commentsCount: 0,
      hashtags: ['CityFeedback'],
    };
    setSocialPosts((prev) => [newPost, ...prev]);
    showToast('Post Published', 'Your feedback was broadcast to the city feed.', 'success');
  };

  const triggerTopic = (hashtag: string, topic: string) => {
    const newTopic: TrendingTopic = {
      hashtag,
      topic,
      category: 'news',
      mentions: 50,
      trend: 'up',
      sentiment: 'positive',
    };
    setTrendingTopics((prev) => [newTopic, ...prev]);
    api.triggerTopic(hashtag, topic);
    showToast('Topic Broadcast', `${hashtag} is now trending across simulated citizens.`, 'info');
  };

  const queryAIAdvisor = async (question: string): Promise<string> => {
    const res = await api.queryCityAdvisor(question);
    if (res && res.analysis) {
      return res.analysis;
    }
    return `Couldn't reach the advisor backend at ${api.getBaseUrl()} — check your connection and try again.`;
  };

  const castVote = (candidateId: string) => {
    setElections((prev) => ({
      ...prev,
      candidates: prev.candidates.map((c) =>
        c.id === candidateId
          ? { ...c, pollingPercent: Math.min(100, Number((c.pollingPercent + 1.2).toFixed(1))) }
          : { ...c, pollingPercent: Math.max(0, Number((c.pollingPercent - 1.2).toFixed(1))) }
      ),
    }));
    showToast('Vote Cast Recorded', 'Your ballot preference was submitted to the municipal ledger.', 'success');
  };

  const unreadAlertsCount = alerts.filter((a) => !a.read).length;
  const activeExperiment = experiments.find((e) => e.status === 'running') || null;

  return (
    <AppContext.Provider
      value={{
        activeTab,
        setActiveTab,
        twins,
        selectedTwin,
        setSelectedTwin,
        toggleTwinStatus,
        restartTwinSimulation,
        agents,
        selectedAgent,
        setSelectedAgent,
        citizens,
        selectedCitizen,
        setSelectedCitizen,
        alerts,
        unreadAlertsCount,
        markAlertRead,
        markAllAlertsRead,
        dismissAlert,
        experiments,
        activeExperiment,
        addExperiment,
        simTime,
        toggleSimulationPlay,
        setSpeedMultiplier,
        stepForward,
        restartSimulation,
        marketplace,
        installMarketItem,
        billing,
        buyCredits,
        upgradePlan,
        team,
        inviteTeamMember,
        departments,
        selectedDept,
        setSelectedDept,
        userRole,
        setUserRole,
        reasoningChains: sampleReasoningChains,
        toasts,
        dismissToast,
        showToast,
        isCreateExpOpen,
        setIsCreateExpOpen,
        inspectReasoningId,
        setInspectReasoningId,
        compareExpIds,
        setCompareExpIds,
        disasters,
        triggerDisaster,
        resolveDisaster,
        refreshDisasters,
        pandemic,
        togglePandemicPolicy,
        socialPosts,
        trendingTopics,
        addSocialPost,
        triggerTopic,
        aiAdvisor,
        queryAIAdvisor,
        refreshAdvisorScorecard,
        populationStats,
        refreshPopulationStats,
        projects,
        elections,
        castVote,
        currentUser,
        isAuthenticated,
        isRestoringSession,
        currentOrg,
        login,
        signup,
        logout,
        isBackendConnected,
        backendUrl,
        setBackendUrl,
        checkBackendHealth,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
