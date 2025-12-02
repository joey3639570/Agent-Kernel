<!-- Editor for requirements.txt file to manage Python dependencies. -->
<template>
  <div class="config-editor-container">
    <div v-if="isLoading" class="loading">Loading...</div>
    <div v-else-if="error" class="message error">{{ error }}</div>

    <div v-if="content !== null">
      <div class="form-group">
        <label for="requirements-content">File Content (one package per line)</label>
        <textarea id="requirements-content" v-model="content" rows="15"></textarea>
      </div>

      <div class="actions">
        <button @click="save" :disabled="isSaving">
          {{ isSaving ? 'Saving...' : 'Save requirements.txt' }}
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

const API_URL = 'http://localhost:8001/api/requirements';

const content = ref(null);
const isLoading = ref(true);
const isSaving = ref(false);
const error = ref('');
const saveMessage = ref('');
const saveMessageType = ref('success');

onMounted(async () => {
  try {
    const response = await axios.get(API_URL);
    content.value = response.data.content;
  } catch (err) {
    error.value = `Failed to load requirements.txt: ${err.response?.data?.detail || err.message}`;
  } finally {
    isLoading.value = false;
  }
});

const save = async () => {
  if (content.value === null) return;
  isSaving.value = true;
  saveMessage.value = '';
  try {
    const response = await axios.post(API_URL, { content: content.value });
    saveMessage.value = response.data.message;
    saveMessageType.value = 'success';
  } catch (err) {
    saveMessage.value = `Failed to save: ${err.response?.data?.detail || err.message}`;
    saveMessageType.value = 'error';
  } finally {
    isSaving.value = false;
    setTimeout(() => { saveMessage.value = ''; }, 4000);
  }
};
</script>

<style scoped>
</style>
