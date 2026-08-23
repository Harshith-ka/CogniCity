export type SimulationStatus = 'running' | 'paused' | 'completed' | 'queued' | 'error';

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  role: 'super_admin' | 'org_admin' | 'researcher' | 'analyst' | 'viewer';
  organization_id?: string | null;
  organization_name?: string | null;
  avatar?: string;
}

export interface DigitalTwin {
  id: string;
  name: string;
  category: 'smart_city' | 'healthcare' | 'aviation' | 'industrial' | 'education' | 'energy';
  icon: string;
  agentCount: number;
  environmentSize: string;
  status: SimulationStatus;
  healthScore: number;
  description: string;
  activeScenario?: string;
  lastUpdated: string;
  tags: string[];
  metrics: {
    trafficFlow?: number;
    resourceUtilization?: number;
    airQualityIndex?: number;
    emergencyResponseSec?: number;
    powerGridLoad?: number;
    patientTriageWaitMin?: number;
  };
}

export interface SimulationEntity {
  id: string;
  type: 'agent' | 'vehicle' | 'emergency' | 'building' | 'incident';
  subType?: 'citizen' | 'car' | 'bus' | 'ambulance' | 'police' | 'fire_truck' | 'hospital' | 'office' | 'school' | 'fire' | 'congestion' | 'accident';
  name: string;
  x: number;
  y: number;
  targetX?: number;
  targetY?: number;
  speed?: number;
  status?: string;
  color?: string;
  pulse?: boolean;
}

export interface SimulationTime {
  day: number;
  hour: number;
  minute: number;
  second: number;
  speedMultiplier: number;
  isRunning: boolean;
  totalSteps: number;
}

export interface AIAgent {
  id: string;
  name: string;
  category: 'traffic' | 'health' | 'finance' | 'triage' | 'real_estate' | 'energy';
  icon: string;
  status: 'running' | 'idle' | 'evaluating' | 'paused';
  environment: string;
  agentsTested: number;
  interactions: string;
  performance: number; // %
  robustness: number; // %
  fairness: number; // %
  latencyMs: number;
  driftRisk: 'low' | 'medium' | 'high';
  version: string;
  description: string;
  lastReasoningStep?: string;
}

export interface SyntheticCitizen {
  id: string;
  name: string;
  avatar: string;
  age: number;
  occupation: string;
  income: string;
  netWorth: string;
  location: string;
  education: string;
  traits: string[];
  health: {
    bmi: number;
    bp: string;
    heartRate: number;
    stressLevel: 'Low' | 'Moderate' | 'High';
    physicalActivityMin: number;
    healthRiskScore: number; // 0-100
  };
  lifestyle: {
    diet: string;
    smoking: boolean;
    alcohol: string;
    sleepHours: number;
  };
  lastAction: string;
  currentIntent: string;
}

export interface ReasoningStep {
  id: string;
  title: string;
  type: 'observation' | 'evaluation' | 'action' | 'reward' | 'goal' | 'options' | 'decision' | 'reason';
  description: string;
  timestamp: string;
  detail?: string;
  metricChange?: string;
}

export interface ReasoningChain {
  entityId: string;
  entityName: string;
  entityType: 'agent' | 'citizen';
  goalOrContext: string;
  confidence: number;
  steps: ReasoningStep[];
}

export interface RealTimeAlert {
  id: string;
  title: string;
  message: string;
  severity: 'critical' | 'warning' | 'info' | 'success';
  timestamp: string;
  source: string;
  twinId?: string;
  read: boolean;
  actionLabel?: string;
}

export interface Experiment {
  id: string;
  title: string;
  environment: string;
  population: number;
  durationDays: number;
  scenario: string;
  agentName: string;
  status: 'running' | 'completed' | 'queued' | 'failed';
  progressPercent: number;
  startedAt: string;
  estimatedRemaining: string;
  agentHoursProcessed: string;
  metrics?: {
    accuracy: number;
    costInr: number;
    robustness: number;
    fairness: number;
    latencyMs: number;
    carbonKg: number;
  };
}

export interface MarketplaceItem {
  id: string;
  title: string;
  type: 'simulation' | 'agent';
  rating: number;
  reviewsCount: number;
  downloads: string;
  price: string;
  author: string;
  badge?: 'trending' | 'verified' | 'popular' | 'new';
  description: string;
  tags: string[];
  installed?: boolean;
}

export interface BillingState {
  availableCredits: number;
  usedThisMonth: number;
  estimatedRemainingSims: number;
  planName: string;
  renewalDate: string;
  transactions: {
    id: string;
    description: string;
    amount: number;
    date: string;
    type: 'credit' | 'debit';
  }[];
}

export interface TeamMember {
  id: string;
  name: string;
  role: 'Owner' | 'Researcher' | 'Developer' | 'Analyst';
  avatar: string;
  email: string;
  status: 'active' | 'offline';
  lastAction: string;
}

export interface DepartmentGov {
  id: string;
  name: string;
  icon: string;
  lead: string;
  activeSimulations: number;
  budgetAllocated: string;
  kpiHealth: number;
  alertsCount: number;
}

// === NEW BACKEND FEATURE DATA MODELS ===

export interface DisasterIncident {
  id: string;
  type: 'earthquake' | 'flood' | 'fire' | 'blackout' | 'heatwave' | 'chemical';
  title: string;
  icon: string;
  district: string;
  intensity: number; // 0.0 - 1.0
  phase: 'onset' | 'peak' | 'declining' | 'recovery' | 'resolved';
  affectedCitizens: number;
  evacuationZoneRadius: number;
  responseNarrative: string;
  startedAt: string;
  isActive: boolean;
}

export interface PandemicOutbreak {
  id: string;
  pathogenName: string;
  variant: string;
  r0: number;
  totalInfected: number;
  totalRecovered: number;
  totalFatalities: number;
  activeHospitalizations: number;
  quarantineActive: boolean;
  maskMandateActive: boolean;
  vaccinationCoveragePercent: number;
  spreadVelocity: 'Accelerating' | 'Stabilizing' | 'Declining';
}

export interface SocialMediaPost {
  id: string;
  authorName: string;
  authorHandle: string;
  authorAvatar: string;
  content: string;
  timestamp: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  sentimentScore: number;
  likes: number;
  retweets: number;
  commentsCount: number;
  hashtags: string[];
}

export interface TrendingTopic {
  hashtag: string;
  topic: string;
  category: 'news' | 'politics' | 'transport' | 'health' | 'culture';
  mentions: number;
  trend: 'up' | 'down' | 'steady';
  sentiment: 'positive' | 'neutral' | 'negative';
}

export interface AIAdvisorAnalysis {
  healthIndex: number;
  economicStability: number;
  safetyScore: number;
  carbonScore: number | null; // null until the environment module has data
  summary: string;
  riskLevel: 'low' | 'moderate' | 'high' | 'critical';
  criticalRisks: string[];
  // No cost/ROI estimate — the backend's grounded analysis (LLM or rule-based
  // fallback, see CityAdvisor) never produces one, so this only carries what's real.
  recommendedPolicies: {
    issue: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    recommendation: string;
    expectedImpact: string;
  }[];
}

export interface InfrastructureProject {
  id: string;
  title: string;
  icon: string;
  category: 'transit' | 'energy' | 'water' | 'civic' | 'telecom';
  district: string;
  progressPercent: number;
  budgetTotal: string;
  spentSoFar: string;
  etaMonths: number;
  status: 'planning' | 'construction' | 'operational';
  benefitDescription: string;
}

export interface ElectionCandidate {
  id: string;
  name: string;
  party: string;
  avatar: string;
  pollingPercent: number;
  platformSummary: string;
  keyStance: string;
}

export interface ElectionRace {
  title: string;
  daysUntilElection: number;
  projectedTurnoutPercent: number;
  candidates: ElectionCandidate[];
}

export type ActiveTab = 
  | 'home'
  | 'twins'
  | 'live_map'
  | 'experiments'
  | 'agents'
  | 'population'
  | 'reasoning'
  | 'alerts'
  | 'analytics'
  | 'comparison'
  | 'marketplace'
  | 'billing'
  | 'collaboration'
  | 'reports'
  | 'gov_mode'
  | 'experiment_watch'
  | 'disasters_pandemics'
  | 'social_feed'
  | 'ai_advisor'
  | 'infrastructure'
  | 'elections'
  | 'account_auth';
