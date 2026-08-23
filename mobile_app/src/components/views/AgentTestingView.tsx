import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, ActivityIndicator } from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import { useApp } from '../../context/AppContext';
import { AIAgent } from '../../types';
import { api } from '../../services/api';

type Protocol = 'mock_benchmark' | 'uploaded_model' | 'rest_webhook' | 'openai_chat';

const PROTOCOL_LABELS: Record<Protocol, string> = {
  mock_benchmark: '⚡ Mock Benchmark',
  uploaded_model: '📁 Upload Model',
  rest_webhook: '🌐 REST Webhook',
  openai_chat: '🤖 OpenAI Chat',
};

const DOMAIN_PRESETS = ['cardiology_uci', 'credit_lending', 'real_estate_housing', 'ecommerce_recsys'];

export const AgentTestingView: React.FC = () => {
  const {
    agents,
    selectedAgent,
    setSelectedAgent,
    setInspectReasoningId,
    setActiveTab,
    showToast
  } = useApp();

  // Real evaluation runner state — this panel talks to the actual backend
  // (POST /api/eval/run-test, POST /api/eval/upload-model), unlike the mock agent
  // list below it, which is browsing pre-installed demo agents.
  const [protocol, setProtocol] = useState<Protocol>('mock_benchmark');
  const [agentName, setAgentName] = useState('My Candidate Model');
  const [domainPreset, setDomainPreset] = useState(DOMAIN_PRESETS[0]);
  const [sampleSize, setSampleSize] = useState('200');
  const [endpointUrl, setEndpointUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [modelInfo, setModelInfo] = useState<any | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [scorecard, setScorecard] = useState<any | null>(null);

  const handlePickModel = async () => {
    const result = await DocumentPicker.getDocumentAsync({
      type: ['application/octet-stream', '*/*'], // ONNX has no universal MIME type across platforms
      copyToCacheDirectory: true,
    });
    if (result.canceled || !result.assets?.[0]) return;
    const file = result.assets[0];
    if (!file.name.toLowerCase().endsWith('.onnx')) {
      showToast('Wrong File Type', 'Only .onnx files are accepted — see why in the notice above.', 'critical');
      return;
    }
    setIsUploading(true);
    setModelInfo(null);
    try {
      // On web, DocumentPicker gives back a real File via `.file` — the RN {uri,name,type}
      // shape means nothing to the browser's fetch/FormData and 422s server-side.
      const res = await api.uploadModelFile({
        uri: file.uri,
        name: file.name,
        type: file.mimeType,
        webFile: (file as any).file,
      });
      if (res?.error) {
        showToast('Model Rejected', res.error, 'critical');
      } else {
        setModelInfo(res);
        showToast('Model Loaded', `${file.name} validated — input shape ${JSON.stringify(res.input_shape)}`, 'success');
      }
    } finally {
      setIsUploading(false);
    }
  };

  const handleRunEvaluation = async () => {
    if (protocol === 'uploaded_model' && !modelInfo) {
      showToast('No Model Loaded', 'Upload a .onnx file before running.', 'critical');
      return;
    }
    setIsRunning(true);
    setScorecard(null);
    try {
      const result = await api.runAgentEvaluation({
        agent_name: agentName,
        domain_preset: domainPreset,
        protocol,
        model_id: protocol === 'uploaded_model' ? modelInfo?.model_id : null,
        endpoint_url: protocol === 'rest_webhook' || protocol === 'openai_chat' ? endpointUrl : null,
        api_key: apiKey || null,
        cohort_distribution: 'balanced_general',
        sample_size: parseInt(sampleSize, 10) || 200,
      });
      if (result) {
        setScorecard(result);
        showToast('Evaluation Complete', `${result.population_size} synthetic citizens evaluated`, 'success');
      } else {
        showToast('Evaluation Failed', 'Could not reach the evaluation backend.', 'critical');
      }
    } finally {
      setIsRunning(false);
    }
  };

  const handleInspectReasoning = (agent: AIAgent) => {
    setInspectReasoningId('traffic_agent');
    setActiveTab('reasoning');
    showToast('Cognitive Inspector', `Inspecting live reasoning steps for ${agent.name}`, 'info');
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer} showsVerticalScrollIndicator={false}>
      {/* Real Evaluation Runner */}
      <View style={styles.runnerCard}>
        <Text style={styles.runnerTitle}>🧪 Test a New Model</Text>
        <Text style={styles.headerSubtitle}>Runs a real evaluation against synthetic citizens via the backend.</Text>

        <View style={styles.protocolRow}>
          {(Object.keys(PROTOCOL_LABELS) as Protocol[]).map((p) => (
            <TouchableOpacity
              key={p}
              onPress={() => { setProtocol(p); setModelInfo(null); setScorecard(null); }}
              style={[styles.protocolChip, protocol === p && styles.protocolChipActive]}
            >
              <Text style={[styles.protocolChipText, protocol === p && styles.protocolChipTextActive]}>
                {PROTOCOL_LABELS[p]}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <TextInput
          style={styles.input}
          value={agentName}
          onChangeText={setAgentName}
          placeholder="Model name"
          placeholderTextColor="#64748b"
        />

        {protocol === 'uploaded_model' && (
          <View style={styles.uploadBox}>
            <Text style={styles.uploadNotice}>
              ONNX only, not pickle/joblib — an arbitrary .pkl file can execute code on load; ONNX
              can't. Model must accept a [1, 8] float32 tensor: age, annual_income, savings,
              monthly_expenses, credit_score_estimate, health_index, stress_level, happiness.
            </Text>
            <TouchableOpacity onPress={handlePickModel} disabled={isUploading} style={styles.pickBtn}>
              {isUploading ? (
                <ActivityIndicator color="#818cf8" size="small" />
              ) : (
                <Text style={styles.pickBtnText}>{modelInfo ? '✓ Change File' : '📁 Pick .onnx File'}</Text>
              )}
            </TouchableOpacity>
            {modelInfo && (
              <Text style={styles.modelInfoText}>
                Input `{modelInfo.input_name}` {JSON.stringify(modelInfo.input_shape)} → outputs {modelInfo.output_names?.join(', ')}
              </Text>
            )}
          </View>
        )}

        {(protocol === 'rest_webhook' || protocol === 'openai_chat') && (
          <>
            <TextInput
              style={styles.input}
              value={endpointUrl}
              onChangeText={setEndpointUrl}
              placeholder={protocol === 'rest_webhook' ? 'http://host.docker.internal:9000/predict' : 'https://api.openai.com/v1/chat/completions'}
              placeholderTextColor="#64748b"
              autoCapitalize="none"
            />
            <TextInput
              style={styles.input}
              value={apiKey}
              onChangeText={setApiKey}
              placeholder="API key (optional)"
              placeholderTextColor="#64748b"
              secureTextEntry
            />
          </>
        )}

        <View style={styles.rowGap}>
          <View style={styles.halfField}>
            <Text style={styles.fieldLabel}>DOMAIN</Text>
            <View style={styles.domainRow}>
              {DOMAIN_PRESETS.map((d) => (
                <TouchableOpacity key={d} onPress={() => setDomainPreset(d)} style={[styles.domainChip, domainPreset === d && styles.protocolChipActive]}>
                  <Text style={[styles.domainChipText, domainPreset === d && styles.protocolChipTextActive]}>{d.split('_')[0]}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        </View>

        <TextInput
          style={styles.input}
          value={sampleSize}
          onChangeText={setSampleSize}
          placeholder="Sample size"
          placeholderTextColor="#64748b"
          keyboardType="number-pad"
        />

        <TouchableOpacity onPress={handleRunEvaluation} disabled={isRunning} style={styles.runBtn}>
          {isRunning ? <ActivityIndicator color="#fff" size="small" /> : <Text style={styles.runBtnText}>🚀 Run Evaluation</Text>}
        </TouchableOpacity>

        {scorecard && (
          <View style={styles.resultBox}>
            <Text style={styles.resultTitle}>{scorecard.agent_name} — {scorecard.population_size} citizens</Text>
            <View style={styles.statsTwoCol}>
              <View style={styles.statPill}>
                <Text style={styles.statKey}>Robustness:</Text>
                <Text style={styles.statVal}>{scorecard.robustness_score}%</Text>
              </View>
              <View style={styles.statPill}>
                <Text style={styles.statKey}>Adoption:</Text>
                <Text style={styles.statVal}>{scorecard.overall_adoption_rate}%</Text>
              </View>
              <View style={styles.statPill}>
                <Text style={styles.statKey}>Fairness:</Text>
                <Text style={styles.statVal}>{scorecard.fairness_index}</Text>
              </View>
              <View style={styles.statPill}>
                <Text style={styles.statKey}>Adversarial Fail:</Text>
                <Text style={styles.statVal}>{scorecard.adversarial_failure_rate}%</Text>
              </View>
            </View>
            <Text style={styles.descText}>{scorecard.executive_summary}</Text>
          </View>
        )}
      </View>

      {/* Header Info */}
      <View style={styles.headerBox}>
        <View style={styles.headerTitleRow}>
          <Text style={styles.headerTitle}>My AI Agents</Text>
          <Text style={styles.countBadge}>{agents.length} Models</Text>
        </View>
        <Text style={styles.headerSubtitle}>Continuous evaluation & synthetic stress testing</Text>
      </View>

      {/* Agents List */}
      <View style={styles.agentsList}>
        {agents.map((agent) => {
          const isSelected = selectedAgent?.id === agent.id;
          const isRunning = agent.status === 'running';

          return (
            <TouchableOpacity
              key={agent.id}
              onPress={() => setSelectedAgent(agent)}
              style={[styles.agentCard, isSelected && styles.agentCardSelected]}
            >
              {/* Top Row */}
              <View style={styles.cardTopRow}>
                <View style={styles.agentProfile}>
                  <View style={styles.iconBox}>
                    <Text style={styles.iconText}>{agent.icon}</Text>
                  </View>
                  <View>
                    <View style={styles.nameRow}>
                      <Text style={styles.agentName}>{agent.name}</Text>
                      <Text style={styles.versionText}>{agent.version}</Text>
                    </View>
                    <Text style={styles.envText}>
                      Env: <Text style={styles.envHighlight}>{agent.environment}</Text>
                    </Text>
                  </View>
                </View>

                <View style={[styles.statusBadge, isRunning ? styles.runningBadge : styles.idleBadge]}>
                  <View style={[styles.dot, isRunning ? styles.runningDot : styles.idleDot]} />
                  <Text style={[styles.statusText, isRunning ? styles.runningText : styles.idleText]}>
                    {agent.status}
                  </Text>
                </View>
              </View>

              {/* Metrics Grid */}
              <View style={styles.metricsGrid}>
                <View style={styles.metricBox}>
                  <Text style={styles.metricLabel}>Performance</Text>
                  <Text style={styles.metricValPrimary}>{agent.performance}%</Text>
                </View>

                <View style={styles.metricBox}>
                  <Text style={styles.metricLabel}>Robustness</Text>
                  <Text style={styles.metricValCyan}>{agent.robustness}%</Text>
                </View>

                <View style={styles.metricBox}>
                  <Text style={styles.metricLabel}>Fairness</Text>
                  <Text style={styles.metricValGreen}>{agent.fairness}%</Text>
                </View>
              </View>

              {/* Expanded details when selected */}
              {isSelected && (
                <View style={styles.expandedSection}>
                  <Text style={styles.descText}>{agent.description}</Text>

                  <View style={styles.statsTwoCol}>
                    <View style={styles.statPill}>
                      <Text style={styles.statKey}>Agents Tested:</Text>
                      <Text style={styles.statVal}>{agent.agentsTested.toLocaleString()}</Text>
                    </View>
                    <View style={styles.statPill}>
                      <Text style={styles.statKey}>Interactions:</Text>
                      <Text style={styles.statVal}>{agent.interactions}</Text>
                    </View>
                    <View style={styles.statPill}>
                      <Text style={styles.statKey}>Latency:</Text>
                      <Text style={styles.statVal}>{agent.latencyMs} ms</Text>
                    </View>
                    <View style={styles.statPill}>
                      <Text style={styles.statKey}>Drift Risk:</Text>
                      <Text style={[styles.statVal, { color: agent.driftRisk === 'low' ? '#34d399' : '#fbbf24' }]}>
                        {agent.driftRisk.toUpperCase()}
                      </Text>
                    </View>
                  </View>

                  {agent.lastReasoningStep && (
                    <View style={styles.reasoningSnippet}>
                      <Text style={styles.snippetLabel}>🧠 Latest Decision Step</Text>
                      <Text style={styles.snippetText}>{agent.lastReasoningStep}</Text>
                    </View>
                  )}

                  <TouchableOpacity
                    onPress={() => handleInspectReasoning(agent)}
                    style={styles.inspectBtn}
                  >
                    <Text style={styles.inspectBtnText}>🧠 Inspect Reasoning Chain</Text>
                  </TouchableOpacity>
                </View>
              )}
            </TouchableOpacity>
          );
        })}
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
    marginBottom: 4,
  },
  headerTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#ffffff',
  },
  countBadge: {
    fontSize: 10,
    fontFamily: 'monospace',
    color: '#a5b4fc',
    backgroundColor: '#1e1b4b',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#4338ca',
  },
  headerSubtitle: {
    fontSize: 11,
    color: '#94a3b8',
    marginTop: 2,
  },
  runnerCard: {
    backgroundColor: 'rgba(15, 23, 42, 0.9)',
    borderRadius: 24,
    padding: 16,
    borderWidth: 1,
    borderColor: '#312e81',
    gap: 10,
  },
  runnerTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: '#ffffff',
  },
  protocolRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 4,
  },
  protocolChip: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 10,
    backgroundColor: '#111827',
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  protocolChipActive: {
    backgroundColor: '#312e81',
    borderColor: '#6366f1',
  },
  protocolChipText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#94a3b8',
  },
  protocolChipTextActive: {
    color: '#c7d2fe',
  },
  input: {
    backgroundColor: '#0b1120',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#1e293b',
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: '#e2e8f0',
    fontSize: 13,
  },
  uploadBox: {
    backgroundColor: '#0b1120',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#312e81',
    padding: 12,
    gap: 8,
  },
  uploadNotice: {
    fontSize: 10.5,
    lineHeight: 15,
    color: '#94a3b8',
  },
  pickBtn: {
    backgroundColor: '#1e1b4b',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#4338ca',
    paddingVertical: 10,
    alignItems: 'center',
  },
  pickBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#a5b4fc',
  },
  modelInfoText: {
    fontSize: 10.5,
    color: '#34d399',
    fontFamily: 'monospace',
  },
  rowGap: {
    gap: 8,
  },
  halfField: {
    gap: 6,
  },
  fieldLabel: {
    fontSize: 9.5,
    fontWeight: '700',
    color: '#64748b',
    letterSpacing: 0.5,
  },
  domainRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  domainChip: {
    paddingHorizontal: 8,
    paddingVertical: 5,
    borderRadius: 8,
    backgroundColor: '#111827',
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  domainChipText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#94a3b8',
    textTransform: 'capitalize',
  },
  runBtn: {
    backgroundColor: '#4f46e5',
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 2,
  },
  runBtnText: {
    fontSize: 13,
    fontWeight: '800',
    color: '#ffffff',
  },
  resultBox: {
    backgroundColor: '#0b1120',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#1e293b',
    padding: 12,
    gap: 8,
  },
  resultTitle: {
    fontSize: 12.5,
    fontWeight: '700',
    color: '#ffffff',
  },
  agentsList: {
    gap: 10,
  },
  agentCard: {
    backgroundColor: 'rgba(15, 23, 42, 0.9)',
    borderRadius: 24,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1e293b',
  },
  agentCardSelected: {
    borderColor: '#6366f1',
    backgroundColor: '#111827',
  },
  cardTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  agentProfile: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  iconBox: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: '#1e1b4b',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#4338ca',
  },
  iconText: {
    fontSize: 22,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  agentName: {
    fontSize: 14,
    fontWeight: '800',
    color: '#ffffff',
  },
  versionText: {
    fontSize: 10,
    color: '#64748b',
    fontFamily: 'monospace',
  },
  envText: {
    fontSize: 11,
    color: '#94a3b8',
    marginTop: 2,
  },
  envHighlight: {
    color: '#818cf8',
    fontWeight: '700',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    gap: 4,
  },
  runningBadge: {
    backgroundColor: 'rgba(6, 78, 59, 0.5)',
    borderWidth: 1,
    borderColor: '#065f46',
  },
  idleBadge: {
    backgroundColor: '#1e293b',
    borderWidth: 1,
    borderColor: '#334155',
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  runningDot: {
    backgroundColor: '#10b981',
  },
  idleDot: {
    backgroundColor: '#f59e0b',
  },
  statusText: {
    fontSize: 10,
    fontWeight: '700',
    textTransform: 'capitalize',
  },
  runningText: {
    color: '#34d399',
  },
  idleText: {
    color: '#fcd34d',
  },
  metricsGrid: {
    flexDirection: 'row',
    gap: 6,
    marginTop: 12,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#1e293b',
  },
  metricBox: {
    flex: 1,
    backgroundColor: '#090d16',
    borderRadius: 12,
    padding: 8,
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 9,
    color: '#94a3b8',
    fontWeight: '600',
  },
  metricValPrimary: {
    fontSize: 13,
    fontWeight: '900',
    color: '#818cf8',
    fontFamily: 'monospace',
    marginTop: 2,
  },
  metricValCyan: {
    fontSize: 13,
    fontWeight: '900',
    color: '#38bdf8',
    fontFamily: 'monospace',
    marginTop: 2,
  },
  metricValGreen: {
    fontSize: 13,
    fontWeight: '900',
    color: '#34d399',
    fontFamily: 'monospace',
    marginTop: 2,
  },
  expandedSection: {
    marginTop: 12,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#1e293b',
    gap: 10,
  },
  descText: {
    fontSize: 12,
    color: '#cbd5e1',
    lineHeight: 16,
  },
  statsTwoCol: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  statPill: {
    flexBasis: '48%',
    flexDirection: 'row',
    justifyContent: 'space-between',
    backgroundColor: '#1e293b',
    padding: 8,
    borderRadius: 8,
  },
  statKey: {
    fontSize: 10,
    color: '#94a3b8',
  },
  statVal: {
    fontSize: 10,
    fontWeight: '700',
    color: '#ffffff',
    fontFamily: 'monospace',
  },
  reasoningSnippet: {
    backgroundColor: '#3b0764',
    padding: 10,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#7e22ce',
  },
  snippetLabel: {
    fontSize: 10,
    fontWeight: '800',
    color: '#d8b4fe',
    marginBottom: 2,
  },
  snippetText: {
    fontSize: 11,
    color: '#f3e8ff',
    lineHeight: 15,
  },
  inspectBtn: {
    backgroundColor: '#7c3aed',
    paddingVertical: 12,
    borderRadius: 14,
    alignItems: 'center',
  },
  inspectBtnText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '800',
  },
});
