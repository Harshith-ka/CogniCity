import React from 'react';
import { StyleSheet, View, SafeAreaView, StatusBar, Platform } from 'react-native';
import { AppProvider, useApp } from './src/context/AppContext';

// Common Components
import { Header } from './src/components/common/Header';
import { BottomNav } from './src/components/common/BottomNav';
import { ToastContainer } from './src/components/common/ToastContainer';
import { CitizenDossierModal } from './src/components/common/CitizenDossierModal';
import { CreateExperimentModal } from './src/components/common/CreateExperimentModal';
import { ReasoningModal } from './src/components/common/ReasoningModal';
import { AuthModal } from './src/components/common/AuthModal';

// Views
import { HomeView } from './src/components/views/HomeView';
import { TwinsView } from './src/components/views/TwinsView';
import { LiveMapView } from './src/components/views/LiveMapView';
import { AgentTestingView } from './src/components/views/AgentTestingView';
import { PopulationExplorerView } from './src/components/views/PopulationExplorerView';
import { ReasoningInspectorView } from './src/components/views/ReasoningInspectorView';
import { AlertsView } from './src/components/views/AlertsView';
import { AnalyticsView } from './src/components/views/AnalyticsView';
import { ExperimentComparisonView } from './src/components/views/ExperimentComparisonView';
import { MarketplaceView } from './src/components/views/MarketplaceView';
import { BillingView } from './src/components/views/BillingView';
import { CollaborationView } from './src/components/views/CollaborationView';
import { ReportGeneratorView } from './src/components/views/ReportGeneratorView';
import { GovModeView } from './src/components/views/GovModeView';
import { ExperimentWatchView } from './src/components/views/ExperimentWatchView';

// New Feature Views
import { DisasterPandemicView } from './src/components/views/DisasterPandemicView';
import { SocialFeedView } from './src/components/views/SocialFeedView';
import { AIAdvisorView } from './src/components/views/AIAdvisorView';
import { InfrastructureView } from './src/components/views/InfrastructureView';
import { ElectionsView } from './src/components/views/ElectionsView';
import { AccountAuthView } from './src/components/views/AccountAuthView';

const MainAppContent: React.FC = () => {
  const { activeTab, isAuthenticated, isRestoringSession } = useApp();

  const renderActiveView = () => {
    switch (activeTab) {
      case 'home': return <HomeView />;
      case 'twins': return <TwinsView />;
      case 'live_map': return <LiveMapView />;
      case 'agents': return <AgentTestingView />;
      case 'experiments': return <ExperimentWatchView />;
      case 'population': return <PopulationExplorerView />;
      case 'reasoning': return <ReasoningInspectorView />;
      case 'alerts': return <AlertsView />;
      case 'analytics': return <AnalyticsView />;
      case 'comparison': return <ExperimentComparisonView />;
      case 'marketplace': return <MarketplaceView />;
      case 'billing': return <BillingView />;
      case 'collaboration': return <CollaborationView />;
      case 'reports': return <ReportGeneratorView />;
      case 'gov_mode': return <GovModeView />;
      case 'experiment_watch': return <ExperimentWatchView />;
      case 'disasters_pandemics': return <DisasterPandemicView />;
      case 'social_feed': return <SocialFeedView />;
      case 'ai_advisor': return <AIAdvisorView />;
      case 'infrastructure': return <InfrastructureView />;
      case 'elections': return <ElectionsView />;
      case 'account_auth': return <AccountAuthView />;
      default: return <HomeView />;
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="light-content" backgroundColor="#090d16" />
      <View style={styles.appContainer}>
        {/* Top Header */}
        <Header />

        {/* Dynamic Toasts */}
        <ToastContainer />

        {/* Active Tab Screen */}
        <View style={styles.mainView}>
          {renderActiveView()}
        </View>

        {/* Modals */}
        <CitizenDossierModal />
        <CreateExperimentModal />
        <ReasoningModal />
        <AuthModal visible={!isAuthenticated && !isRestoringSession} />

        {/* Bottom Navigation */}
        <BottomNav />
      </View>
    </SafeAreaView>
  );
};

export default function App() {
  return (
    <AppProvider>
      <MainAppContent />
    </AppProvider>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#090d16',
    paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight : 0,
  },
  appContainer: {
    flex: 1,
    backgroundColor: '#090d16',
  },
  mainView: {
    flex: 1,
  },
});
