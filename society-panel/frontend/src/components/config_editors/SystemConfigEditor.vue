<!-- Editor for system components configuration (messager, timer, recorder). -->
<template>
  <div class="config-editor-container">
    <div v-if="isLoading" class="loading">Loading...</div>
    <div v-else-if="error" class="message error">{{ error }}</div>

    <div v-if="configData">
      <div class="form-group">
        <label>Module Name</label>
        <input type="text" v-model="configData.name" />
      </div>

      <div class="component-section">
        <h4>Component: <code>messager</code></h4>
        <div class="form-grid">
          <div v-for="(value, key) in configData.components.messager" :key="key" class="form-group">
            <label>{{ key }}</label>
            <input type="text" :value="formatParamValue(value)" @input="updateParam('messager', key, $event.target.value)" />
          </div>
        </div>
      </div>

      <div class="component-section">
        <h4>Component: <code>timer</code></h4>
        <div class="form-grid">
          <div v-for="(value, key) in configData.components.timer" :key="key" class="form-group">
            <label>{{ key }}</label>
            <input type="number" v-model.number="configData.components.timer[key]" />
          </div>
        </div>
      </div>

      <div class="component-section">
        <h4>Component: <code>recorder</code></h4>
        <div class="form-grid">
          <div v-for="(value, key) in configData.components.recorder" :key="key" class="form-group">
            <label>{{ key }}</label>
            <input type="text" v-model="configData.components.recorder[key]" />
          </div>
        </div>
      </div>

      <div class="actions">
        <button @click="saveConfig" :disabled="isSaving">
          {{ isSaving ? 'Saving...' : 'Save System Config' }}
        </button>
        <div v-if="saveMessage" :class="['message', saveMessageType]">
          {{ saveMessage }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const CONFIG_NAME = 'system_config.yaml';
const API_URL = `http://localhost:8001/api/configs/${CONFIG_NAME}`;

const configData = ref(null);
const isLoading = ref(true);
const isSaving = ref(false);
const error = ref('');
const saveMessage = ref('');
const saveMessageType = ref('success');

onMounted(async () => {
  try {
    const response = await axios.get(API_URL);
    configData.value = response.data;
  } catch (err) {
    error.value = `Failed to load config: ${err.response?.data?.detail || err.message}`;
  } finally {
    isLoading.value = false;
  }
});

const formatParamValue = (value) => {
  if (typeof value === 'object' && value !== null) {
    return JSON.stringify(value);
  }
  return value;
};

const updateParam = (componentName, paramKey, newValue) => {
  try {
    configData.value.components[componentName][paramKey] = JSON.parse(newValue);
  } catch (e) {
    configData.value.components[componentName][paramKey] = newValue;
  }
};

const saveConfig = async () => {
  if (!configData.value) return;
  isSaving.value = true;
  saveMessage.value = '';
  try {
    const response = await axios.post(API_URL, configData.value);
    saveMessage.value = response.data.message;
    saveMessageType.value = 'success';
  } catch (err) {
    saveMessage.value = `Failed to save config: ${err.response?.data?.detail || err.message}`;
    saveMessageType.value = 'error';
  } finally {
    isSaving.value = false;
    setTimeout(() => { saveMessage.value = ''; }, 3000);
  }
};
</script>

<style scoped>
.component-section {
  margin-bottom: 1.5rem;
  padding: 24px;
  border: 1px solid var(--border-soft);
  border-radius: 16px;
  background-color: var(--bg-inset-soft);
  transition: all 250ms ease;
}

.component-section:hover {
  border-color: color-mix(in srgb, var(--accent) 50%, var(--border-soft) 50%);
  box-shadow: 0 8px 30px var(--accent-shadow);
}

.component-section h4 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--accent);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.component-section h4 code {
  font-size: 0.85rem;
  padding: 4px 10px;
  background-color: var(--nav-link-hover-bg);
  border-radius: 6px;
  font-weight: 600;
  color: var(--accent);
  border: none;
}
</style>
