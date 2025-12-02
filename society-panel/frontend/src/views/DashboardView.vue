<!-- Dashboard view containing simulation controls, god mode console, and real-time logs. -->
<script setup>
import { ref } from 'vue';
import SimulationControl from '../components/dashboard/SimulationControl.vue';
import GodModeConsole from '../components/dashboard/GodModeConsole.vue';
import RealtimeLog from '../components/dashboard/RealtimeLog.vue';

const godModeConsoleRef = ref(null);

const handleSimulationStarted = () => {
  if (godModeConsoleRef.value) {
    godModeConsoleRef.value.loadCommands();
  }
};
</script>

<template>
  <div class="dashboard-view">
    <div class="page-header">
      <h1>Simulation Dashboard</h1>
      <p>Control the simulation lifecycle, send commands, and monitor real-time events.</p>
    </div>

    <div class="dashboard-grid">
      <div class="main-panel">
        <SimulationControl @simulation-started="handleSimulationStarted" />
        <GodModeConsole ref="godModeConsoleRef" />
      </div>
      <div class="side-panel">
        <RealtimeLog />
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-header {
  margin-bottom: 2rem;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 3fr) minmax(0, 2fr);
  gap: 2rem;
  align-items: start;
}

.main-panel {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.side-panel {
  position: relative;
  height: 0;
  min-height: 100%;
}

.side-panel :deep(.log-panel) {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.side-panel :deep(.log-panel h3) {
  flex-shrink: 0;
}

.side-panel :deep(.log-actions) {
  flex-shrink: 0;
}

.side-panel :deep(.log-window) {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

@media (max-width: 1024px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  
  .side-panel {
    position: static;
    height: auto;
    min-height: auto;
  }
  
  .side-panel :deep(.log-panel) {
    position: static;
    height: 500px;
  }
}
</style>
