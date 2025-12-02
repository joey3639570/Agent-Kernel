<!-- Generic editor for plugin-based configurations like actions and environment. -->
<template>
  <div class="config-editor-container">
    <div v-if="isLoading" class="loading">Loading...</div>
    <div v-else-if="error" class="message error">{{ error }}</div>

    <div v-if="configData && availablePlugins">
      <div class="form-group">
        <label>Module Name</label>
        <input type="text" v-model="configData.name" />
      </div>

      <div v-for="(component, componentName) in configData.components" :key="componentName" class="component-section">
        <h4>Component: <code>{{ componentName }}</code></h4>

        <div v-if="component.plugin || component.plugins" class="form-group">
          <label>Plugin</label>
          <select :value="getCurrentPluginName(component)" @change="onPluginChange(component, $event.target.value)">
            <option disabled value="">Select a plugin</option>
            <option v-for="pluginName in availablePlugins[configType + '_plugins'][componentName]" :key="pluginName" :value="pluginName">
              {{ pluginName }}
            </option>
          </select>
        </div>

        <div v-if="getCurrentPluginConfig(component)" class="plugin-params">
          <div v-for="(paramValue, paramKey) in getCurrentPluginConfig(component)" :key="paramKey" class="form-group with-delete">
            <label>{{ paramKey }}</label>
            <input
              type="text"
              :value="formatParamValue(paramValue)"
              @input="updatePluginParam(component, paramKey, $event.target.value)"
            />
            <button @click="removePluginParam(component, paramKey)" class="delete-field-btn" title="Remove parameter">×</button>
          </div>

          <div class="add-field-section">
            <input type="text" v-model="newParam[componentName].key" placeholder="New parameter name">
            <input type="text" v-model="newParam[componentName].value" placeholder="Value">
            <button @click="addPluginParam(component, componentName)">Add Parameter</button>
          </div>
        </div>
      </div>

      <div class="actions">
        <button @click="saveConfig" :disabled="isSaving">
          {{ isSaving ? 'Saving...' : `Save ${configName}` }}
        </button>
        <div v-if="saveMessage" :class="['message', saveMessageType]">
          {{ saveMessage }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, defineProps, reactive } from 'vue';
import axios from 'axios';

const props = defineProps({
  configName: { type: String, required: true },
  configType: { type: String, required: true },
  availablePlugins: { type: Object, required: true }
});

const API_URL = `http://localhost:8001/api/configs/${props.configName}`;

const configData = ref(null);
const isLoading = ref(true);
const isSaving = ref(false);
const error = ref('');
const saveMessage = ref('');
const saveMessageType = ref('success');
const newParam = reactive({});

onMounted(async () => {
  try {
    const response = await axios.get(API_URL);
    configData.value = response.data;
    if (configData.value && configData.value.components) {
      Object.keys(configData.value.components).forEach(compName => {
        newParam[compName] = { key: '', value: '' };
      });
    }
  } catch (err) {
    error.value = `Failed to load config: ${err.response?.data?.detail || err.message}`;
  } finally {
    isLoading.value = false;
  }
});

const getPluginContainer = (component) => {
  return props.configType === 'action' ? component?.plugins : component?.plugin;
};

const setPluginContainer = (component, value) => {
  if (props.configType === 'action') {
    component.plugins = value;
  } else {
    component.plugin = value;
  }
};

const formatParamValue = (value) => (typeof value === 'object' && value !== null) ? JSON.stringify(value) : String(value);

const getCurrentPluginName = (component) => {
  const container = getPluginContainer(component);
  return container ? Object.keys(container)[0] || '' : '';
};

const getCurrentPluginConfig = (component) => {
  const container = getPluginContainer(component);
  const name = getCurrentPluginName(component);
  return name && container ? container[name] : null;
};

const updatePluginParam = (component, paramKey, newValue) => {
  const pluginConfig = getCurrentPluginConfig(component);
  if (pluginConfig) {
    try {
      pluginConfig[paramKey] = JSON.parse(newValue);
    } catch (e) {
      pluginConfig[paramKey] = newValue;
    }
  }
};

const onPluginChange = (component, newPluginName) => {
  const oldConfig = getCurrentPluginConfig(component) || { adapters: {} };
  setPluginContainer(component, { [newPluginName]: oldConfig });
};

const addPluginParam = (component, componentName) => {
  const pluginConfig = getCurrentPluginConfig(component);
  const paramData = newParam[componentName];
  if (!pluginConfig || !paramData.key || pluginConfig.hasOwnProperty(paramData.key)) {
    alert('Please enter a unique parameter name.');
    return;
  }
  updatePluginParam(component, paramData.key, paramData.value);
  paramData.key = '';
  paramData.value = '';
};

const removePluginParam = (component, paramKey) => {
  const pluginConfig = getCurrentPluginConfig(component);
  if (pluginConfig && confirm(`Are you sure you want to remove the parameter "${paramKey}"?`)) {
    delete pluginConfig[paramKey];
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
