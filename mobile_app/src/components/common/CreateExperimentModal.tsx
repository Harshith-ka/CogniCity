import React, { useState } from 'react';
import { View, Text, StyleSheet, Modal, TouchableOpacity, ScrollView, TextInput } from 'react-native';
import { useApp } from '../../context/AppContext';

export const CreateExperimentModal: React.FC = () => {
  const { 
    isCreateExpOpen, 
    setIsCreateExpOpen, 
    addExperiment, 
    twins, 
    agents,
    setActiveTab 
  } = useApp();

  const [title, setTitle] = useState('');
  const [selectedEnv, setSelectedEnv] = useState(twins[0]?.name || 'Smart City Metropolitan');
  const [population, setPopulation] = useState(10000);
  const [durationDays, setDurationDays] = useState(30);
  const [scenario, setScenario] = useState('Monsoon Flooding & Signal Outage');
  const [selectedAgentId, setSelectedAgentId] = useState(agents[0]?.id || 'agent_traffic_rl');

  const populationOptions = [1000, 5000, 10000, 25000, 50000];
  const durationOptions = [7, 14, 30, 60, 90];
  const scenarioPresets = [
    'Monsoon Flooding & Signal Outage',
    'Emergency Casualty Influx',
    'Morning Rush Hour Congestion',
    'Subway Line Transit Strike',
    'Severe Monsoon Flood Warning',
  ];

  const handleRun = () => {
    const chosenAgent = agents.find((a) => a.id === selectedAgentId) || agents[0];
    
    addExperiment({
      title: title || `${chosenAgent.name} - ${scenario}`,
      environment: selectedEnv,
      population,
      durationDays,
      scenario,
      agentName: chosenAgent.name,
    });

    setIsCreateExpOpen(false);
    setActiveTab('experiment_watch');
  };

  return (
    <Modal
      visible={isCreateExpOpen}
      animationType="slide"
      transparent={true}
      onRequestClose={() => setIsCreateExpOpen(false)}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.sheetContainer}>
          {/* Header */}
          <View style={styles.headerRow}>
            <View style={styles.titleRow}>
              <View style={styles.iconBox}>
                <Text style={styles.iconEmoji}>⚡</Text>
              </View>
              <View>
                <Text style={styles.titleText}>Create Experiment</Text>
                <Text style={styles.subText}>Run scalable simulations in cloud sandbox</Text>
              </View>
            </View>
            <TouchableOpacity onPress={() => setIsCreateExpOpen(false)} style={styles.closeBtn}>
              <Text style={styles.closeText}>✕</Text>
            </TouchableOpacity>
          </View>

          {/* Form Scroll */}
          <ScrollView style={styles.formScroll} showsVerticalScrollIndicator={false}>
            {/* 1. Experiment Name */}
            <View style={styles.fieldGroup}>
              <Text style={styles.fieldLabel}>EXPERIMENT TITLE (OPTIONAL)</Text>
              <TextInput
                style={styles.textInput}
                placeholder="e.g. Rush Hour RL Optimization Run #4"
                placeholderTextColor="#64748b"
                value={title}
                onChangeText={setTitle}
              />
            </View>

            {/* 2. Environment Selection */}
            <View style={styles.fieldGroup}>
              <Text style={styles.fieldLabel}>SELECT DIGITAL TWIN ENVIRONMENT</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.pillsScroll}>
                {twins.map((t) => (
                  <TouchableOpacity
                    key={t.id}
                    onPress={() => setSelectedEnv(t.name)}
                    style={[styles.pillBtn, selectedEnv === t.name && styles.pillBtnActive]}
                  >
                    <Text style={styles.pillEmoji}>{t.icon}</Text>
                    <Text style={[styles.pillText, selectedEnv === t.name && styles.pillTextActive]}>
                      {t.name.split(' ')[0]}
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>

            {/* 3. Target AI Agent */}
            <View style={styles.fieldGroup}>
              <Text style={styles.fieldLabel}>TESTING AI AGENT MODEL</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.pillsScroll}>
                {agents.map((a) => (
                  <TouchableOpacity
                    key={a.id}
                    onPress={() => setSelectedAgentId(a.id)}
                    style={[styles.pillBtn, selectedAgentId === a.id && styles.pillBtnActiveIndigo]}
                  >
                    <Text style={styles.pillEmoji}>{a.icon}</Text>
                    <Text style={[styles.pillText, selectedAgentId === a.id && styles.pillTextActive]}>
                      {a.name}
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>

            {/* 4. Population Scale */}
            <View style={styles.fieldGroup}>
              <View style={styles.labelRow}>
                <Text style={styles.fieldLabel}>POPULATION SCALE</Text>
                <Text style={styles.valBadge}>{population.toLocaleString()} Agents</Text>
              </View>
              <View style={styles.optionsRow}>
                {populationOptions.map((pop) => (
                  <TouchableOpacity
                    key={pop}
                    onPress={() => setPopulation(pop)}
                    style={[styles.optionPill, population === pop && styles.optionPillActive]}
                  >
                    <Text style={[styles.optionText, population === pop && styles.optionTextActive]}>
                      {pop >= 1000 ? `${pop / 1000}k` : pop}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            {/* 5. Duration */}
            <View style={styles.fieldGroup}>
              <View style={styles.labelRow}>
                <Text style={styles.fieldLabel}>SIMULATION HORIZON</Text>
                <Text style={styles.valBadge}>{durationDays} Days</Text>
              </View>
              <View style={styles.optionsRow}>
                {durationOptions.map((dur) => (
                  <TouchableOpacity
                    key={dur}
                    onPress={() => setDurationDays(dur)}
                    style={[styles.optionPill, durationDays === dur && styles.optionPillActive]}
                  >
                    <Text style={[styles.optionText, durationDays === dur && styles.optionTextActive]}>
                      {dur}d
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            {/* 6. Scenario Presets */}
            <View style={styles.fieldGroup}>
              <Text style={styles.fieldLabel}>SCENARIO STRESS CONDITION</Text>
              <View style={styles.scenariosList}>
                {scenarioPresets.map((scen, idx) => (
                  <TouchableOpacity
                    key={idx}
                    onPress={() => setScenario(scen)}
                    style={[styles.scenarioCard, scenario === scen && styles.scenarioCardActive]}
                  >
                    <Text style={[styles.scenarioRadio, scenario === scen && styles.radioActive]}>
                      {scenario === scen ? '●' : '○'}
                    </Text>
                    <Text style={[styles.scenarioTitle, scenario === scen && styles.scenarioTitleActive]}>
                      {scen}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </ScrollView>

          {/* Action Footer */}
          <View style={styles.footer}>
            <View style={styles.costInfo}>
              <Text style={styles.costLabel}>Estimated Compute:</Text>
              <Text style={styles.costVal}>500 Credits (~₹25)</Text>
            </View>

            <TouchableOpacity onPress={handleRun} style={styles.launchBtn}>
              <Text style={styles.launchBtnText}>⚡ Run in Cloud</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'flex-end',
  },
  sheetContainer: {
    backgroundColor: '#0f172a',
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    padding: 16,
    maxHeight: '90%',
    borderTopWidth: 1,
    borderTopColor: '#334155',
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
    paddingBottom: 12,
    marginBottom: 8,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  iconBox: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: '#312e81',
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconEmoji: {
    fontSize: 18,
  },
  titleText: {
    fontSize: 16,
    fontWeight: '800',
    color: '#ffffff',
  },
  subText: {
    fontSize: 10,
    color: '#94a3b8',
    marginTop: 1,
  },
  closeBtn: {
    backgroundColor: '#1e293b',
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeText: {
    color: '#cbd5e1',
    fontSize: 14,
    fontWeight: '700',
  },
  formScroll: {
    paddingVertical: 8,
    maxHeight: 460,
  },
  fieldGroup: {
    marginBottom: 14,
  },
  labelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  fieldLabel: {
    fontSize: 10,
    fontFamily: 'monospace',
    fontWeight: '800',
    color: '#94a3b8',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  valBadge: {
    fontSize: 11,
    fontFamily: 'monospace',
    fontWeight: '800',
    color: '#818cf8',
  },
  textInput: {
    backgroundColor: '#1e293b',
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: '#ffffff',
    fontSize: 12,
    borderWidth: 1,
    borderColor: '#334155',
  },
  pillsScroll: {
    flexDirection: 'row',
  },
  pillBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1e293b',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 12,
    marginRight: 8,
    gap: 6,
    borderWidth: 1,
    borderColor: '#334155',
  },
  pillBtnActive: {
    backgroundColor: '#4f46e5',
    borderColor: '#818cf8',
  },
  pillBtnActiveIndigo: {
    backgroundColor: '#3b0764',
    borderColor: '#a855f7',
  },
  pillEmoji: {
    fontSize: 14,
  },
  pillText: {
    fontSize: 11,
    color: '#94a3b8',
    fontWeight: '700',
  },
  pillTextActive: {
    color: '#ffffff',
  },
  optionsRow: {
    flexDirection: 'row',
    gap: 6,
  },
  optionPill: {
    flex: 1,
    backgroundColor: '#1e293b',
    paddingVertical: 8,
    borderRadius: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  optionPillActive: {
    backgroundColor: '#4f46e5',
    borderColor: '#818cf8',
  },
  optionText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#94a3b8',
    fontFamily: 'monospace',
  },
  optionTextActive: {
    color: '#ffffff',
  },
  scenariosList: {
    gap: 6,
  },
  scenarioCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1e293b',
    padding: 10,
    borderRadius: 12,
    gap: 10,
    borderWidth: 1,
    borderColor: '#334155',
  },
  scenarioCardActive: {
    backgroundColor: '#1e1b4b',
    borderColor: '#6366f1',
  },
  scenarioRadio: {
    fontSize: 14,
    color: '#64748b',
  },
  radioActive: {
    color: '#818cf8',
  },
  scenarioTitle: {
    fontSize: 11,
    color: '#cbd5e1',
    fontWeight: '600',
    flex: 1,
  },
  scenarioTitleActive: {
    color: '#ffffff',
    fontWeight: '800',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#1e293b',
    paddingTop: 12,
  },
  costInfo: {
    flex: 1,
  },
  costLabel: {
    fontSize: 9,
    color: '#64748b',
  },
  costVal: {
    fontSize: 11,
    fontWeight: '800',
    color: '#34d399',
    fontFamily: 'monospace',
    marginTop: 1,
  },
  launchBtn: {
    backgroundColor: '#4f46e5',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 14,
  },
  launchBtnText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '900',
  },
});
