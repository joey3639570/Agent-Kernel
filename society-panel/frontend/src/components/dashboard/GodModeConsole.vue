<!-- Console for executing PodManager commands with parameter input and response display. -->
<template>
  <div class="panel-container">
    <h3>God Mode Console</h3>
    <div v-if="isCommandsLoading" class="loading-small">Loading commands...</div>
    <div v-else-if="commandsError" class="message error">{{ commandsError }}</div>

    <div v-else>
      <div class="form-group">
        <label for="command">Command (PodManager Method)</label>
        <div class="custom-select" :class="{ 'is-open': isDropdownOpen }">
          <div class="custom-select__trigger" @click="toggleDropdown">
            <span class="custom-select__value">{{ command || '-- Select a command --' }}</span>
            <svg class="custom-select__arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M6 9l6 6 6-6" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="custom-select__options" v-show="isDropdownOpen">
            <div class="custom-select__search">
              <input 
                type="text" 
                v-model="searchQuery" 
                placeholder="Search commands..."
                @click.stop
                ref="searchInput"
              />
            </div>
            <div class="custom-select__options-list">
              <div 
                v-for="cmd in filteredCommands" 
                :key="cmd.name"
                class="custom-select__option"
                :class="{ 'is-selected': command === cmd.name }"
                @click="selectCommand(cmd.name)"
              >
                {{ cmd.name }}
              </div>
              <div v-if="filteredCommands.length === 0" class="custom-select__empty">
                No commands found
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="selectedCommandInfo" class="command-info">
        <p class="docstring">{{ selectedCommandInfo.doc }}</p>
        <div v-if="filteredParameters.length > 0" class="params-hint">
          <strong>Parameters:</strong>
          <ul>
            <li v-for="param in filteredParameters" :key="param.name">
              <code>{{ param.name }}</code> ({{ param.type }}) -
              <span v-if="param.default !== 'required'">Default: <code>{{ param.default }}</code></span>
              <span v-else class="required">Required</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="form-group">
        <label for="params">Parameters (JSON)</label>
        <textarea id="params" v-model="params" rows="10"></textarea>
      </div>
      <button @click="execute" :disabled="isLoading || !command" class="btn-primary">Execute Command</button>
      <div v-if="message" :class="['message', messageType]">{{ message }}</div>
      <div v-if="response" class="response-box">
        <strong>Response:</strong>
        <pre>{{ response }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, defineExpose, onMounted, onUnmounted, nextTick } from 'vue';
import axios from 'axios';

const command = ref('');
const params = ref('{}');
const isLoading = ref(false);
const message = ref('');
const messageType = ref('success');
const response = ref(null);

const commands = ref([]);
const isCommandsLoading = ref(false);
const commandsError = ref('');

const isDropdownOpen = ref(false);
const searchQuery = ref('');
const searchInput = ref(null);

const selectedCommandInfo = computed(() => {
  return commands.value.find(c => c.name === command.value) || null;
});

const filteredParameters = computed(() => {
  if (!selectedCommandInfo.value) return [];
  return selectedCommandInfo.value.parameters.filter(param => param.name !== '_ray_trace_ctx');
});

const filteredCommands = computed(() => {
  if (!searchQuery.value) return commands.value;
  const query = searchQuery.value.toLowerCase();
  return commands.value.filter(cmd => cmd.name.toLowerCase().includes(query));
});

const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value;
  if (isDropdownOpen.value) {
    nextTick(() => {
      searchInput.value?.focus();
    });
  } else {
    searchQuery.value = '';
  }
};

const selectCommand = (cmdName) => {
  command.value = cmdName;
  isDropdownOpen.value = false;
  searchQuery.value = '';
  onCommandChange();
};

const closeDropdown = (e) => {
  if (!e.target.closest('.custom-select')) {
    isDropdownOpen.value = false;
    searchQuery.value = '';
  }
};

onMounted(() => {
  document.addEventListener('click', closeDropdown);
});

onUnmounted(() => {
  document.removeEventListener('click', closeDropdown);
});

const loadCommands = async () => {
  if (commands.value.length > 0 || isCommandsLoading.value) {
    return;
  }
  isCommandsLoading.value = true;
  commandsError.value = '';
  try {
    const res = await axios.get('http://localhost:8001/api/simulation/commands');
    commands.value = res.data;
  } catch (err) {
    commandsError.value = `Failed to load commands: ${err.response?.data?.detail || err.message}`;
  } finally {
    isCommandsLoading.value = false;
  }
};

defineExpose({
  loadCommands
});

const onCommandChange = () => {
  if (!selectedCommandInfo.value) {
    params.value = '{}';
    return;
  }

  const template = {};
  selectedCommandInfo.value.parameters.forEach(param => {
    if (param.name === '_ray_trace_ctx') {
        return;
    }
    if (command.value === 'deliver_message' && param.name === 'message') {
        template[param.name] = {
            from_id: "God",
            to_id: "<AgentName>",
            kind: "from_user_to_agent",
            content: "Your message here"
        };
    } else {
        template[param.name] = param.default !== 'required'
            ? param.default
            : `<${param.type}>`;
    }
  });

  params.value = JSON.stringify(template, null, 2);
};

const execute = async () => {
  isLoading.value = true;
  message.value = '';
  response.value = null;
  let parsedParams;

  try {
    parsedParams = JSON.parse(params.value);
  } catch (e) {
    message.value = 'Invalid JSON in parameters.';
    messageType.value = 'error';
    isLoading.value = false;
    return;
  }

  try {
    const res = await axios.post('http://localhost:8001/api/simulation/command', {
      command: command.value,
      params: parsedParams,
    });
    message.value = 'Command executed successfully.';
    messageType.value = 'success';
    response.value = JSON.stringify(res.data.result, null, 2);
  } catch (err) {
    message.value = `Execution failed: ${err.response?.data?.detail || err.message}`;
    messageType.value = 'error';
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.panel-container h3 {
  margin-top: 0;
}

.loading-small {
  color: var(--text-muted);
  font-style: italic;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--accent);
}

.custom-select {
  position: relative;
  width: 100%;
}

.custom-select__trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border: 1px solid var(--border-soft);
  border-radius: 12px;
  background-color: var(--bg-inset-soft);
  color: var(--text-primary);
  font-size: 1rem;
  cursor: pointer;
  transition: all 200ms ease;
}

.custom-select__trigger:hover {
  border-color: color-mix(in srgb, var(--accent) 50%, var(--border-soft) 50%);
}

.custom-select.is-open .custom-select__trigger {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--input-focus-shadow);
  border-radius: 12px 12px 0 0;
}

.custom-select__value {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.custom-select__arrow {
  width: 18px;
  height: 18px;
  color: var(--accent);
  transition: transform 200ms ease;
  flex-shrink: 0;
  margin-left: 8px;
}

.custom-select.is-open .custom-select__arrow {
  transform: rotate(180deg);
}

.custom-select__options {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 100;
  background: var(--card-bg);
  border: 1px solid var(--accent);
  border-top: none;
  border-radius: 0 0 12px 12px;
  box-shadow: 0 12px 30px var(--accent-shadow);
  overflow: hidden;
}

.custom-select__search {
  padding: 10px;
  border-bottom: 1px solid var(--border-soft);
}

.custom-select__search input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  background: var(--bg-inset-soft);
  color: var(--text-primary);
  font-size: 0.95rem;
  outline: none;
  transition: all 200ms ease;
}

.custom-select__search input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px var(--input-focus-shadow);
}

.custom-select__search input::placeholder {
  color: var(--text-muted);
}

.custom-select__options-list {
  max-height: 280px;
  overflow-y: auto;
}

.custom-select__option {
  padding: 12px 14px;
  cursor: pointer;
  font-size: 0.95rem;
  color: var(--text-primary);
  transition: all 150ms ease;
  border-left: 3px solid transparent;
}

.custom-select__option:hover {
  background: var(--nav-link-hover-bg);
  border-left-color: var(--accent);
}

.custom-select__option.is-selected {
  background: var(--nav-link-hover-bg);
  color: var(--accent);
  font-weight: 600;
  border-left-color: var(--accent);
}

.custom-select__empty {
  padding: 16px;
  text-align: center;
  color: var(--text-muted);
  font-style: italic;
}

.custom-select__options-list::-webkit-scrollbar {
  width: 6px;
}

.custom-select__options-list::-webkit-scrollbar-track {
  background: transparent;
}

.custom-select__options-list::-webkit-scrollbar-thumb {
  background: var(--accent-soft);
  border-radius: 3px;
}

.custom-select__options-list::-webkit-scrollbar-thumb:hover {
  background: var(--accent);
}

textarea {
  width: 100%;
  padding: 16px 18px;
  box-sizing: border-box;
  border: 2px solid var(--accent-soft);
  border-radius: 12px;
  background-color: var(--card-bg);
  color: var(--accent);
  font-size: 1.1rem;
  font-weight: 600;
  line-height: 1.6;
  transition: all 200ms ease;
  resize: vertical;
  min-height: 160px;
  font-family: var(--font-family-mono);
}

textarea:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 4px var(--input-focus-shadow);
}

textarea:hover:not(:focus) {
  border-color: var(--accent);
}

[data-theme="dark"] textarea {
  color: #facc15;
  background-color: rgba(0, 0, 0, 0.3);
}

.command-info {
  background-color: var(--bg-inset-soft);
  border: 1px solid var(--border-soft);
  border-radius: 12px;
  padding: 18px;
  margin-bottom: 20px;
}

.docstring {
  font-style: italic;
  color: var(--text-secondary);
  margin: 0 0 16px 0;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-soft);
  line-height: 1.6;
}

.params-hint ul {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 0.95rem;
}

.params-hint li {
  margin-bottom: 10px;
  color: var(--text-secondary);
  padding: 8px 12px;
  background: var(--bg-inset-softest);
  border-radius: 8px;
}

.params-hint code {
  background: var(--nav-link-hover-bg);
  padding: 2px 8px;
  border-radius: 4px;
  color: var(--accent);
  font-weight: 600;
  border: none;
}

.params-hint .required {
  color: var(--accent-strong);
  font-weight: bold;
}

[data-theme="dark"] .params-hint .required {
  color: #facc15;
}

.response-box {
  margin-top: 20px;
  padding: 18px;
  background-color: var(--bg-inset-soft);
  border-radius: 12px;
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid var(--border-soft);
}

pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 0.95rem;
  color: var(--text-secondary);
}

.btn-primary {
  padding: 12px 28px;
  border: 1px solid transparent;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  font-size: 1rem;
  transition: all 200ms ease;
  background-color: var(--accent);
  color: #FDF8E8;
}

[data-theme="dark"] .btn-primary {
  background-color: var(--accent);
  color: #0a0f1e;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px var(--accent-shadow);
  opacity: 0.95;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.message {
  margin-top: 15px;
  padding: 12px 16px;
  border-radius: 10px;
  border-left: 4px solid;
  font-size: 0.95rem;
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
</style>
