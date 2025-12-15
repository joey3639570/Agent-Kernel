<!-- Custom Vue Flow node for representing an Agent. -->
<script setup>
import { computed } from 'vue'
import { Handle, Position } from '@vue-flow/core'

const props = defineProps({
  id: String,
  data: Object,
  selected: Boolean,
})

const roleColors = {
  assistant: '#10b981',
  researcher: '#3b82f6',
  critic: '#f59e0b',
  moderator: '#8b5cf6',
  default: '#6b7280',
}

const roleColor = computed(() => {
  return roleColors[props.data?.role] || roleColors.default
})

const personalityBars = computed(() => {
  const p = props.data?.personality || {}
  return [
    { label: 'O', value: p.openness || 0.5 },
    { label: 'C', value: p.conscientiousness || 0.5 },
    { label: 'E', value: p.extraversion || 0.5 },
    { label: 'A', value: p.agreeableness || 0.5 },
    { label: 'N', value: p.neuroticism || 0.5 },
  ]
})
</script>

<template>
  <div class="agent-node" :class="{ selected }">
    <Handle type="target" :position="Position.Left" />
    
    <div class="agent-header" :style="{ borderColor: roleColor }">
      <div class="agent-avatar" :style="{ background: roleColor }">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="8" r="4" />
          <path d="M20 21a8 8 0 1 0-16 0" />
        </svg>
      </div>
      <div class="agent-info">
        <span class="agent-name">{{ data?.name || 'Unnamed Agent' }}</span>
        <span class="agent-role" :style="{ color: roleColor }">{{ data?.role || 'unknown' }}</span>
      </div>
    </div>

    <div class="agent-body">
      <div class="personality-bars">
        <div
          v-for="bar in personalityBars"
          :key="bar.label"
          class="bar-item"
          :title="`${bar.label}: ${(bar.value * 100).toFixed(0)}%`"
        >
          <span class="bar-label">{{ bar.label }}</span>
          <div class="bar-track">
            <div class="bar-fill" :style="{ width: `${bar.value * 100}%` }"></div>
          </div>
        </div>
      </div>

      <div class="agent-features">
        <span class="feature-badge" :class="{ active: data?.memory_enabled }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2a10 10 0 1 0 10 10 4 4 0 0 1-5-5 4 4 0 0 1-5-5" />
          </svg>
          Memory
        </span>
        <span class="feature-badge" :class="{ active: data?.tools_enabled }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="m3 17 2 2 4-4" />
            <path d="m3 7 2 2 4-4" />
            <path d="M13 6h8" />
            <path d="M13 12h8" />
            <path d="M13 18h8" />
          </svg>
          Tools
        </span>
      </div>
    </div>

    <Handle type="source" :position="Position.Right" />
  </div>
</template>

<style scoped>
.agent-node {
  min-width: 200px;
  background: var(--card-bg, #ffffff);
  border: 2px solid var(--border-soft, #e5e7eb);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 200ms ease;
  overflow: hidden;
}

.agent-node:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.agent-node.selected {
  border-color: var(--accent, #6366f1);
  box-shadow: 0 0 0 3px var(--accent-soft, rgba(99, 102, 241, 0.2));
}

.agent-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-bottom: 2px solid;
  background: var(--surface, #f9fafb);
}

.agent-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.agent-avatar svg {
  width: 24px;
  height: 24px;
  stroke: white;
}

.agent-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.agent-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary, #111827);
}

.agent-role {
  font-size: 12px;
  font-weight: 500;
  text-transform: capitalize;
}

.agent-body {
  padding: 12px;
}

.personality-bars {
  display: flex;
  gap: 6px;
  margin-bottom: 12px;
}

.bar-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.bar-label {
  font-size: 10px;
  font-weight: 600;
  color: var(--text-muted, #9ca3af);
}

.bar-track {
  width: 100%;
  height: 24px;
  background: var(--bg-inset-light, #f3f4f6);
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.bar-fill {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--accent, #6366f1);
  transition: height 200ms ease;
  border-radius: 4px;
  height: 100%;
}

.agent-features {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.feature-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 500;
  background: var(--bg-inset-light, #f3f4f6);
  color: var(--text-muted, #9ca3af);
  border: 1px solid transparent;
}

.feature-badge svg {
  width: 12px;
  height: 12px;
}

.feature-badge.active {
  background: var(--accent-soft, rgba(99, 102, 241, 0.1));
  color: var(--accent, #6366f1);
  border-color: var(--accent, #6366f1);
}

/* Handle styles */
:deep(.vue-flow__handle) {
  width: 12px;
  height: 12px;
  background: var(--accent, #6366f1);
  border: 2px solid white;
}

:deep(.vue-flow__handle:hover) {
  background: var(--accent-strong, #4f46e5);
}
</style>

