import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, Dimensions, TouchableOpacity, ScrollView } from 'react-native';
import { Ionicons, Feather, MaterialCommunityIcons } from '@expo/vector-icons';
import { useApp } from '../../context/AppContext';
import { SimulationEntity } from '../../types';
import { colors, typography, layout } from '../../constants/theme';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const MAP_WIDTH = SCREEN_WIDTH - 28;
const MAP_HEIGHT = 380;

export const LiveMapView: React.FC = () => {
  const {
    selectedTwin,
    simTime,
    toggleSimulationPlay,
    setSpeedMultiplier,
    stepForward,
    restartSimulation,
    setSelectedCitizen,
    citizens,
    showToast,
  } = useApp();

  const [filterLayer, setFilterLayer] = useState<'all' | 'vehicles' | 'agents' | 'incidents'>('all');
  const [selectedEntity, setSelectedEntity] = useState<SimulationEntity | null>(null);

  // Entities on canvas
  const [entities, setEntities] = useState<SimulationEntity[]>([
    { id: 'b_hosp', type: 'building', subType: 'hospital', name: 'General Hospital', x: 260, y: 50 },
    { id: 'b_gov', type: 'building', subType: 'office', name: 'City Hall', x: 70, y: 60 },
    { id: 'b_sch', type: 'building', subType: 'school', name: 'Metro Institute', x: 170, y: 190 },

    { id: 'v_1', type: 'vehicle', subType: 'car', name: 'Autonomous EV #102', x: 80, y: 130, speed: 2.2 },
    { id: 'v_2', type: 'vehicle', subType: 'bus', name: 'Rapid Transit Line 4', x: 190, y: 130, speed: 1.5 },
    { id: 'v_3', type: 'vehicle', subType: 'car', name: 'EV Taxi #44', x: 290, y: 130, speed: 2.5 },
    { id: 'v_4', type: 'vehicle', subType: 'ambulance', name: 'EMS Unit 9', x: 220, y: 250, speed: 3.0, pulse: true },
    { id: 'v_5', type: 'vehicle', subType: 'police', name: 'Police Cruiser 3', x: 110, y: 250, speed: 2.8 },

    { id: 'a_1', type: 'agent', subType: 'citizen', name: 'Priya S. (Doctor)', x: 240, y: 90 },
    { id: 'a_2', type: 'agent', subType: 'citizen', name: 'Rahul V. (Engineer)', x: 100, y: 80 },
    { id: 'a_3', type: 'agent', subType: 'citizen', name: 'Ananya D. (Student)', x: 160, y: 220 },

    { id: 'inc_1', type: 'incident', subType: 'fire', name: 'Grid Transformer Fire', x: 140, y: 280, pulse: true },
  ]);

  // Motion animation loop for live simulation
  useEffect(() => {
    if (!simTime.isRunning) return;

    const interval = setInterval(() => {
      setEntities((prev) =>
        prev.map((ent) => {
          if (ent.type === 'vehicle') {
            let nextX = ent.x + (ent.speed || 1.5);
            if (nextX > MAP_WIDTH - 25) nextX = 20;
            return { ...ent, x: nextX };
          }
          if (ent.type === 'agent') {
            const deltaX = (Math.random() - 0.5) * 2;
            const deltaY = (Math.random() - 0.5) * 2;
            return {
              ...ent,
              x: Math.max(20, Math.min(MAP_WIDTH - 30, ent.x + deltaX)),
              y: Math.max(30, Math.min(MAP_HEIGHT - 40, ent.y + deltaY)),
            };
          }
          return ent;
        })
      );
    }, 60);

    return () => clearInterval(interval);
  }, [simTime.isRunning]);

  const handleEntityPress = (entity: SimulationEntity) => {
    setSelectedEntity(entity);
    if (entity.type === 'agent') {
      const match = citizens.find((c) => c.name.includes(entity.name.split(' ')[0]));
      if (match) {
        setSelectedCitizen(match);
      } else {
        showToast(entity.name, `Agent live coordinates: [${entity.x.toFixed(0)}, ${entity.y.toFixed(0)}]`, 'info');
      }
    } else {
      showToast(entity.name, `Telemetry status: ${entity.subType || entity.type} active in district.`, 'info');
    }
  };

  const filteredEntities = entities.filter((ent) => {
    if (filterLayer === 'all') return true;
    if (filterLayer === 'vehicles') return ent.type === 'vehicle';
    if (filterLayer === 'agents') return ent.type === 'agent';
    if (filterLayer === 'incidents') return ent.type === 'incident' || ent.type === 'building';
    return true;
  });

  const renderEntityIcon = (entity: SimulationEntity) => {
    if (entity.subType === 'hospital') return <Ionicons name="medical" size={14} color={colors.dangerLight} />;
    if (entity.subType === 'office') return <MaterialCommunityIcons name="office-building" size={14} color={colors.primaryLight} />;
    if (entity.subType === 'school') return <Ionicons name="school" size={14} color={colors.purpleLight} />;
    if (entity.subType === 'car') return <Ionicons name="car-sport" size={13} color={colors.cyanLight} />;
    if (entity.subType === 'bus') return <Ionicons name="bus" size={13} color={colors.warningLight} />;
    if (entity.subType === 'ambulance') return <Ionicons name="medical" size={13} color={colors.dangerLight} />;
    if (entity.subType === 'police') return <Ionicons name="shield" size={13} color={colors.primaryLight} />;
    if (entity.subType === 'fire') return <Ionicons name="flame" size={15} color={colors.danger} />;
    if (entity.subType === 'citizen') return <Ionicons name="person" size={12} color={colors.successLight} />;
    return <Feather name="circle" size={10} color={colors.textPrimary} />;
  };

  return (
    <View style={styles.container}>
      {/* Filter Layer Pills */}
      <View style={styles.layerSelector}>
        {(['all', 'vehicles', 'agents', 'incidents'] as const).map((l) => (
          <TouchableOpacity
            key={l}
            onPress={() => setFilterLayer(l)}
            style={[styles.layerPill, filterLayer === l && styles.layerPillActive]}
            activeOpacity={0.7}
          >
            <Text style={[styles.layerText, filterLayer === l && styles.layerTextActive]}>
              {l === 'all' ? 'All Entities' : l === 'vehicles' ? 'Vehicles' : l === 'agents' ? 'Citizens' : 'Incidents'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* 2.5D Isometric Simulation Canvas */}
      <View style={styles.mapCanvas}>
        {/* Isometric Grid Road Lines */}
        <View style={[styles.roadHorizontal, { top: 120 }]} />
        <View style={[styles.roadHorizontal, { top: 240 }]} />
        <View style={[styles.roadVertical, { left: 130 }]} />
        <View style={[styles.roadVertical, { left: 240 }]} />

        {/* Render Entities */}
        {filteredEntities.map((ent) => (
          <TouchableOpacity
            key={ent.id}
            onPress={() => handleEntityPress(ent)}
            style={[
              styles.entityNode,
              { left: ent.x, top: ent.y },
              ent.pulse && styles.pulseNode,
              selectedEntity?.id === ent.id && styles.selectedNode,
            ]}
            activeOpacity={0.7}
          >
            <View style={styles.entityIconBox}>
              {renderEntityIcon(ent)}
            </View>
            <Text style={styles.entityLabel} numberOfLines={1}>
              {ent.name.split(' ')[0]}
            </Text>
          </TouchableOpacity>
        ))}

        {/* Live HUD Overlay */}
        <View style={styles.hudOverlay}>
          <View style={styles.hudBadge}>
            <View style={styles.hudDot} />
            <Text style={styles.hudText}>FPS 60 • 10,000 AGENTS</Text>
          </View>
          <Text style={styles.hudDistrict}>{selectedTwin.name}</Text>
        </View>
      </View>

      {/* Bottom Simulation Control HUD */}
      <View style={styles.controlsCard}>
        <View style={styles.clockRow}>
          <View>
            <Text style={styles.timeTag}>VIRTUAL TIME</Text>
            <Text style={styles.clockValue}>
              Day {simTime.day} • {String(simTime.hour).padStart(2, '0')}:{String(simTime.minute).padStart(2, '0')}:{String(simTime.second).padStart(2, '0')}
            </Text>
          </View>

          <View style={styles.speedPills}>
            {[1, 10, 100].map((s) => (
              <TouchableOpacity
                key={s}
                onPress={() => setSpeedMultiplier(s)}
                style={[styles.speedPill, simTime.speedMultiplier === s && styles.speedPillActive]}
                activeOpacity={0.7}
              >
                <Text style={[styles.speedPillText, simTime.speedMultiplier === s && styles.speedPillTextActive]}>
                  {s}x
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Playback Controls */}
        <View style={styles.actionButtonsRow}>
          <TouchableOpacity onPress={restartSimulation} style={styles.controlBtn} activeOpacity={0.7}>
            <Feather name="rotate-ccw" size={14} color={colors.textSecondary} />
            <Text style={styles.controlBtnText}>Reset</Text>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={toggleSimulationPlay}
            style={[styles.primaryPlayBtn, simTime.isRunning ? styles.bgPause : styles.bgPlay]}
            activeOpacity={0.7}
          >
            <Ionicons
              name={simTime.isRunning ? 'pause' : 'play'}
              size={16}
              color="#ffffff"
            />
            <Text style={styles.primaryPlayText}>
              {simTime.isRunning ? 'Pause Simulation' : 'Run Simulation'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={stepForward} style={styles.controlBtn} activeOpacity={0.7}>
            <Feather name="skip-forward" size={14} color={colors.textSecondary} />
            <Text style={styles.controlBtnText}>Step</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    padding: layout.padding,
    gap: 10,
  },
  layerSelector: {
    flexDirection: 'row',
    backgroundColor: colors.surface,
    borderRadius: layout.radiusMd,
    padding: 3,
    gap: 4,
    borderWidth: 1,
    borderColor: colors.border,
  },
  layerPill: {
    flex: 1,
    paddingVertical: 7,
    borderRadius: layout.radiusSm,
    alignItems: 'center',
  },
  layerPillActive: {
    backgroundColor: colors.primary,
  },
  layerText: {
    fontSize: 10,
    fontWeight: '600',
    color: colors.textMuted,
  },
  layerTextActive: {
    color: '#ffffff',
    fontWeight: '700',
  },
  mapCanvas: {
    height: MAP_HEIGHT,
    backgroundColor: '#090D16',
    borderRadius: layout.radiusLg,
    borderWidth: 1,
    borderColor: colors.border,
    position: 'relative',
    overflow: 'hidden',
  },
  roadHorizontal: {
    position: 'absolute',
    left: 0,
    right: 0,
    height: 18,
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.05)',
  },
  roadVertical: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    width: 18,
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderLeftWidth: 1,
    borderRightWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.05)',
  },
  entityNode: {
    position: 'absolute',
    alignItems: 'center',
    justifyContent: 'center',
  },
  pulseNode: {
    shadowColor: colors.danger,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 6,
    elevation: 4,
  },
  selectedNode: {
    borderWidth: 1,
    borderColor: colors.primaryLight,
    borderRadius: 8,
    padding: 2,
  },
  entityIconBox: {
    width: 26,
    height: 26,
    borderRadius: 7,
    backgroundColor: colors.surfaceElevated,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  entityLabel: {
    fontSize: 8,
    fontWeight: '600',
    color: colors.textSecondary,
    backgroundColor: 'rgba(7, 9, 14, 0.85)',
    paddingHorizontal: 4,
    paddingVertical: 1,
    borderRadius: 4,
    marginTop: 2,
  },
  hudOverlay: {
    position: 'absolute',
    top: 10,
    left: 10,
    right: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  hudBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(7, 9, 14, 0.8)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: layout.radiusSm,
    gap: 5,
    borderWidth: 1,
    borderColor: colors.border,
  },
  hudDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    backgroundColor: colors.success,
  },
  hudText: {
    fontSize: 8.5,
    fontFamily: 'monospace',
    fontWeight: '700',
    color: colors.successLight,
  },
  hudDistrict: {
    fontSize: 10,
    fontWeight: '700',
    color: colors.textPrimary,
    backgroundColor: 'rgba(7, 9, 14, 0.8)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: layout.radiusSm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  controlsCard: {
    backgroundColor: colors.surface,
    borderRadius: layout.radiusLg,
    padding: layout.cardPadding,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 12,
  },
  clockRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  timeTag: {
    ...typography.badge,
    color: colors.textMuted,
  },
  clockValue: {
    fontSize: 13,
    fontWeight: '700',
    fontFamily: 'monospace',
    color: colors.textPrimary,
    marginTop: 1,
  },
  speedPills: {
    flexDirection: 'row',
    backgroundColor: colors.surfaceElevated,
    borderRadius: layout.radiusSm,
    padding: 2,
    gap: 2,
    borderWidth: 1,
    borderColor: colors.border,
  },
  speedPill: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  speedPillActive: {
    backgroundColor: colors.primary,
  },
  speedPillText: {
    fontSize: 9.5,
    fontWeight: '700',
    fontFamily: 'monospace',
    color: colors.textMuted,
  },
  speedPillTextActive: {
    color: '#ffffff',
  },
  actionButtonsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  controlBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceElevated,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: layout.radiusMd,
    gap: 6,
    borderWidth: 1,
    borderColor: colors.border,
  },
  controlBtnText: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  primaryPlayBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    borderRadius: layout.radiusMd,
    gap: 6,
  },
  bgPlay: {
    backgroundColor: colors.primary,
  },
  bgPause: {
    backgroundColor: colors.warning,
  },
  primaryPlayText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '700',
  },
});
