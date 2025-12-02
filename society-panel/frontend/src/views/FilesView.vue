<!-- File management view for uploading, listing, and deleting package and data files. -->
<script setup>
import { ref, onMounted, reactive } from 'vue';
import axios from 'axios';
import AppIcons from '../components/icons/AppIcons.vue';
import ConfirmDialog from '../components/ConfirmDialog.vue';

const confirmDialog = ref(null);

const zones = reactive({
  package: {
    title: 'MAS-Package',
    description: 'Contains all logic: plugins, configs, and custom Python code.',
    file: null,
    isDragOver: false,
    isLoading: false,
    message: '',
    messageType: 'success',
    uploadUrl: 'http://localhost:8001/api/files/upload/package',
    pluginsUrl: 'http://localhost:8001/api/registry/plugins',
    contentsUrl: 'http://localhost:8001/api/files/list/package',
    plugins: null,
    contents: [],
    fileInputRef: ref(null)
  },
  data: {
    title: 'Data',
    description: 'Datasets for agent profiles, environment objects, and relationships.',
    file: null,
    isDragOver: false,
    isLoading: false,
    message: '',
    messageType: 'success',
    uploadUrl: 'http://localhost:8001/api/files/upload/data',
    listUrl: 'http://localhost:8001/api/files/list/data',
    items: [],
    fileInputRef: ref(null)
  }
});

const fetchPackageContents = async () => {
  const zone = zones.package;
  try {
    const [pluginsRes, contentsRes] = await Promise.all([
      axios.get(zone.pluginsUrl),
      axios.get(zone.contentsUrl)
    ]);
    zone.plugins = pluginsRes.data;
    zone.contents = contentsRes.data;
  } catch (error) {
    zone.message = 'Failed to load existing package contents.';
    zone.messageType = 'error';
    console.error('Error fetching package contents:', error);
  }
};

const fetchDataContents = async () => {
  const zone = zones.data;
  try {
    const response = await axios.get(zone.listUrl);
    zone.items = response.data;
  } catch (error) {
    zone.message = 'Failed to load existing data files.';
    zone.messageType = 'error';
    console.error('Error fetching data files:', error);
  }
};

onMounted(() => {
  fetchPackageContents();
  fetchDataContents();
});

const processFile = (zone, droppedFile) => {
  if (droppedFile && droppedFile.name.endsWith('.zip')) {
    zone.file = droppedFile;
    zone.message = '';
  } else {
    zone.message = 'Please drop a .zip file.';
    zone.messageType = 'error';
  }
  zone.isDragOver = false;
};

const handleUpload = async (zoneKey) => {
  const zone = zones[zoneKey];
  if (!zone.file) return;

  zone.isLoading = true;
  zone.message = '';

  const formData = new FormData();
  formData.append('file', zone.file);

  try {
    const response = await axios.post(zone.uploadUrl, formData);
    zone.message = response.data.message;
    zone.messageType = 'success';
    zone.file = null;
    if (zoneKey === 'package') {
      await fetchPackageContents();
    } else {
      await fetchDataContents();
    }
  } catch (error) {
    zone.message = error.response?.data?.detail || `An error occurred during ${zone.title} upload.`;
    zone.messageType = 'error';
  } finally {
    zone.isLoading = false;
    if (zone.fileInputRef) {
      zone.fileInputRef.value = '';
    }
    setTimeout(() => {
      if (zone.messageType === 'success') {
        zone.message = '';
      }
    }, 5000);
  }
};

const clearFile = (zone) => {
  zone.file = null;
  if (zone.fileInputRef) {
    zone.fileInputRef.value = '';
  }
};

const getIconType = (filename) => {
  const lower = filename.toLowerCase();
  
  if (lower.endsWith('.py')) return 'python';
  if (lower.endsWith('.json') || lower.endsWith('.jsonl')) return 'json';
  if (lower.endsWith('.yaml') || lower.endsWith('.yml')) return 'yaml';
  if (lower.endsWith('.csv')) return 'csv';
  if (lower.endsWith('.xml')) return 'xml';
  if (lower.endsWith('.txt')) return 'txt';
  if (lower.endsWith('.md') || lower.endsWith('.markdown')) return 'md';
  if (!filename.includes('.') || filename.endsWith('/')) return 'folder';
  
  return 'data';
};

const hasPlugins = (zone) => {
  if (!zone.plugins) return false;
  const { agent_plugins, action_plugins, environment_plugins } = zone.plugins;
  
  const hasAgent = agent_plugins && Object.values(agent_plugins).some(arr => arr && arr.length > 0);
  const hasAction = action_plugins && Object.values(action_plugins).some(arr => arr && arr.length > 0);
  const hasEnv = environment_plugins && Object.values(environment_plugins).some(arr => arr && arr.length > 0);
  
  return hasAgent || hasAction || hasEnv;
};

const handleDeleteItem = async (type, itemName) => {
  const confirmed = await confirmDialog.value.show({
    title: 'Delete File',
    message: `Are you sure you want to delete "${itemName}"? This action cannot be undone.`,
    confirmText: 'Delete',
    cancelText: 'Cancel',
    isDanger: true
  });
  
  if (!confirmed) return;
  
  try {
    await axios.delete(`http://localhost:8001/api/files/delete/${type}/${encodeURIComponent(itemName)}`);
    
    if (type === 'package') {
      await fetchPackageContents();
    } else {
      await fetchDataContents();
    }
  } catch (error) {
    alert(error.response?.data?.detail || `Failed to delete "${itemName}".`);
  }
};

const handleClearAll = async (type) => {
  const zone = zones[type];
  const confirmed = await confirmDialog.value.show({
    title: 'Clear All Files',
    message: `Are you sure you want to clear all ${zone.title} files? This action cannot be undone.`,
    confirmText: 'Clear All',
    cancelText: 'Cancel',
    isDanger: true
  });
  
  if (!confirmed) return;
  
  try {
    await axios.delete(`http://localhost:8001/api/files/clear/${type}`);
    
    if (type === 'package') {
      await fetchPackageContents();
    } else {
      await fetchDataContents();
    }
  } catch (error) {
    alert(error.response?.data?.detail || `Failed to clear ${zone.title} files.`);
  }
};

const handleDeletePlugin = async (pluginType, category, pluginName) => {
  const confirmed = await confirmDialog.value.show({
    title: 'Delete Plugin',
    message: `Are you sure you want to delete plugin "${pluginName}"? This will remove the entire ${category} plugin folder.`,
    confirmText: 'Delete',
    cancelText: 'Cancel',
    isDanger: true
  });
  
  if (!confirmed) return;
  
  const folderPath = `plugins/${pluginType}/${category}`;
  
  try {
    await axios.delete(`http://localhost:8001/api/files/delete/package/${encodeURIComponent(folderPath)}`);
    await fetchPackageContents();
  } catch (error) {
    alert(error.response?.data?.detail || `Failed to delete plugin "${pluginName}".`);
  }
};
</script>

<template>
  <div class="files-view">
    <ConfirmDialog ref="confirmDialog" />
    <div class="page-header">
      <h1>File Management</h1>
      <p>Package your custom code and configs into <strong>.zip files</strong> to upload, and provide the data required for simulation.</p>
    </div>

    <div class="management-grid">
      <div v-for="(zone, key) in zones" :key="key" class="management-zone">
        <div class="upload-container panel-container">
          <h2>{{ zone.title }}</h2>
          <p class="zone-description">{{ zone.description }}</p>
          <div
            :class="['drop-zone', { 'is-dragover': zone.isDragOver }]"
            @dragover.prevent="zone.isDragOver = true"
            @dragleave.prevent="zone.isDragOver = false"
            @drop.prevent="processFile(zone, $event.dataTransfer.files[0])"
            @click="zone.fileInputRef.click()"
          >
            <input
              type="file"
              :ref="el => { if (el) zone.fileInputRef = el }"
              @change="processFile(zone, $event.target.files[0])"
              style="display: none;"
              accept=".zip"
            />
            <div v-if="!zone.file" class="placeholder-content">
              <div class="icon"><AppIcons :name="key === 'package' ? 'package' : 'data'" :size="48" /></div>
              <h3>Drop {{ zone.title }}.zip here</h3>
              <p>or click to select</p>
            </div>
            <div v-else class="file-preview-content">
              <div class="icon success-icon">✓</div>
              <h3>File Ready</h3>
              <p class="file-name">{{ zone.file.name }}</p>
              <div class="button-group">
                <button @click.stop="handleUpload(key)" :disabled="zone.isLoading" class="upload-btn">
                  {{ zone.isLoading ? 'Uploading...' : 'Upload' }}
                </button>
                <button @click.stop="clearFile(zone)" class="clear-btn">Clear</button>
              </div>
            </div>
          </div>
          <div v-if="zone.message" :class="['message', zone.messageType]">{{ zone.message }}</div>
        </div>

        <div class="existing-content-container panel-container">
          <div class="existing-header">
            <h3>Existing {{ zone.title }}</h3>
            <button 
              @click="handleClearAll(key)" 
              class="clear-all-btn"
              :disabled="key === 'package' ? zone.contents.length === 0 : (!zone.items || zone.items.length === 0)"
            >
              Clear All
            </button>
          </div>

          <div v-if="key === 'package'" class="package-content-display">
            <h4>Detected Plugins</h4>
            <div v-if="hasPlugins(zone)" class="plugin-grid">
              <div v-for="(plugins, category) in zone.plugins.agent_plugins" :key="'agent-' + category">
                <div v-for="pluginName in plugins" :key="pluginName" class="plugin-card">
                  <span class="plugin-icon"><AppIcons name="plugin" :size="24" /></span>
                  <div class="plugin-info">
                    <span class="plugin-name">{{ pluginName }}</span>
                    <span class="plugin-category">Agent / {{ category }}</span>
                  </div>
                  <button @click="handleDeletePlugin('agent', category, pluginName)" class="delete-item-btn plugin-delete" title="Delete">×</button>
                </div>
              </div>
              <div v-for="(plugins, category) in zone.plugins.action_plugins" :key="'action-' + category">
                <div v-for="pluginName in plugins" :key="pluginName" class="plugin-card">
                  <span class="plugin-icon"><AppIcons name="plugin" :size="24" /></span>
                  <div class="plugin-info">
                    <span class="plugin-name">{{ pluginName }}</span>
                    <span class="plugin-category">Action / {{ category }}</span>
                  </div>
                  <button @click="handleDeletePlugin('action', category, pluginName)" class="delete-item-btn plugin-delete" title="Delete">×</button>
                </div>
              </div>
              <div v-for="(plugins, category) in zone.plugins.environment_plugins" :key="'env-' + category">
                <div v-for="pluginName in plugins" :key="pluginName" class="plugin-card">
                  <span class="plugin-icon"><AppIcons name="plugin" :size="24" /></span>
                  <div class="plugin-info">
                    <span class="plugin-name">{{ pluginName }}</span>
                    <span class="plugin-category">Environment / {{ category }}</span>
                  </div>
                  <button @click="handleDeletePlugin('environment', category, pluginName)" class="delete-item-btn plugin-delete" title="Delete">×</button>
                </div>
              </div>
            </div>
            <div v-else class="empty-list">No plugins detected.</div>

            <h4 class="sub-header">Package Contents</h4>
            <div class="file-list">
              <ul v-if="zone.contents.length > 0">
                <li v-for="item in zone.contents" :key="item">
                  <span class="file-icon"><AppIcons :name="getIconType(item)" :size="20" /></span>
                  <span class="file-name-text">{{ item }}</span>
                  <button @click="handleDeleteItem('package', item)" class="delete-item-btn" title="Delete">×</button>
                </li>
              </ul>
              <div v-else class="empty-list">No other files found.</div>
            </div>
          </div>

          <div v-else class="file-list">
            <div v-if="!zone.items || zone.items.length === 0" class="empty-list">
              No data files found.
            </div>
            <ul v-else>
              <li v-for="item in zone.items" :key="item">
                <span class="file-icon"><AppIcons :name="getIconType(item)" :size="20" /></span>
                <span class="file-name-text">{{ item }}</span>
                <button @click="handleDeleteItem('data', item)" class="delete-item-btn" title="Delete">×</button>
              </li>
            </ul>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped>
.page-header {
  margin-bottom: 2rem;
}

.page-header p {
  white-space: nowrap;
}

.management-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2.5rem;
}

@media (max-width: 1200px) {
  .management-grid {
    grid-template-columns: 1fr;
  }
}

.management-zone {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.upload-container {
  display: flex;
  flex-direction: column;
}

.existing-content-container {
  flex-grow: 1;
}

h2 {
  margin-top: 0;
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--accent);
  border: none;
  text-shadow: none;
}

h3 {
  margin-top: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-secondary);
  border: none;
  text-shadow: none;
}

.zone-description {
  margin-top: -0.5rem;
  margin-bottom: 1.5rem;
  color: var(--text-muted);
  font-size: 0.9rem;
}

.drop-zone {
  border: 2px dashed var(--border-soft);
  border-radius: var(--border-radius-lg);
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: var(--transition-fast);
  background-color: var(--bg-inset-softest);
  flex-grow: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.drop-zone:hover {
  border-color: var(--accent);
  transform: scale(1.02);
  background-color: var(--nav-link-hover-bg);
}

.drop-zone.is-dragover {
  background-color: var(--nav-link-hover-bg);
  border-color: var(--accent);
  border-style: solid;
  transform: scale(1.03);
}

.placeholder-content .icon,
.file-preview-content .icon {
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s ease;
}

.drop-zone:hover .placeholder-content .icon {
  transform: scale(1.1) rotate(-5deg);
}

.file-preview-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.file-preview-content .icon {
  color: var(--accent);
}

.file-preview-content .success-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent) 0%, #5a8a3a 100%);
  color: #fff;
  font-size: 1.75rem;
  font-weight: bold;
  box-shadow: 0 4px 15px var(--accent-shadow);
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-content h3,
.file-preview-content h3 {
  margin: 16px 0 8px 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.placeholder-content p {
  color: var(--text-muted);
  margin: 0;
}

.file-name {
  margin-top: 12px;
  font-family: var(--font-family-mono);
  background-color: var(--chip-bg);
  padding: 10px 20px;
  border-radius: 10px;
  display: inline-block;
  border: 1px solid var(--border-soft);
  font-size: 0.95rem;
  color: var(--accent);
  font-weight: 500;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.button-group {
  margin-top: 1.5rem;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
}

.upload-btn,
.clear-btn {
  padding: 12px 28px;
  border: 1px solid transparent;
  border-radius: 25px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.95rem;
  transition: all 200ms ease;
  min-width: 100px;
}

.upload-btn {
  background: linear-gradient(135deg, var(--accent) 0%, #5a8a3a 100%);
  color: #FDF8E8;
  box-shadow: 0 2px 8px var(--accent-shadow);
}

[data-theme="dark"] .upload-btn {
  background: linear-gradient(135deg, var(--accent) 0%, #8bc34a 100%);
  color: #0a0f1e;
}

.upload-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px var(--accent-shadow);
}

.upload-btn:disabled {
  background: var(--surface-muted);
  color: var(--text-muted);
  cursor: not-allowed;
  box-shadow: none;
}

.clear-btn {
  background-color: var(--surface);
  color: var(--text-secondary);
  border: 1px solid var(--border-soft);
}

.clear-btn:hover {
  background-color: var(--bg-inset-soft);
  border-color: var(--accent);
  color: var(--accent);
}

.message {
  margin-top: 1rem;
  padding: 10px 16px;
  border-radius: var(--border-radius-md);
  text-align: center;
  font-size: 0.9rem;
  border-left: 4px solid;
}

.message.success {
  background-color: var(--success-bg);
  color: var(--accent);
  border-color: var(--accent);
}

.message.error {
  background-color: var(--error-bg);
  color: var(--accent-strong);
  border-color: var(--accent-strong);
}

[data-theme="dark"] .message.success {
  background-color: var(--success-bg);
  color: var(--accent);
  border-color: var(--accent);
}

[data-theme="dark"] .message.error {
  background-color: var(--error-bg);
  color: #f85149;
  border-color: #f85149;
}

.package-content-display h4 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 1rem;
  margin-top: 0;
}

.package-content-display .sub-header {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border-soft);
}

.plugin-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  overflow-y: auto;
  max-height: 250px;
  padding: 4px;
}

.plugin-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background-color: var(--bg-inset-soft);
  padding: 12px 16px;
  border-radius: var(--border-radius-md);
  border: 1px solid var(--border-soft);
  transition: var(--transition-fast);
  position: relative;
}

.plugin-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--accent);
}

.plugin-card .plugin-delete {
  opacity: 0;
  margin-left: auto;
}

.plugin-card:hover .plugin-delete {
  opacity: 1;
}

.plugin-icon {
  font-size: 1.5rem;
  color: var(--accent);
  flex-shrink: 0;
}

.plugin-info {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.plugin-name {
  font-weight: 600;
  color: var(--text-primary);
}

.plugin-category {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.file-list {
  overflow-y: auto;
  max-height: 250px;
  padding: 4px;
}

.existing-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.existing-header h3 {
  margin: 0;
}

.clear-all-btn {
  padding: 6px 14px;
  border: 1px solid var(--accent-strong);
  border-radius: 8px;
  background: transparent;
  color: var(--accent-strong);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 200ms ease;
}

.clear-all-btn:hover:not(:disabled) {
  background: var(--error-bg);
  border-color: var(--accent-strong);
}

.clear-all-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

[data-theme="dark"] .clear-all-btn {
  color: #f85149;
  border-color: #f85149;
}

[data-theme="dark"] .clear-all-btn:hover:not(:disabled) {
  background: rgba(248, 81, 73, 0.15);
}

.file-list ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.file-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--border-radius-sm);
  font-family: var(--font-family-mono);
  font-size: 0.9rem;
  color: var(--text-secondary);
  transition: background-color 0.2s;
}

.file-list li:hover {
  background-color: var(--surface);
  color: var(--text-primary);
}

.file-name-text {
  flex: 1;
}

.delete-item-btn {
  width: 26px;
  height: 26px;
  min-width: 26px;
  min-height: 26px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-muted);
  font-size: 1.3rem;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 150ms ease;
  flex-shrink: 0;
}

.file-list li:hover .delete-item-btn {
  opacity: 1;
}

.delete-item-btn:hover {
  background: var(--error-bg);
  color: var(--accent-strong);
}

[data-theme="dark"] .delete-item-btn:hover {
  color: #f85149;
}

.file-icon {
  font-size: 1rem;
  flex-shrink: 0;
}

.empty-list {
  color: var(--text-muted);
  text-align: center;
  padding: 2rem 0;
  font-style: italic;
}

.existing-content-container > .file-list {
  display: flex;
  flex-direction: column;
  min-height: 200px;
}

.existing-content-container > .file-list > .empty-list {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0;
  padding: 0;
}
</style>
