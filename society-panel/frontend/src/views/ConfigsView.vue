<!-- Configuration view with sidebar navigation for editing various YAML config files. -->
<script setup>
import { ref, shallowRef, onMounted } from 'vue';
import axios from 'axios';
import SimulationConfigEditor from '../components/config_editors/SimulationConfigEditor.vue';
import DatabaseConfigEditor from '../components/config_editors/DatabaseConfigEditor.vue';
import AgentsConfigEditor from '../components/config_editors/AgentsConfigEditor.vue';
import PluginBasedConfigEditor from '../components/config_editors/PluginBasedConfigEditor.vue';
import ModelsConfigEditor from '../components/config_editors/ModelsConfigEditor.vue';
import SystemConfigEditor from '../components/config_editors/SystemConfigEditor.vue';
import RequirementsEditor from '../components/config_editors/RequirementsEditor.vue';

const availablePlugins = ref(null);
const isLoading = ref(true);
const error = ref('');

const configSections = [
  { id: 'agents', title: 'Agent Templates', component: AgentsConfigEditor, props: { configName: 'agents_config.yaml' } },
  { id: 'actions', title: 'Action Settings', component: PluginBasedConfigEditor, props: { configName: 'actions_config.yaml', configType: 'action' } },
  { id: 'environment', title: 'Environment Settings', component: PluginBasedConfigEditor, props: { configName: 'environment_config.yaml', configType: 'environment' } },
  { id: 'models', title: 'Model Providers', component: ModelsConfigEditor, props: {} },
  { id: 'database', title: 'Database Settings', component: DatabaseConfigEditor, props: {} },
  { id: 'system', title: 'System Settings', component: SystemConfigEditor, props: {} },
  { id: 'simulation', title: 'Simulation Settings', component: SimulationConfigEditor, props: {} },
  { id: 'requirements', title: 'Python Dependencies', component: RequirementsEditor, props: {} },
];

const activeConfig = ref(configSections[0].id);
const activeComponent = shallowRef(configSections[0].component);
const activeProps = ref(configSections[0].props);

const setActiveConfig = (section) => {
  activeConfig.value = section.id;
  activeComponent.value = section.component;
  activeProps.value = section.props;
};

onMounted(async () => {
  try {
    const response = await axios.get('http://localhost:8001/api/registry/plugins');
    availablePlugins.value = response.data;
  } catch (err) {
    error.value = `Failed to load available plugins: ${err.response?.data?.detail || err.message}`;
  } finally {
    isLoading.value = false;
  }
});
</script>

<template>
  <div class="configs-view">
    <div class="page-header">
      <h1>Configuration</h1>
      <p>Edit simulation parameters. Changes are saved to the respective YAML files in the workspace.</p>
    </div>

    <div v-if="isLoading" class="loading">Loading plugin information...</div>
    <div v-else-if="error" class="message error">{{ error }}</div>

    <div v-else class="config-layout">
      <nav class="config-nav">
        <ul>
          <li v-for="section in configSections" :key="section.id">
            <button @click="setActiveConfig(section)" :class="{ active: activeConfig === section.id }">
              {{ section.title }}
            </button>
          </li>
        </ul>
      </nav>
      <main class="config-editor-main">
        <component
          :is="activeComponent"
          :key="activeConfig"
          v-bind="activeProps"
          :available-plugins="availablePlugins"
        />
      </main>
    </div>
  </div>
</template>

<style scoped>
.page-header {
  margin-bottom: 2rem;
}

.config-layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 2rem;
  margin-top: 2rem;
}

.config-nav ul {
  list-style: none;
  padding: 0;
  margin: 0;
  position: sticky;
  top: 120px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background: var(--card-bg);
  border-radius: var(--border-radius-lg);
  border: 1px solid var(--border-soft);
  box-shadow: var(--shadow-md);
}

.config-nav button {
  width: 100%;
  padding: 12px 16px;
  border: none;
  background-color: transparent;
  color: var(--text-secondary);
  text-align: left;
  font-size: 0.9rem;
  font-weight: 500;
  border-radius: var(--border-radius-md);
  cursor: pointer;
  transition: all 200ms ease;
  position: relative;
}

.config-nav button:hover {
  background-color: var(--surface);
  color: var(--text-primary);
  transform: translateX(4px);
}

.config-nav button.active {
  background-color: var(--nav-link-hover-bg);
  color: var(--accent);
  font-weight: 600;
}

[data-theme="dark"] .config-nav button.active {
  background-color: var(--nav-link-hover-bg);
  color: var(--accent);
}

.config-editor-main {
  min-width: 0;
}

.loading, .message.error {
  margin: 2rem 0;
  padding: 1rem 1.25rem;
  border-radius: var(--border-radius-md);
  border-left: 4px solid;
}

.loading {
  background-color: var(--info-bg);
  color: var(--accent);
  border-color: var(--accent);
}

.error {
  background-color: var(--error-bg);
  color: var(--accent-strong);
  border-color: var(--accent-strong);
}

[data-theme="dark"] .loading {
  background-color: var(--info-bg);
  color: var(--accent);
  border-color: var(--accent);
}

[data-theme="dark"] .error {
  background-color: var(--error-bg);
  color: #f85149;
  border-color: #f85149;
}

@media (max-width: 960px) {
  .config-layout {
    grid-template-columns: 1fr;
  }
  .config-nav ul {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 8px;
    position: relative;
    top: 0;
  }
  .config-nav button {
    width: auto;
    padding: 10px 16px;
  }
  .config-nav button:hover {
    transform: translateY(-2px);
  }
}
</style>
