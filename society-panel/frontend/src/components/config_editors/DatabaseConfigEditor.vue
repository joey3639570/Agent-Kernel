<!-- Editor for database connection pools and adapters configuration. -->
<template>
  <div class="config-editor-container">
    <div v-if="isLoading" class="loading">Loading...</div>
    <div v-else-if="error" class="message error">{{ error }}</div>

    <div v-if="configData">
      <h3>Connection Pools</h3>
      <div v-for="(pool, poolName) in configData.pools" :key="poolName" class="config-section">
        <div class="section-header">
          <h4>Pool: <code>{{ poolName }}</code></h4>
          <button @click="removeTopLevelKey('pools', poolName)" class="remove-btn">Remove</button>
        </div>
        <div class="form-grid">
          <div class="form-group">
            <label>type</label>
            <select v-model="pool.type">
              <option>redis</option>
              <option>postgres</option>
            </select>
          </div>
        </div>
        <div class="sub-section">
          <h5>Settings</h5>
          <div class="form-grid settings-grid">
            <div v-for="(value, key) in pool.settings" :key="key" class="form-group with-delete">
              <label>{{ key }}</label>
              <input type="text" :value="formatParamValue(value)" @input="updateNestedParam(pool.settings, key, $event.target.value)" />
              <button @click="removeNestedKey(pool.settings, key)" class="delete-field-btn">×</button>
            </div>
          </div>
          <div class="add-field-section">
            <input type="text" v-model="newField.pools[poolName].settings.key" placeholder="New field name">
            <input type="text" v-model="newField.pools[poolName].settings.value" placeholder="Value">
            <button @click="addNestedKey(pool.settings, newField.pools[poolName].settings)">Add Field</button>
          </div>
        </div>
        <div class="sub-section">
          <h5>Pool Settings</h5>
          <div class="form-grid settings-grid">
            <div v-for="(value, key) in pool.pool_settings" :key="key" class="form-group with-delete">
              <label>{{ key }}</label>
              <input type="text" :value="formatParamValue(value)" @input="updateNestedParam(pool.pool_settings, key, $event.target.value)" />
              <button @click="removeNestedKey(pool.pool_settings, key)" class="delete-field-btn">×</button>
            </div>
          </div>
           <div class="add-field-section">
            <input type="text" v-model="newField.pools[poolName].pool_settings.key" placeholder="New field name">
            <input type="text" v-model="newField.pools[poolName].pool_settings.value" placeholder="Value">
            <button @click="addNestedKey(pool.pool_settings, newField.pools[poolName].pool_settings)">Add Field</button>
          </div>
        </div>
      </div>
      <div class="add-section">
        <input type="text" v-model="newPoolName" placeholder="New pool name">
        <button @click="addPool" :disabled="!newPoolName">Add New Pool</button>
      </div>

      <h3 style="margin-top: 2.5rem;">Adapters</h3>
      <div v-for="(adapter, adapterName) in configData.adapters" :key="adapterName" class="config-section">
        <div class="section-header">
          <h4>Adapter: <code>{{ adapterName }}</code></h4>
          <button @click="removeTopLevelKey('adapters', adapterName)" class="remove-btn">Remove</button>
        </div>

        <div v-if="'use_pool' in adapter" class="form-group">
          <label>use_pool</label>
          <select v-model="adapter.use_pool">
            <option value="">-- None --</option>
            <option v-for="poolName in Object.keys(configData.pools)" :key="poolName" :value="poolName">{{ poolName }}</option>
          </select>
        </div>

        <div v-if="'settings' in adapter" class="sub-section">
          <h5>Settings</h5>
          <div class="form-grid settings-grid">
            <div v-for="(value, key) in adapter.settings" :key="key" class="form-group with-delete">
              <label>{{ key }}</label>
              <input type="text" :value="formatParamValue(value)" @input="updateNestedParam(adapter.settings, key, $event.target.value)" />
              <button @click="removeNestedKey(adapter.settings, key)" class="delete-field-btn">×</button>
            </div>
          </div>
          <div class="add-field-section">
            <input type="text" v-model="newField.adapters[adapterName].settings.key" placeholder="New field name">
            <input type="text" v-model="newField.adapters[adapterName].settings.value" placeholder="Value">
            <button @click="addNestedKey(adapter.settings, newField.adapters[adapterName].settings)">Add Field</button>
          </div>
        </div>
      </div>
      <div class="add-section">
        <input type="text" v-model="newAdapterName" placeholder="New adapter name">
        <select v-model="newAdapterType">
          <option value="pooled">Pooled</option>
          <option value="standalone">Standalone</option>
        </select>
        <button @click="addAdapter" :disabled="!newAdapterName">Add New Adapter</button>
      </div>

      <div class="actions">
        <button @click="saveConfig" :disabled="isSaving">
          {{ isSaving ? 'Saving...' : 'Save Database Config' }}
        </button>
        <div v-if="saveMessage" :class="['message', saveMessageType]">
          {{ saveMessage }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue';
import axios from 'axios';

const CONFIG_NAME = 'db_config.yaml';
const API_URL = `http://localhost:8001/api/configs/${CONFIG_NAME}`;

const configData = ref(null);
const isLoading = ref(true);
const isSaving = ref(false);
const error = ref('');
const saveMessage = ref('');
const saveMessageType = ref('success');

const newPoolName = ref('');
const newAdapterName = ref('');
const newAdapterType = ref('pooled');

const newField = reactive({ pools: {}, adapters: {} });

const initializeNewFieldData = (data) => {
  if (!data) return;
  for (const poolName in data.pools) {
    newField.pools[poolName] = {
      settings: { key: '', value: '' },
      pool_settings: { key: '', value: '' }
    };
  }
  for (const adapterName in data.adapters) {
    newField.adapters[adapterName] = {
      settings: { key: '', value: '' }
    };
  }
};

onMounted(async () => {
  try {
    const response = await axios.get(API_URL);
    const data = response.data || {};
    data.pools = data.pools || {};
    data.adapters = data.adapters || {};

    for (const pool of Object.values(data.pools)) {
      if (!pool.settings) pool.settings = {};
      if (!pool.pool_settings) pool.pool_settings = {};
    }
    for (const adapter of Object.values(data.adapters)) {
      if (!adapter.settings) adapter.settings = {};
    }

    configData.value = data;
    initializeNewFieldData(data);
  } catch (err) {
    error.value = `Failed to load config: ${err.response?.data?.detail || err.message}`;
  } finally {
    isLoading.value = false;
  }
});

const formatParamValue = (value) => (typeof value === 'object' && value !== null) ? JSON.stringify(value) : String(value);

const updateNestedParam = (obj, key, newValue) => {
  try {
    obj[key] = JSON.parse(newValue);
  } catch (e) {
    obj[key] = newValue;
  }
};

const removeTopLevelKey = (section, key) => {
  if (confirm(`Are you sure you want to remove "${key}"?`)) {
    delete configData.value[section][key];
    delete newField[section][key];
  }
};

const addPool = () => {
  if (!newPoolName.value || configData.value.pools[newPoolName.value]) {
    alert('Please enter a unique name for the new pool.');
    return;
  }
  const name = newPoolName.value;
  configData.value.pools[name] = {
    type: 'redis',
    settings: { host: 'localhost', port: 6379 },
    pool_settings: { max_connections: 50 },
  };
  newField.pools[name] = { settings: { key: '', value: '' }, pool_settings: { key: '', value: '' } };
  newPoolName.value = '';
};

const addAdapter = () => {
  if (!newAdapterName.value || configData.value.adapters[newAdapterName.value]) {
    alert('Please enter a unique name for the new adapter.');
    return;
  }
  const name = newAdapterName.value;
  if (newAdapterType.value === 'pooled') {
    configData.value.adapters[name] = { use_pool: '' };
  } else {
    configData.value.adapters[name] = { settings: { uri: 'http://localhost:19530' } };
  }
  newField.adapters[name] = { settings: { key: '', value: '' } };
  newAdapterName.value = '';
};

const addNestedKey = (targetObject, newFieldData) => {
  if (!newFieldData.key || targetObject.hasOwnProperty(newFieldData.key)) {
    alert('Please enter a unique field name.');
    return;
  }
  updateNestedParam(targetObject, newFieldData.key, newFieldData.value);
  newFieldData.key = '';
  newFieldData.value = '';
};

const removeNestedKey = (targetObject, key) => {
  delete targetObject[key];
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
h3 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  color: var(--accent);
  font-size: 1.15rem;
  font-weight: 700;
}
</style>
