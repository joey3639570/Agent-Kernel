<!-- Side panel for editing node/edge properties. -->
<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  node: Object,
  edge: Object,
})

const emit = defineEmits(['update:node', 'update:edge', 'close'])

// Local state for editing
const localData = ref({})

// Initialize local data when selection changes
watch(
  () => props.node || props.edge,
  (value) => {
    if (value?.data) {
      localData.value = JSON.parse(JSON.stringify(value.data))
    }
  },
  { immediate: true, deep: true }
)

// Update handlers
function updateNodeProperty(key, value) {
  localData.value[key] = value
  emit('update:node', { [key]: value })
}

function updatePersonality(trait, value) {
  if (!localData.value.personality) {
    localData.value.personality = {}
  }
  localData.value.personality[trait] = value
  emit('update:node', { personality: { ...localData.value.personality } })
}

function updateEdgeProperty(key, value) {
  localData.value[key] = value
  emit('update:edge', { [key]: value })
}

const roleOptions = [
  { value: 'assistant', label: 'Assistant' },
  { value: 'researcher', label: 'Researcher' },
  { value: 'critic', label: 'Critic' },
  { value: 'moderator', label: 'Moderator' },
]

const relationOptions = [
  { value: 'friend', label: 'Friend' },
  { value: 'enemy', label: 'Enemy' },
  { value: 'neutral', label: 'Neutral' },
  { value: 'colleague', label: 'Colleague' },
  { value: 'ally', label: 'Ally' },
  { value: 'rival', label: 'Rival' },
  { value: 'mentor', label: 'Mentor' },
]

const personalityTraits = [
  { key: 'openness', label: 'Openness', description: 'Creativity and curiosity' },
  { key: 'conscientiousness', label: 'Conscientiousness', description: 'Organization and diligence' },
  { key: 'extraversion', label: 'Extraversion', description: 'Social energy and assertiveness' },
  { key: 'agreeableness', label: 'Agreeableness', description: 'Cooperation and trust' },
  { key: 'neuroticism', label: 'Neuroticism', description: 'Emotional sensitivity' },
]
</script>

<template>
  <div class="property-panel">
    <div class="panel-header">
      <h3 v-if="node">Agent Properties</h3>
      <h3 v-else-if="edge">Relationship Properties</h3>
      <button class="close-btn" @click="emit('close')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>

    <div class="panel-body">
      <!-- Agent Properties -->
      <template v-if="node">
        <div class="form-group">
          <label>Name</label>
          <input
            type="text"
            :value="localData.name"
            @input="updateNodeProperty('name', $event.target.value)"
            placeholder="Agent name"
          />
        </div>

        <div class="form-group">
          <label>Role</label>
          <select
            :value="localData.role"
            @change="updateNodeProperty('role', $event.target.value)"
          >
            <option v-for="opt in roleOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>Model</label>
          <input
            type="text"
            :value="localData.model"
            @input="updateNodeProperty('model', $event.target.value)"
            placeholder="default"
          />
        </div>

        <div class="form-divider"></div>

        <h4>Personality (Big Five)</h4>
        <div class="personality-sliders">
          <div
            v-for="trait in personalityTraits"
            :key="trait.key"
            class="slider-group"
          >
            <div class="slider-header">
              <label>{{ trait.label }}</label>
              <span class="slider-value">
                {{ ((localData.personality?.[trait.key] || 0.5) * 100).toFixed(0) }}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              :value="localData.personality?.[trait.key] || 0.5"
              @input="updatePersonality(trait.key, parseFloat($event.target.value))"
            />
            <span class="slider-desc">{{ trait.description }}</span>
          </div>
        </div>

        <div class="form-divider"></div>

        <h4>Features</h4>
        <div class="checkbox-group">
          <label class="checkbox-label">
            <input
              type="checkbox"
              :checked="localData.memory_enabled"
              @change="updateNodeProperty('memory_enabled', $event.target.checked)"
            />
            <span>Enable Memory (RAG + Social Graph)</span>
          </label>
          <label class="checkbox-label">
            <input
              type="checkbox"
              :checked="localData.tools_enabled"
              @change="updateNodeProperty('tools_enabled', $event.target.checked)"
            />
            <span>Enable Tools (Function Calling)</span>
          </label>
        </div>
      </template>

      <!-- Edge Properties -->
      <template v-else-if="edge">
        <div class="form-group">
          <label>Relationship Type</label>
          <select
            :value="localData.relation_type"
            @change="updateEdgeProperty('relation_type', $event.target.value)"
          >
            <option v-for="opt in relationOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>

        <div class="slider-group">
          <div class="slider-header">
            <label>Weight</label>
            <span class="slider-value">{{ (localData.weight || 0).toFixed(2) }}</span>
          </div>
          <input
            type="range"
            min="-1"
            max="1"
            step="0.1"
            :value="localData.weight || 0"
            @input="updateEdgeProperty('weight', parseFloat($event.target.value))"
          />
          <div class="weight-labels">
            <span>Hostile</span>
            <span>Neutral</span>
            <span>Friendly</span>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.property-panel {
  width: 320px;
  background: var(--card-bg, #ffffff);
  border-left: 1px solid var(--border-soft, #e5e7eb);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid var(--border-soft, #e5e7eb);
  background: var(--surface, #f9fafb);
}

.panel-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary, #111827);
}

.close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-muted, #9ca3af);
  transition: all 200ms ease;
}

.close-btn:hover {
  background: var(--bg-inset-light, #f3f4f6);
  color: var(--text-primary, #111827);
}

.close-btn svg {
  width: 18px;
  height: 18px;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary, #374151);
  margin-bottom: 0.5rem;
}

.form-group input[type='text'],
.form-group select {
  width: 100%;
  padding: 0.625rem 0.875rem;
  border: 1px solid var(--border-soft, #e5e7eb);
  border-radius: 8px;
  background: var(--bg-inset-light, #ffffff);
  color: var(--text-primary, #111827);
  font-size: 0.875rem;
  transition: all 200ms ease;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--accent, #6366f1);
  box-shadow: 0 0 0 3px var(--accent-soft, rgba(99, 102, 241, 0.1));
}

.form-divider {
  height: 1px;
  background: var(--border-soft, #e5e7eb);
  margin: 1.5rem 0;
}

h4 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary, #111827);
  margin: 0 0 1rem;
}

.personality-sliders {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.slider-group {
  margin-bottom: 0.5rem;
}

.slider-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
}

.slider-header label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-secondary, #374151);
}

.slider-value {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--accent, #6366f1);
}

.slider-group input[type='range'] {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: var(--bg-inset-light, #e5e7eb);
  appearance: none;
  cursor: pointer;
}

.slider-group input[type='range']::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--accent, #6366f1);
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  cursor: pointer;
}

.slider-desc {
  display: block;
  font-size: 0.75rem;
  color: var(--text-muted, #9ca3af);
  margin-top: 0.25rem;
}

.weight-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--text-muted, #9ca3af);
  margin-top: 0.25rem;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  cursor: pointer;
}

.checkbox-label input[type='checkbox'] {
  width: 18px;
  height: 18px;
  accent-color: var(--accent, #6366f1);
  cursor: pointer;
}

.checkbox-label span {
  font-size: 0.875rem;
  color: var(--text-secondary, #374151);
}
</style>

