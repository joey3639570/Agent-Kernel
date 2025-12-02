<!-- Control panel for starting, stopping simulation and regenerating registry. -->
<template>
  <div class="panel-container">
    <h3>Simulation Control</h3>
    <div class="status-bar">
      <span>Status:</span>
      <span :class="['status-indicator', status]">
        <span class="status-dot"></span>
        {{ status }}
      </span>
    </div>
    <div class="actions">
      <button @click="start" :disabled="isLoading || status === 'running'" class="btn-primary">Start</button>
      <button @click="stop" :disabled="isLoading || status === 'stopped' || status === 'error'" class="btn-danger">Stop</button>
      <button @click="generateRegistry" :disabled="isLoading" class="btn-secondary">Regenerate Registry</button>
    </div>
    <div v-if="message" :class="['message', messageType]">{{ message }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, defineEmits } from 'vue';
import axios from 'axios';

const emit = defineEmits(['simulation-started']);

const status = ref('stopped');
const isLoading = ref(false);
const message = ref('');
const messageType = ref('info');
let pollInterval;

const fetchStatus = async () => {
  try {
    const response = await axios.get('http://localhost:8001/api/simulation/status');
    const oldStatus = status.value;
    const newStatus = response.data.status;
    status.value = newStatus;

    if (response.data.error) {
      message.value = `Error: ${response.data.error}`;
      messageType.value = 'error';
    }

    if (oldStatus !== 'running' && newStatus === 'running') {
      emit('simulation-started');
    }

  } catch (err) {
    status.value = 'error';
    message.value = 'Failed to connect to backend.';
    messageType.value = 'error';
  }
};

const start = async () => {
  isLoading.value = true;
  message.value = 'Starting simulation... This may take a moment.';
  messageType.value = 'info';
  try {
    await axios.post('http://localhost:8001/api/simulation/start');
    await fetchStatus();
    if (status.value === 'running') {
        message.value = 'Simulation started successfully.';
        messageType.value = 'success';
        emit('simulation-started');
    } else if (status.value !== 'error') {
        message.value = 'Simulation is starting...';
        messageType.value = 'info';
    }
  } catch (err) {
    message.value = `Failed to start: ${err.response?.data?.detail || err.message}`;
    messageType.value = 'error';
    await fetchStatus();
  } finally {
    isLoading.value = false;
  }
};

const stop = async () => {
  isLoading.value = true;
  message.value = 'Stopping simulation...';
  messageType.value = 'info';
  try {
    await axios.post('http://localhost:8001/api/simulation/stop');
    await fetchStatus();
    message.value = 'Simulation stopped.';
    messageType.value = 'success';
  } catch (err) {
    message.value = `Failed to stop: ${err.response?.data?.detail || err.message}`;
    messageType.value = 'error';
    await fetchStatus();
  } finally {
    isLoading.value = false;
  }
};

const generateRegistry = async () => {
  isLoading.value = true;
  message.value = 'Regenerating registry.py...';
  messageType.value = 'info';
  try {
    const response = await axios.post('http://localhost:8001/api/registry/generate');
    message.value = response.data.message;
    messageType.value = 'success';
  } catch (err) {
    message.value = `Failed to regenerate registry: ${err.response?.data?.detail || err.message}`;
    messageType.value = 'error';
  } finally {
    isLoading.value = false;
    setTimeout(() => {
      if (messageType.value !== 'error') {
        message.value = '';
      }
    }, 3000);
  }
};

onMounted(() => {
  fetchStatus();
  pollInterval = setInterval(fetchStatus, 5000);
});

onUnmounted(() => {
  clearInterval(pollInterval);
});
</script>

<style scoped>
.panel-container h3 {
  margin-top: 0;
}

.status-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 20px 0;
  padding: 12px 16px;
  background-color: var(--bg-inset-soft);
  border-radius: var(--border-radius-md);
  border: 1px solid var(--border-soft);
}

.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  text-transform: uppercase;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  letter-spacing: 0.5px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: currentColor;
}

.status-indicator.running .status-dot {
  animation: pulse 1.5s infinite;
}

.status-indicator.running {
  color: var(--accent);
  background-color: var(--success-bg);
}

.status-indicator.stopped {
  color: var(--accent-strong);
  background-color: var(--error-bg);
}

[data-theme="dark"] .status-indicator.stopped {
  color: #f85149;
  background-color: var(--error-bg);
}

.status-indicator.starting,
.status-indicator.stopping {
  color: #d4a017;
  background-color: var(--warning-bg);
}

.status-indicator.error {
  color: var(--text-muted);
  background-color: var(--surface-muted);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.actions {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

button {
  padding: 10px 24px;
  border: 1px solid transparent;
  border-radius: var(--border-radius-md);
  cursor: pointer;
  font-weight: 600;
  font-size: 0.95rem;
  transition: var(--transition-fast);
}

button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background-color: var(--accent);
  color: #FDF8E8;
}

[data-theme="dark"] .btn-primary {
  background-color: var(--accent);
  color: #0a0f1e;
}

.btn-primary:hover:not(:disabled) {
  box-shadow: var(--shadow-glow);
  opacity: 0.9;
}

.btn-danger {
  background-color: var(--danger-bg);
  color: var(--danger-text);
}

.btn-danger:hover:not(:disabled) {
  background-color: var(--danger-bg-hover);
}

.btn-secondary {
  background-color: var(--modal-backdrop);
  color: var(--text-primary);
  border-color: var(--border-soft);
}

.btn-secondary:hover:not(:disabled) {
  background-color: var(--accent);
  color: #FDF8E8;
  border-color: transparent;
}

[data-theme="dark"] .btn-secondary {
  background-color: var(--surface-muted);
  color: var(--text-secondary);
}

[data-theme="dark"] .btn-secondary:hover:not(:disabled) {
  background-color: var(--accent);
  color: #0a0f1e;
}

.message {
  margin-top: 20px;
  padding: 12px 16px;
  border-radius: var(--border-radius-sm);
  font-size: 0.95rem;
  border-left: 4px solid;
}

.success {
  background-color: var(--success-bg);
  color: var(--accent);
  border-color: var(--accent);
}

.error {
  background-color: var(--error-bg);
  color: var(--accent-strong);
  border-color: var(--accent-strong);
}

[data-theme="dark"] .error {
  color: #f85149;
  border-color: #f85149;
}

.info {
  background-color: var(--info-bg);
  color: var(--accent);
  border-color: var(--accent);
}
</style>
