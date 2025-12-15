<!-- Node-based editor for designing Agent societies using Vue Flow. -->
<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import { useNodeEditorStore } from '../stores/node_editor'
import AgentNode from '../components/node_editor/AgentNode.vue'
import PropertyPanel from '../components/node_editor/PropertyPanel.vue'

const store = useNodeEditorStore()
const { onConnect, addEdges, onNodesChange, onEdgesChange, applyNodeChanges, applyEdgeChanges } = useVueFlow()

// Custom node types
const nodeTypes = {
  agent: AgentNode,
}

// Handle connections
onConnect((params) => {
  store.addRelationEdge(params.source, params.target)
})

// Sync changes back to store
onNodesChange((changes) => {
  store.nodes = applyNodeChanges(changes, store.nodes)
})

onEdgesChange((changes) => {
  store.edges = applyEdgeChanges(changes, store.edges)
})

// Handle node selection
function onNodeClick(event) {
  store.selectNode(event.node.id)
}

function onEdgeClick(event) {
  store.selectEdge(event.edge.id)
}

function onPaneClick() {
  store.clearSelection()
}

// Toolbar actions
function addAgent() {
  const node = store.addAgentNode({
    x: 200 + Math.random() * 200,
    y: 150 + Math.random() * 150,
  })
}

function deleteSelected() {
  if (store.selectedNode) {
    store.removeNode(store.selectedNode.id)
  } else if (store.selectedEdge) {
    store.removeEdge(store.selectedEdge.id)
  }
}

function clearCanvas() {
  if (confirm('Are you sure you want to clear all nodes and edges?')) {
    store.clearAll()
  }
}

async function exportConfig() {
  const config = store.configJson
  const json = JSON.stringify(config, null, 2)

  // Create download
  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'society_config.json'
  a.click()
  URL.revokeObjectURL(url)

  store.markClean()
}

async function saveToBackend() {
  try {
    const config = store.configJson
    const response = await fetch('/api/configs/society', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    })
    if (response.ok) {
      alert('Configuration saved successfully!')
      store.markClean()
    } else {
      alert('Failed to save configuration')
    }
  } catch (error) {
    alert('Error saving configuration: ' + error.message)
  }
}

function importConfig(event) {
  const file = event.target.files[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const config = JSON.parse(e.target.result)
      store.loadFromConfig(config)
    } catch (err) {
      alert('Invalid configuration file')
    }
  }
  reader.readAsText(file)
  event.target.value = '' // Reset input
}

// Add some demo nodes on mount if empty
onMounted(() => {
  if (store.nodes.length === 0) {
    // Add demo agents
    store.addAgentNode({ x: 150, y: 100 })
    store.addAgentNode({ x: 450, y: 100 })
    store.addAgentNode({ x: 300, y: 300 })

    // Add demo relationships
    const agents = store.agentNodes
    if (agents.length >= 3) {
      store.addRelationEdge(agents[0].id, agents[1].id, {
        relation_type: 'friend',
        weight: 0.7,
      })
      store.addRelationEdge(agents[1].id, agents[2].id, {
        relation_type: 'colleague',
        weight: 0.5,
      })
    }
  }
})
</script>

<template>
  <div class="node-editor-container">
    <div class="editor-toolbar">
      <div class="toolbar-left">
        <button class="toolbar-btn primary" @click="addAgent">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="8" r="4" />
            <path d="M20 21a8 8 0 1 0-16 0" />
          </svg>
          Add Agent
        </button>
        <button
          class="toolbar-btn danger"
          @click="deleteSelected"
          :disabled="!store.selectedNode && !store.selectedEdge"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          </svg>
          Delete
        </button>
        <button class="toolbar-btn" @click="clearCanvas">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <line x1="9" y1="9" x2="15" y2="15" />
            <line x1="15" y1="9" x2="9" y2="15" />
          </svg>
          Clear All
        </button>
      </div>
      <div class="toolbar-center">
        <span v-if="store.isDirty" class="unsaved-indicator">Unsaved changes</span>
      </div>
      <div class="toolbar-right">
        <label class="toolbar-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          Import
          <input type="file" accept=".json,.yaml,.yml" @change="importConfig" hidden />
        </label>
        <button class="toolbar-btn" @click="exportConfig">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          Export JSON
        </button>
        <button class="toolbar-btn primary" @click="saveToBackend">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
            <polyline points="17 21 17 13 7 13 7 21" />
            <polyline points="7 3 7 8 15 8" />
          </svg>
          Save
        </button>
      </div>
    </div>

    <div class="editor-main">
      <div class="flow-container">
        <VueFlow
          :nodes="store.nodes"
          :edges="store.edges"
          :node-types="nodeTypes"
          @node-click="onNodeClick"
          @edge-click="onEdgeClick"
          @pane-click="onPaneClick"
          fit-view-on-init
          :default-viewport="{ zoom: 1 }"
          :min-zoom="0.2"
          :max-zoom="2"
        >
          <Background pattern-color="var(--accent)" :gap="20" />
          <Controls />
          <MiniMap />
        </VueFlow>
      </div>

      <PropertyPanel
        v-if="store.selectedNode || store.selectedEdge"
        :node="store.selectedNode"
        :edge="store.selectedEdge"
        @update:node="(data) => store.updateNodeData(store.selectedNode.id, data)"
        @update:edge="(data) => store.updateEdgeData(store.selectedEdge.id, data)"
        @close="store.clearSelection"
      />
    </div>
  </div>
</template>

<style>
@import '@vue-flow/core/dist/style.css';
@import '@vue-flow/core/dist/theme-default.css';
@import '@vue-flow/controls/dist/style.css';
@import '@vue-flow/minimap/dist/style.css';

.node-editor-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 200px);
  min-height: 500px;
  background: var(--card-bg);
  border-radius: var(--border-radius-lg);
  border: 1px solid var(--border-soft);
  overflow: hidden;
}

.editor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: var(--surface);
  border-bottom: 1px solid var(--border-soft);
  gap: 1rem;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.toolbar-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.unsaved-indicator {
  color: var(--warning, #f59e0b);
  font-size: 0.875rem;
  font-weight: 500;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid var(--border-soft);
  border-radius: var(--border-radius-md);
  background: var(--bg-inset-light);
  color: var(--text-primary);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 200ms ease;
}

.toolbar-btn:hover:not(:disabled) {
  background: var(--accent-soft);
  border-color: var(--accent);
}

.toolbar-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.toolbar-btn.primary {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}

.toolbar-btn.primary:hover:not(:disabled) {
  background: var(--accent-strong);
}

.toolbar-btn.danger:hover:not(:disabled) {
  background: #fee2e2;
  border-color: #ef4444;
  color: #dc2626;
}

[data-theme='dark'] .toolbar-btn.danger:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.2);
}

.toolbar-btn svg {
  width: 18px;
  height: 18px;
}

.editor-main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.flow-container {
  flex: 1;
  position: relative;
}

/* Vue Flow customizations */
.vue-flow {
  background: var(--bg-inset-lightest);
}

.vue-flow__edge-path {
  stroke: var(--accent);
  stroke-width: 2;
}

.vue-flow__edge.selected .vue-flow__edge-path {
  stroke: var(--accent-strong);
  stroke-width: 3;
}

.vue-flow__controls {
  box-shadow: var(--shadow-md);
}

.vue-flow__controls-button {
  background: var(--card-bg);
  border-color: var(--border-soft);
  fill: var(--text-primary);
}

.vue-flow__controls-button:hover {
  background: var(--accent-soft);
}

.vue-flow__minimap {
  background: var(--card-bg);
  border: 1px solid var(--border-soft);
  border-radius: var(--border-radius-md);
}
</style>

