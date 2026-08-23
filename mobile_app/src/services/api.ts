/**
 * AI Twin City Mobile — Backend API & WebSocket Service Layer with Full Multi-Tenant Auth
 */

import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AuthUser } from '../types';

const DEFAULT_HOST = Platform.select({
  android: 'http://10.0.2.2:8000',
  ios: 'http://localhost:8000',
  default: 'http://localhost:8000',
});

// The backend's real session is an httpOnly cookie — invisible to app JS and
// unreliable to persist across iOS/Android/web from React Native's fetch. So the
// login endpoint also hands back the raw JWT in its response body (see
// backend/app/api/auth.py's UserOut.token) for this client to store and replay as
// `Authorization: Bearer <token>` instead.
const TOKEN_STORAGE_KEY = 'cognicity_mobile_token';

class ApiService {
  private baseUrl: string = DEFAULT_HOST;
  private isConnected: boolean = false;
  private token: string | null = null;
  private ws: WebSocket | null = null;
  private wsListeners: Array<(data: any) => void> = [];

  constructor() {
    this.checkHealth();
  }

  public setBaseUrl(url: string) {
    this.baseUrl = url.replace(/\/+$/, '');
    this.checkHealth();
    this.reconnectWebSocket();
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  public getIsConnected(): boolean {
    return this.isConnected;
  }

  public setToken(token: string | null) {
    this.token = token;
  }

  public getToken(): string | null {
    return this.token;
  }

  private getHeaders(extraHeaders: Record<string, string> = {}): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...extraHeaders,
    };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  /**
   * Health check endpoint
   */
  public async checkHealth(): Promise<boolean> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);
      const res = await fetch(`${this.baseUrl}/health`, { signal: controller.signal });
      clearTimeout(timeoutId);
      this.isConnected = res.ok;
      return res.ok;
    } catch {
      this.isConnected = false;
      return false;
    }
  }

  /**
   * Authentication Endpoints — no fake fallback: a failed login (wrong credentials
   * OR an unreachable backend) returns null and the caller shows a real error. Auth
   * that silently "succeeds" as a fabricated user regardless of what you typed isn't
   * auth — it's a demo that happened to look like one.
   */
  public async login(email: string, password: string): Promise<AuthUser | null> {
    try {
      const res = await fetch(`${this.baseUrl}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) return null;
      const user = await res.json();
      if (user.token) {
        this.token = user.token;
        try { await AsyncStorage.setItem(TOKEN_STORAGE_KEY, user.token); } catch { /* persistence best-effort */ }
      }
      return user;
    } catch {
      return null;
    }
  }

  /**
   * Restores a persisted session token at app boot, before the first getMe() call.
   * Returns the token if one was found (not yet validated — getMe() does that).
   */
  public async restoreToken(): Promise<string | null> {
    try {
      const stored = await AsyncStorage.getItem(TOKEN_STORAGE_KEY);
      if (stored) this.token = stored;
      return stored;
    } catch {
      return null;
    }
  }

  public async logout(): Promise<boolean> {
    try {
      await fetch(`${this.baseUrl}/api/auth/logout`, {
        method: 'POST',
        headers: this.getHeaders(),
      });
    } catch {
      // ignore — clearing the local token below is what actually matters
    }
    this.token = null;
    try { await AsyncStorage.removeItem(TOKEN_STORAGE_KEY); } catch { /* best-effort */ }
    return true;
  }

  public async getMe(): Promise<AuthUser | null> {
    try {
      const res = await fetch(`${this.baseUrl}/api/auth/me`, {
        headers: this.getHeaders(),
      });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }

  /**
   * Multi-Tenant Admin & Organization Management — no mock fallback: a failed fetch
   * here means "we don't know", not "assume Metropolitan Smart City Authority
   * exists." Screens decide how to represent an empty/failed result themselves.
   */
  public async listOrganizations(): Promise<any[]> {
    try {
      const res = await fetch(`${this.baseUrl}/api/admin/organizations`, {
        headers: this.getHeaders(),
      });
      if (!res.ok) throw new Error('Failed to list orgs');
      return await res.json();
    } catch {
      return [];
    }
  }

  public async getOrganization(orgId: string): Promise<any | null> {
    try {
      const res = await fetch(`${this.baseUrl}/api/admin/organizations/${orgId}`, {
        headers: this.getHeaders(),
      });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }

  public async listOrganizationUsers(orgId: string): Promise<any[]> {
    try {
      const res = await fetch(`${this.baseUrl}/api/admin/organizations/${orgId}/users`, {
        headers: this.getHeaders(),
      });
      if (!res.ok) return [];
      return await res.json();
    } catch {
      return [];
    }
  }

  public async inviteOrganizationUser(
    orgId: string,
    email: string,
    password: string,
    name: string,
    role: 'org_admin' | 'org_member' = 'org_member'
  ): Promise<any | null> {
    try {
      const res = await fetch(`${this.baseUrl}/api/admin/organizations/${orgId}/users`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ email, password, name, role }),
      });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }

  public async listPlans(): Promise<any[]> {
    try {
      const res = await fetch(`${this.baseUrl}/api/admin/plans`, { headers: this.getHeaders() });
      if (!res.ok) return [];
      return await res.json();
    } catch {
      return [];
    }
  }

  /**
   * Self-service plan upgrade — the real "purchase" action (no payment gateway,
   * see backend/app/services/billing.py). Returns the updated organization, whose
   * allowed_environments/allowed_modules reflect the new plan immediately, or null
   * on failure (e.g. an org_member trying to change their org's plan, which the
   * backend rejects with 403).
   */
  public async subscribeToPlan(orgId: string, planKey: string): Promise<any | null> {
    try {
      const res = await fetch(`${this.baseUrl}/api/admin/organizations/${orgId}/subscribe`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ plan_key: planKey }),
      });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }

  /**
   * Self-service signup — POST /api/auth/signup on the backend. Every signup lands
   * on the Free Trial plan (3 simulation runs) and becomes org_admin of a
   * brand-new organization created for them.
   */
  public async signup(email: string, password: string, name: string, organizationName: string): Promise<AuthUser | null> {
    try {
      const res = await fetch(`${this.baseUrl}/api/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, name, organization_name: organizationName }),
      });
      if (!res.ok) return null;
      const user = await res.json();
      if (user.token) {
        this.token = user.token;
        try { await AsyncStorage.setItem(TOKEN_STORAGE_KEY, user.token); } catch { /* persistence best-effort */ }
      }
      return user;
    } catch {
      return null;
    }
  }

  /**
   * Uploads a real .onnx model file for local inference in the Agent Sandbox — see
   * backend/app/agent_eval/model_store.py for why ONNX specifically (not
   * pickle/joblib, which can execute arbitrary code on load) and the fixed 8-feature
   * input contract the model must accept. `file` is the shape React Native's fetch
   * expects for a picked document: { uri, name, type }.
   */
  public async uploadModelFile(file: { uri: string; name: string; type?: string; webFile?: Blob }): Promise<any | null> {
    try {
      const form = new FormData();
      if (file.webFile) {
        // Web: expo-document-picker hands back a real Blob/File via `.file`. The RN
        // {uri,name,type} object form below is meaningless to the browser's FormData —
        // fetch silently sends an empty/malformed part and the backend 422s.
        form.append('file', file.webFile, file.name);
      } else {
        // @ts-ignore — React Native's FormData accepts this {uri,name,type} shape for
        // file fields; the DOM FormData typings don't know about it, hence the ignore.
        form.append('file', { uri: file.uri, name: file.name, type: file.type || 'application/octet-stream' });
      }

      const headers: Record<string, string> = {};
      if (this.token) headers['Authorization'] = `Bearer ${this.token}`;
      // Deliberately no Content-Type here — fetch sets the multipart boundary itself
      // when the body is a FormData; setting it manually breaks the upload.

      const res = await fetch(`${this.baseUrl}/api/eval/upload-model`, {
        method: 'POST',
        headers,
        body: form,
      });
      const body = await res.json().catch(() => null);
      if (!res.ok) {
        // FastAPI's own validation errors put an array of {loc,msg,...} objects in
        // `detail`, not a string — rendering that directly in a <Text> crashes the tree.
        const detail = body?.detail;
        const message = typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? detail.map((d: any) => d?.msg || JSON.stringify(d)).join('; ')
            : `Upload failed (${res.status})`;
        return { error: message };
      }
      return body;
    } catch (err: any) {
      return { error: err?.message || 'Upload failed' };
    }
  }

  /**
   * Simulation Status & Telemetry
   */
  public async getSimulationStatus(): Promise<any> {
    try {
      const res = await fetch(`${this.baseUrl}/api/simulation/status`, {
        headers: this.getHeaders(),
      });
      if (!res.ok) throw new Error('Status fetch failed');
      return await res.json();
    } catch {
      return null;
    }
  }

  /**
   * Simulation Control Action (start, pause, resume, step, stop)
   */
  public async sendSimulationControl(action: 'start' | 'pause' | 'resume' | 'step' | 'stop', steps: number = 1): Promise<any> {
    try {
      const res = await fetch(`${this.baseUrl}/api/simulation/control`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ action, steps }),
      });
      return await res.json();
    } catch {
      return { status: 'offline_fallback', action };
    }
  }

  /**
   * Fetch Citizens List
   */
  public async getCitizens(limit: number = 50, offset: number = 0): Promise<any[]> {
    try {
      const res = await fetch(`${this.baseUrl}/api/citizens/?limit=${limit}&offset=${offset}`, {
        headers: this.getHeaders(),
      });
      if (!res.ok) throw new Error('Citizens fetch failed');
      return await res.json();
    } catch {
      return [];
    }
  }

  /**
   * Fetch Specific Citizen by ID
   */
  public async getCitizen(id: string): Promise<any> {
    try {
      const res = await fetch(`${this.baseUrl}/api/citizens/${id}`, {
        headers: this.getHeaders(),
      });
      if (!res.ok) throw new Error('Citizen not found');
      return await res.json();
    } catch {
      return null;
    }
  }

  /**
   * Fetch Real-time Incidents & Events
   */
  public async getEvents(limit: number = 30): Promise<any[]> {
    try {
      const res = await fetch(`${this.baseUrl}/api/events/?limit=${limit}`, {
        headers: this.getHeaders(),
      });
      if (!res.ok) throw new Error('Events fetch failed');
      return await res.json();
    } catch {
      return [];
    }
  }

  /**
   * Fetch Digital Twin Environments
   */
  public async getTwinEnvironments(): Promise<any[]> {
    try {
      const res = await fetch(`${this.baseUrl}/api/twin-platform/environments`, {
        headers: this.getHeaders(),
      });
      if (!res.ok) throw new Error('Twins fetch failed');
      return await res.json();
    } catch {
      return [];
    }
  }

  /**
   * Run Agent Evaluation Sandbox Test
   */
  public async runAgentEvaluation(payload: any): Promise<any> {
    try {
      const res = await fetch(`${this.baseUrl}/api/eval/run-test`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(payload),
      });
      return await res.json();
    } catch {
      return null;
    }
  }

  /**
   * Disasters API
   */
  public async getActiveDisasters(): Promise<any[]> {
    try {
      const res = await fetch(`${this.baseUrl}/api/disasters/active`, {
        headers: this.getHeaders(),
      });
      if (!res.ok) throw new Error('Disasters fetch failed');
      return await res.json();
    } catch {
      return [];
    }
  }

  public async triggerDisaster(disaster_type: string, intensity: number = 0.7): Promise<any | null> {
    try {
      const res = await fetch(`${this.baseUrl}/api/disasters/trigger`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ disaster_type, intensity }),
      });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }

  public async resolveDisaster(disasterId: string): Promise<boolean> {
    try {
      const res = await fetch(`${this.baseUrl}/api/disasters/${disasterId}/resolve`, {
        method: 'POST',
        headers: this.getHeaders(),
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  /**
   * Demographics API
   */
  public async getPopulationLiveStats(): Promise<any | null> {
    try {
      const res = await fetch(`${this.baseUrl}/api/demographics/live-stats`, {
        headers: this.getHeaders(),
      });
      if (!res.ok) return null;
      const body = await res.json();
      return body.status === 'no_data' ? null : body;
    } catch {
      return null;
    }
  }

  /**
   * AI Advisor scorecard
   */
  public async getAdvisorScorecard(): Promise<any | null> {
    try {
      const res = await fetch(`${this.baseUrl}/api/ai-advisor/scorecard`, {
        headers: this.getHeaders(),
      });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }

  /**
   * Social Media API
   */
  public async getTrendingTopics(): Promise<any[]> {
    try {
      const res = await fetch(`${this.baseUrl}/api/social-media/trending`, {
        headers: this.getHeaders(),
      });
      if (!res.ok) throw new Error('Trending fetch failed');
      return await res.json();
    } catch {
      return [];
    }
  }

  public async triggerTopic(hashtag: string, topic: string, category: string = 'news'): Promise<any> {
    try {
      const res = await fetch(`${this.baseUrl}/api/social-media/trigger-topic`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ hashtag, topic, category }),
      });
      return await res.json();
    } catch {
      return { hashtag, topic, mentions: 1 };
    }
  }

  /**
   * AI City Advisor API
   */
  public async getCityAdvisorAnalysis(): Promise<any> {
    try {
      const res = await fetch(`${this.baseUrl}/api/ai-advisor/analyze`, {
        headers: this.getHeaders(),
      });
      if (!res.ok) throw new Error('Advisor fetch failed');
      return await res.json();
    } catch {
      return null;
    }
  }

  public async queryCityAdvisor(scenario: string): Promise<any> {
    try {
      const res = await fetch(`${this.baseUrl}/api/ai-advisor/scenario`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ scenario }),
      });
      return await res.json();
    } catch {
      return null;
    }
  }

  /**
   * Infrastructure API
   */
  public async getInfrastructureProjects(): Promise<any[]> {
    try {
      const res = await fetch(`${this.baseUrl}/api/infrastructure/projects`, {
        headers: this.getHeaders(),
      });
      if (!res.ok) throw new Error('Projects fetch failed');
      return await res.json();
    } catch {
      return [];
    }
  }

  /**
   * Elections API
   */
  public async getElectionsStatus(): Promise<any> {
    try {
      const res = await fetch(`${this.baseUrl}/api/elections/`, {
        headers: this.getHeaders(),
      });
      if (!res.ok) throw new Error('Elections fetch failed');
      return await res.json();
    } catch {
      return null;
    }
  }

  /**
   * Real-Time WebSocket Telemetry Connection
   */
  public connectWebSocket(onMessage: (data: any) => void) {
    this.wsListeners.push(onMessage);

    if (!this.ws || this.ws.readyState === WebSocket.CLOSED) {
      this.initWebSocket();
    }
  }

  private initWebSocket() {
    try {
      const wsUrl = this.baseUrl.replace(/^http/, 'ws') + '/ws/simulation';
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.isConnected = true;
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.wsListeners.forEach((listener) => listener(data));
        } catch {
          // ignore non-json
        }
      };

      this.ws.onerror = () => {
        // graceful
      };

      this.ws.onclose = () => {
        // will retry
      };
    } catch {
      // ignore
    }
  }

  private reconnectWebSocket() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.initWebSocket();
  }
}

export const api = new ApiService();
