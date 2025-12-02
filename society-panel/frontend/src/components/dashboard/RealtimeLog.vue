<!-- Real-time WebSocket log viewer for simulation events. -->
<template>
  <div class="log-panel panel-container">
    <h3>Real-time Event Log</h3>
    <div class="log-actions">
      <button @click="toggleConnection" :class="['btn-toggle', connectionStatus]">
        {{ isConnected ? 'Disconnect' : 'Connect' }}
      </button>
      <button @click="clearLogs" :disabled="!logs.length" class="btn-clear">Clear Logs</button>
    </div>
    <div class="log-window" ref="logWindowRef">
      <div v-for="(log, index) in logs" :key="index" class="log-entry">
        <span class="log-tick">[T:{{ log.tick }}]</span>
        <span :class="['log-name', log.category]">{{ log.name }}</span>
        <span class="log-payload">{{ log.payload }}</span>
      </div>
      <div v-if="!logs.length" class="log-placeholder">
        <span class="placeholder-icon"><AppIcons name="connection" :size="64" /></span>
        <p>Connect to view real-time events</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted, nextTick } from 'vue';
import AppIcons from '../icons/AppIcons.vue';

const logs = ref([]);
const isConnected = ref(false);
const connectionStatus = ref('disconnected');
const logWindowRef = ref(null);
let socket = null;

const scrollToTop = () => {
  nextTick(() => {
    if (logWindowRef.value) {
      logWindowRef.value.scrollTop = 0;
    }
  });
};

const connect = () => {
  socket = new WebSocket('ws://localhost:8000/ws');
  connectionStatus.value = 'connecting';

  socket.onopen = () => {
    isConnected.value = true;
    connectionStatus.value = 'connected';
    logs.value.unshift({ tick: 'SYS', name: 'SYSTEM', payload: 'Connected to event stream.', category: 'system' });
    scrollToTop();
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      logs.value.unshift({
        tick: data.tick,
        name: data.name,
        payload: JSON.stringify(data.payload),
        category: data.category
      });
      if (logs.value.length > 200) logs.value.pop();
      scrollToTop();
    } catch (e) {
      console.error('Failed to parse WebSocket message:', e);
    }
  };

  socket.onclose = () => {
    isConnected.value = false;
    connectionStatus.value = 'disconnected';
    if (logs.value[0]?.name !== 'SYSTEM' || logs.value[0]?.payload !== 'Disconnected.') {
      logs.value.unshift({ tick: 'SYS', name: 'SYSTEM', payload: 'Disconnected.', category: 'system' });
      scrollToTop();
    }
    socket = null;
  };

  socket.onerror = (error) => {
    console.error('WebSocket Error:', error);
    isConnected.value = false;
    connectionStatus.value = 'error';
    logs.value.unshift({ tick: 'SYS', name: 'SYSTEM', payload: 'Connection error.', category: 'system' });
    scrollToTop();
  };
};

const disconnect = () => {
  if (socket) socket.close();
};

const toggleConnection = () => {
  if (isConnected.value) disconnect();
  else connect();
};

const clearLogs = () => {
  logs.value = [];
};

onUnmounted(() => {
  disconnect();
});
</script>

<style scoped>
.log-panel {
  display: flex;
  flex-direction: column;
}

.log-panel h3 {
  margin-top: 0;
  flex-shrink: 0;
}

.log-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.log-actions button {
  padding: 6px 14px;
  border-radius: var(--border-radius-md);
  font-size: 0.9rem;
  font-weight: 500;
  border: 1px solid var(--border-soft);
  background-color: var(--surface);
  color: var(--text-secondary);
  cursor: pointer;
  transition: var(--transition-fast);
}

.log-actions button:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}

.btn-toggle.connected {
  border-color: var(--accent-strong);
  color: var(--accent-strong);
}

[data-theme="dark"] .btn-toggle.connected {
  border-color: #f85149;
  color: #f85149;
}

.btn-toggle.disconnected {
  border-color: var(--accent);
  color: var(--accent);
}

.btn-toggle.connecting {
  border-color: #d4a017;
  color: #d4a017;
}

.log-window {
  background-color: var(--bg-inset-soft);
  color: var(--text-muted);
  padding: 16px;
  border-radius: var(--border-radius-md);
  border: 1px solid var(--border-soft);
  font-family: var(--font-family-mono);
  font-size: 0.875rem;
  flex-grow: 1;
  overflow-y: auto;
  min-height: 0;
}

.log-entry {
  margin-bottom: 8px;
  line-height: 1.6;
  display: flex;
  gap: 10px;
}

.log-tick {
  color: var(--text-muted);
}

.log-name {
  font-weight: 600;
}

.log-name.agent {
  color: #58a6ff;
}

[data-theme="dark"] .log-name.agent {
  color: #79c0ff;
}

.log-name.environment {
  color: var(--accent);
}

.log-name.simulation {
  color: var(--accent-strong);
}

[data-theme="dark"] .log-name.simulation {
  color: var(--accent);
}

.log-name.system {
  color: #d4a017;
}

.log-payload {
  color: var(--text-secondary);
  word-break: break-all;
}

.log-placeholder {
  color: var(--text-muted);
  text-align: center;
  padding-top: 20%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.placeholder-icon {
  font-size: 3rem;
  opacity: 0.5;
}
</style>
