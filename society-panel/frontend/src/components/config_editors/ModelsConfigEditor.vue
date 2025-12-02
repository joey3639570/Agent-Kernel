<!-- Editor for model providers configuration. -->
<template>
  <div class="config-editor-container">
    <div v-if="isLoading" class="loading">Loading...</div>
    <div v-else-if="error" class="message error">{{ error }}</div>

    <div v-if="configData">
      <div v-for="(model, index) in configData" :key="index" class="model-section">
        <div class="model-header">
          <h4>Model Provider {{ index + 1 }}</h4>
          <button @click="removeModel(index)" class="remove-btn">Remove</button>
        </div>
        <div class="form-grid">
          <div class="form-group">
            <label>Name</label>
            <input type="text" v-model="model.name" />
          </div>
          <div class="form-group">
            <label>Model</label>
            <input type="text" v-model="model.model" />
          </div>
          <div class="form-group full-width">
            <label>Base URL</label>
            <input type="text" v-model="model.base_url" />
          </div>
          <div class="form-group full-width">
            <label>API Key</label>
            <input type="password" v-model="model.api_key" placeholder="Leave blank if not needed" />
          </div>
          <div class="form-group">
            <label>Capabilities</label>
            <input type="text" v-model="model.capabilities" placeholder="e.g., chat,embedding" />
            <small>Comma-separated list.</small>
          </div>
        </div>
      </div>

      <div class="add-section">
        <button @click="addModel">Add New Model Provider</button>
      </div>

      <div class="actions">
        <button @click="saveConfig" :disabled="isSaving">
          {{ isSaving ? 'Saving...' : 'Save Models Config' }}
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

const CONFIG_NAME = 'models_config.yaml';
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
    configData.value = response.data || [];
  } catch (err) {
    error.value = `Failed to load config: ${err.response?.data?.detail || err.message}`;
  } finally {
    isLoading.value = false;
  }
});

const addModel = () => {
  configData.value.push({
    name: "OpenAIProvider",
    model: "Qwen/Qwen-chat",
    api_key: "",
    base_url: "http://localhost:8000/v1",
    capabilities: ["chat"]
  });
};

const removeModel = (index) => {
  configData.value.splice(index, 1);
};

const saveConfig = async () => {
  if (!configData.value) return;
  isSaving.value = true;
  saveMessage.value = '';
  try {
    const dataToSave = configData.value.map(model => {
      if (typeof model.capabilities === 'string') {
        return { ...model, capabilities: model.capabilities.split(',').map(s => s.trim()) };
      }
      return model;
    });
    const response = await axios.post(API_URL, dataToSave);
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
</style>
